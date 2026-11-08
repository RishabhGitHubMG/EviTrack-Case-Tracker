"""
Class-based Views for EviTrack Accounts & Authentication.
Production-grade implementation with role-based access control, django-axes lockout protection,
TOTP two-factor authentication, administrative approval workflow, and security audit logging.
"""
import json
import logging
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login as auth_login,
    logout as auth_logout,
    update_session_auth_hash,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import FormView, ListView, UpdateView

from axes.decorators import axes_dispatch
from axes.models import AccessAttempt, AccessFailureLog
from axes.utils import reset as axes_reset

from apps.accounts.models import EmailOTPChallenge
from apps.core.rate_limit import is_rate_limited
from apps.accounts.forms import (
    LoginForm,
    NotificationPreferencesForm,
    OTPSetupForm,
    OTPVerificationForm,
    PasswordChangeForm,
    ProfileForm,
    RegistrationForm,
    UserApprovalForm,
    UserRoleForm,
)
from apps.accounts.mixins import AdminRequiredMixin
from apps.accounts.services import (
    generate_otp_secret,
    generate_qr_code_b64,
    get_otp_uri,
    mask_email,
    send_approval_email,
    send_email_otp,
    send_rejection_email,
    verify_email_otp,
    verify_otp,
)

User = get_user_model()
logger = logging.getLogger(__name__)


# ==============================================================================
# AUTHENTICATION VIEWS
# ==============================================================================

class RegisterView(FormView):
    """
    User self-registration view.
    New accounts are registered with is_active=True and is_approved=False.
    """
    template_name = 'accounts/register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('accounts:login')

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: RegistrationForm) -> HttpResponse:
        user = form.save()
        logger.info("New user registered: %s (Role: %s, Approved: %s)", user.email, user.role, user.is_approved)
        messages.success(
            self.request,
            'Your registration has been submitted successfully. '
            'Your registration is pending admin approval. You will receive an email once approved.',
        )
        return super().form_valid(form)


@method_decorator(axes_dispatch, name='dispatch')
@method_decorator(sensitive_post_parameters('password'), name='dispatch')
class LoginView(FormView):
    """
    Custom login view integrating Django-Axes lockout protection, admin approval verification,
    and TOTP two-factor authentication redirection.
    """
    template_name = 'accounts/login.html'
    form_class = LoginForm

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        if request.method == 'POST' and is_rate_limited(
            request, 'login', settings.AUTH_LOGIN_RATE_LIMIT, settings.AUTH_LOGIN_RATE_WINDOW_SECONDS
        ):
            return HttpResponse('Too many login attempts. Try again later.', status=429)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url and next_url.startswith('/'):
            return next_url
        return settings.LOGIN_REDIRECT_URL

    def form_valid(self, form: LoginForm) -> HttpResponse:
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        remember_me = form.cleaned_data.get('remember_me', False)

        # Pre-check: If user exists, verify approval and active state
        existing_user = User.objects.filter(email__iexact=email).first()
        if existing_user and existing_user.check_password(password):
            if not existing_user.is_approved:
                logger.warning("Unapproved login attempt by %s", email)
                messages.warning(
                    self.request,
                    "Your account registration is currently pending administrative approval. "
                    "Please contact your EviTrack administrator.",
                )
                return self.form_invalid(form)

            if not existing_user.is_active:
                logger.warning("Inactive login attempt by %s", email)
                messages.error(
                    self.request,
                    "This account has been deactivated. Please contact your system administrator.",
                )
                return self.form_invalid(form)

        # Authenticate via Django authentication backends (including AxesStandaloneBackend)
        user = authenticate(self.request, username=email, password=password)

        if user is None:
            logger.warning("Failed login attempt for email: %s", email)
            form.add_error(None, "Invalid email address or password.")
            return self.form_invalid(form)

        otp_method = 'email'
        if not send_email_otp(user):
            form.add_error(None, 'Unable to send a sign-in code. Please try again later.')
            return self.form_invalid(form)

        self.request.session['pre_otp_user_id'] = user.pk
        self.request.session['pre_otp_backend'] = getattr(
            user, 'backend', settings.AUTHENTICATION_BACKENDS[0]
        )
        self.request.session['pre_otp_method'] = otp_method
        self.request.session['pre_otp_remember_me'] = remember_me
        self.request.session['pre_otp_next'] = self.get_success_url()
        logger.info('User %s credentials verified. Awaiting %s OTP.', user.email, otp_method)
        return redirect('accounts:otp_verify')


class OTPVerifyView(FormView):
    """
    Validates the 6-digit TOTP token during the two-factor authentication login sequence.
    """
    template_name = 'accounts/otp_verify.html'
    form_class = OTPVerificationForm

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        if request.method == 'POST' and is_rate_limited(
            request, 'otp-verify', settings.OTP_VERIFY_RATE_LIMIT, settings.OTP_VERIFY_RATE_WINDOW_SECONDS
        ):
            return HttpResponse('Too many verification attempts. Try again later.', status=429)

        pre_otp_user_id = request.session.get('pre_otp_user_id')
        if not pre_otp_user_id:
            messages.warning(request, "No pending two-factor authentication session found. Please sign in.")
            return redirect('accounts:login')

        self.pending_user = User.objects.filter(
            pk=pre_otp_user_id, is_active=True, is_approved=True
        ).first()

        if not self.pending_user:
            request.session.pop('pre_otp_user_id', None)
            messages.error(request, "Invalid authentication session. Please sign in again.")
            return redirect('accounts:login')

        self.otp_method = request.session.get('pre_otp_method', 'email')
        if self.otp_method == 'totp' and not self.pending_user.otp_enabled:
            self._clear_pending_session()
            messages.error(request, 'Your authenticator settings changed. Please sign in again.')
            return redirect('accounts:login')
        challenge = EmailOTPChallenge.objects.filter(user=self.pending_user).first()
        if not challenge or challenge.expires_at <= timezone.now():
            self._clear_pending_session()
            messages.warning(request, 'Your sign-in code expired. Please sign in again.')
            return redirect('accounts:login')
        if challenge.locked_until and challenge.locked_until > timezone.now():
            self._clear_pending_session()
            messages.error(request, 'Sign-in verification is temporarily locked. Try again later.')
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)

    def _clear_pending_session(self) -> None:
        for key in ('pre_otp_user_id', 'pre_otp_backend', 'pre_otp_method', 'pre_otp_remember_me', 'pre_otp_next'):
            self.request.session.pop(key, None)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['verification_instruction'] = (
            f'Enter the 6-digit code sent to {self._mask_email(self.pending_user.email)}.'
            if self.otp_method == 'email'
            else 'Enter the 6-digit code from your authenticator app.'
        )
        return context

    def _mask_email(self, email: str) -> str:
        return mask_email(email)

    def form_valid(self, form: OTPVerificationForm) -> HttpResponse:
        code = form.cleaned_data['otp_code']

        valid_code = (
            verify_email_otp(self.pending_user, code)
            if self.otp_method == 'email'
            else verify_otp(self.pending_user, code)
        )
        if valid_code and self.otp_method == 'email' and self.pending_user.otp_enabled:
            EmailOTPChallenge.objects.update_or_create(
                user=self.pending_user,
                defaults={
                    'code_hash': '',
                    'expires_at': timezone.now() + timedelta(minutes=settings.EMAIL_OTP_TTL_MINUTES),
                    'attempts': 0,
                    'locked_until': None,
                },
            )
            self.request.session['pre_otp_method'] = 'totp'
            return redirect('accounts:otp_verify')

        if valid_code:
            EmailOTPChallenge.objects.filter(user=self.pending_user).delete()
            user = self.pending_user
            remember_me = self.request.session.get('pre_otp_remember_me', False)
            next_url = self.request.session.get('pre_otp_next', settings.LOGIN_REDIRECT_URL)
            backend = self.request.session.get('pre_otp_backend')
            self._clear_pending_session()

            auth_login(self.request, user, backend=backend)

            if not remember_me:
                self.request.session.set_expiry(0)
            else:
                self.request.session.set_expiry(getattr(settings, 'SESSION_COOKIE_AGE', 900))

            try:
                axes_reset(username=user.email)
            except Exception:
                pass

            logger.info('User %s completed %s verification and signed in.', user.email, self.otp_method)
            messages.success(self.request, f"Identity verified. Welcome back, {user.first_name or user.email}!")
            return redirect(next_url)

        logger.warning('Invalid %s code entered for user %s', self.otp_method, self.pending_user.email)
        challenge = EmailOTPChallenge.objects.filter(user=self.pending_user).first()
        if challenge:
            if self.otp_method == 'totp':
                challenge.attempts += 1
                if challenge.attempts >= settings.EMAIL_OTP_MAX_ATTEMPTS:
                    challenge.locked_until = timezone.now() + timedelta(
                        minutes=settings.EMAIL_OTP_LOCKOUT_MINUTES
                    )
                challenge.save(update_fields=['attempts', 'locked_until', 'updated_at'])
            if challenge.locked_until and challenge.locked_until > timezone.now():
                self._clear_pending_session()
                messages.error(self.request, 'Too many invalid codes. Sign-in verification is locked temporarily.')
                return redirect('accounts:login')
        form.add_error('otp_code', 'Invalid or expired verification code. Please try again.')
        return self.form_invalid(form)


class LogoutView(View):
    """
    Terminates the user's active session and redirects to the sign-in page.
    """
    def get(self, request: HttpRequest) -> HttpResponse:
        return self._do_logout(request)

    def post(self, request: HttpRequest) -> HttpResponse:
        return self._do_logout(request)

    def _do_logout(self, request: HttpRequest) -> HttpResponse:
        is_timeout = request.GET.get('timeout') == '1'
        auth_logout(request)
        if is_timeout:
            messages.warning(request, "Your session has expired due to inactivity. Please sign in again.")
        else:
            messages.info(request, "You have been signed out successfully.")
        return redirect('accounts:login')


# ==============================================================================
# USER PROFILE & SELF-SERVICE VIEWS
# ==============================================================================

class NotificationPreferencesView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = NotificationPreferencesForm
    template_name = 'accounts/notification_preferences.html'
    success_url = reverse_lazy('accounts:preferences')

    def get_object(self, queryset=None) -> User:
        return self.request.user

    def form_valid(self, form: NotificationPreferencesForm) -> HttpResponse:
        response = super().form_valid(form)
        from apps.hearings.services import reschedule_user_reminders

        reschedule_user_reminders(self.request.user)
        messages.success(self.request, 'Notification preferences saved.')
        return response


class ProfileView(LoginRequiredMixin, UpdateView):
    """
    Allows the authenticated user to view and update their profile details and notification preferences.
    """
    model = User
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None) -> User:
        return self.request.user

    def form_valid(self, form: ProfileForm) -> HttpResponse:
        messages.success(self.request, "Your profile and preferences have been updated successfully.")
        return super().form_valid(form)


class PasswordChangeView(LoginRequiredMixin, FormView):
    """
    Enables authenticated users to securely update their account password.
    """
    template_name = 'accounts/password_change.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('accounts:profile')

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form: PasswordChangeForm) -> HttpResponse:
        form.save()
        # Maintain session without logging the user out after password change
        update_session_auth_hash(self.request, self.request.user)
        logger.info("Password changed for user %s", self.request.user.email)
        messages.success(self.request, "Your password has been changed successfully.")
        return super().form_valid(form)


class OTPSetupView(LoginRequiredMixin, View):
    """
    Configures TOTP Two-Factor Authentication for the authenticated user.
    Generates QR code and manual secret key, and validates a test token before enabling.
    """
    template_name = 'accounts/otp_setup.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        user = request.user

        # If user does not have an OTP secret yet, or if not enabled, create/retrieve secret
        if not user.otp_secret or not user.otp_enabled:
            temp_secret = request.session.get('temp_otp_secret')
            if not temp_secret:
                temp_secret = generate_otp_secret()
                request.session['temp_otp_secret'] = temp_secret
            active_secret = temp_secret
        else:
            active_secret = user.otp_secret

        uri = get_otp_uri(user, secret=active_secret)
        qr_code_b64 = generate_qr_code_b64(uri)

        # Format secret in groups of 4 for easy manual typing
        formatted_secret = ' '.join(active_secret[i:i + 4] for i in range(0, len(active_secret), 4))

        context = {
            'form': OTPSetupForm(initial={'action': 'disable' if user.otp_enabled else 'enable'}),
            'otp_enabled': user.otp_enabled,
            'qr_code_b64': qr_code_b64,
            'raw_secret': active_secret,
            'formatted_secret': formatted_secret,
            'provisioning_uri': uri,
        }
        return render(request, self.template_name, context)

    def post(self, request: HttpRequest) -> HttpResponse:
        form = OTPSetupForm(request.POST)
        user = request.user

        if not form.is_valid():
            messages.error(request, "Please correct the errors below.")
            return self.get(request)

        action = form.cleaned_data['action']
        otp_code = form.cleaned_data.get('otp_code', '').strip()

        if action == 'disable':
            user.otp_enabled = False
            user.otp_secret = ''
            user.save(update_fields=['otp_enabled', 'otp_secret'])
            request.session.pop('temp_otp_secret', None)
            logger.info("User %s disabled two-factor authentication.", user.email)
            messages.success(request, "Two-factor authentication has been disabled for your account.")
            return redirect('accounts:otp_setup')

        if action == 'enable':
            temp_secret = request.session.get('temp_otp_secret') or user.otp_secret
            if not temp_secret:
                messages.error(request, "Session setup expired. Please refresh and try again.")
                return redirect('accounts:otp_setup')

            if verify_otp(user, otp_code, secret=temp_secret):
                user.otp_secret = temp_secret
                user.otp_enabled = True
                user.save(update_fields=['otp_secret', 'otp_enabled'])
                request.session.pop('temp_otp_secret', None)
                logger.info("User %s successfully verified and enabled two-factor authentication.", user.email)
                messages.success(request, "Two-factor authentication has been successfully activated!")
                return redirect('accounts:otp_setup')
            else:
                messages.error(request, "Invalid verification code. Please check your authenticator application and try again.")
                return self.get(request)

        return redirect('accounts:otp_setup')


class DarkModeToggleView(LoginRequiredMixin, View):
    """
    AJAX endpoint to toggle or persist the dark_mode preference on the authenticated user model.
    """
    def post(self, request: HttpRequest) -> JsonResponse:
        user = request.user
        try:
            if request.body:
                data = json.loads(request.body.decode('utf-8'))
                if 'theme' in data:
                    user.dark_mode = (data['theme'] == 'dark')
                elif 'dark_mode' in data:
                    user.dark_mode = bool(data['dark_mode'])
                else:
                    user.dark_mode = not user.dark_mode
            else:
                user.dark_mode = not user.dark_mode
        except Exception:
            user.dark_mode = not user.dark_mode

        user.save(update_fields=['dark_mode'])
        theme = 'dark' if user.dark_mode else 'light'
        return JsonResponse({
            'status': 'ok',
            'dark_mode': user.dark_mode,
            'theme': theme,
        })

    def get(self, request: HttpRequest) -> JsonResponse:
        return JsonResponse({
            'dark_mode': request.user.dark_mode,
            'theme': 'dark' if request.user.dark_mode else 'light',
        })


# ==============================================================================
# ADMINISTRATIVE USER MANAGEMENT VIEWS
# ==============================================================================

class SecurityPolicyView(AdminRequiredMixin, View):
    template_name = 'accounts/security.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name, {
            'session_timeout_minutes': settings.SESSION_TIMEOUT_SECONDS // 60,
            'session_warning_minutes': (settings.SESSION_TIMEOUT_SECONDS - settings.SESSION_WARNING_SECONDS) // 60,
            'lockout_failure_limit': settings.AXES_FAILURE_LIMIT,
            'lockout_cooloff_minutes': int(settings.AXES_COOLOFF_TIME.total_seconds() // 60),
            'email_otp_ttl_minutes': settings.EMAIL_OTP_TTL_MINUTES,
            'email_otp_max_attempts': settings.EMAIL_OTP_MAX_ATTEMPTS,
            'email_otp_lockout_minutes': settings.EMAIL_OTP_LOCKOUT_MINUTES,
            'password_min_length': next(
                validator['OPTIONS']['min_length']
                for validator in settings.AUTH_PASSWORD_VALIDATORS
                if validator['NAME'].endswith('MinimumLengthValidator')
            ),
            'upload_limit_mb': settings.EVIDENCE_MAX_SIZE // (1024 * 1024),
            'login_rate_limit': settings.AUTH_LOGIN_RATE_LIMIT,
            'login_rate_window_seconds': settings.AUTH_LOGIN_RATE_WINDOW_SECONDS,
        })


class UserListView(AdminRequiredMixin, ListView):
    """
    Administrative directory of all registered system users with full-text search,
    role-based filtering, approval state filtering, and pagination.
    """
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 15

    def get_queryset(self):
        qs = User.objects.all().order_by('-date_joined')

        # Full-text search
        query = self.request.GET.get('q', '').strip()
        if query:
            qs = qs.filter(
                Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(phone__icontains=query)
            )

        # Role filter
        role = self.request.GET.get('role', '').strip()
        if role and role in User.Role.values:
            qs = qs.filter(role=role)

        # Status filter
        status = self.request.GET.get('status', '').strip()
        if status == 'pending':
            qs = qs.filter(is_approved=False, is_active=True)
        elif status == 'approved':
            qs = qs.filter(is_approved=True, is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)

        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['roles'] = User.Role.choices
        context['status_choices'] = [('pending', 'Pending'), ('approved', 'Approved'), ('inactive', 'Deactivated')]
        context['current_q'] = self.request.GET.get('q', '')
        context['current_role'] = self.request.GET.get('role', '')
        context['current_status'] = self.request.GET.get('status', '')

        # Summary statistics
        context['total_users_count'] = User.objects.count()
        context['pending_users_count'] = User.objects.filter(is_approved=False, is_active=True).count()
        context['active_users_count'] = User.objects.filter(is_approved=True, is_active=True).count()
        context['inactive_users_count'] = User.objects.filter(is_active=False).count()
        return context


class UserApprovalView(AdminRequiredMixin, ListView):
    """
    Displays pending user registrations awaiting administrative authorization.
    """
    model = User
    template_name = 'accounts/user_approval.html'
    context_object_name = 'pending_users'

    def get_queryset(self):
        return User.objects.filter(is_approved=False, is_active=True).order_by('-date_joined')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['pending_count'] = self.get_queryset().count()
        return context


class ApproveUserView(AdminRequiredMixin, View):
    """
    POST endpoint for approving a pending user account.
    Marks is_approved=True and sends an email notification.
    """
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        user = get_object_or_404(User, pk=pk)

        if user.is_approved and user.is_active:
            messages.info(request, f"User {user.email} is already approved.")
            return redirect('accounts:user_approval')

        user.is_approved = True
        user.is_active = True
        user.save(update_fields=['is_approved', 'is_active'])

        logger.info("User %s approved by Admin %s", user.email, request.user.email)
        send_approval_email(user)

        messages.success(request, f"Account for {user.get_full_name() or user.email} has been approved and activated.")
        next_url = request.POST.get('next', '')
        if url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return redirect(next_url)
        return redirect('accounts:user_approval')


class RejectUserView(AdminRequiredMixin, View):
    """
    POST endpoint for rejecting or deactivating a user account.
    Sets is_approved=False and is_active=False, and notifies the applicant.
    """
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        user = get_object_or_404(User, pk=pk)

        # Protect against self-deactivation
        if user == request.user:
            messages.error(request, "You cannot reject or deactivate your own administrator account.")
            return redirect('accounts:user_list')

        # Protect superuser accounts
        if user.is_superuser and not request.user.is_superuser:
            raise PermissionDenied("Only superusers may deactivate other superuser accounts.")

        reason = request.POST.get('reason', '').strip()
        user.is_approved = False
        user.is_active = False
        user.save(update_fields=['is_approved', 'is_active'])

        logger.info("User %s rejected/deactivated by Admin %s. Reason: %s", user.email, request.user.email, reason)
        send_rejection_email(user, reason=reason)

        messages.warning(request, f"Account for {user.get_full_name() or user.email} has been rejected / deactivated.")
        next_url = request.POST.get('next', '')
        if url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return redirect(next_url)
        return redirect('accounts:user_approval')


class UserRoleChangeView(AdminRequiredMixin, View):
    """
    Changes a user's assigned role and adjusts administrative privileges accordingly.
    """
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        user = get_object_or_404(User, pk=pk)
        form = UserRoleForm(request.POST, instance=user)

        if form.is_valid():
            new_role = form.cleaned_data['role']

            # Prevent an admin from accidentally revoking their own admin role
            if user == request.user and new_role != User.Role.ADMIN:
                messages.error(request, "You cannot demote your own administrator role.")
                return redirect('accounts:user_list')

            user.role = new_role
            if new_role == User.Role.ADMIN:
                user.is_staff = True
            user.save(update_fields=['role', 'is_staff'])

            logger.info("Admin %s updated role of %s to %s", request.user.email, user.email, new_role)
            messages.success(request, f"Role for {user.email} updated to {user.get_role_display()}.")
        else:
            messages.error(request, "Invalid role specified.")

        return redirect('accounts:user_list')


class FailedLoginListView(AdminRequiredMixin, ListView):
    """
    Audit view showing failed login attempts and active account lockouts captured by Django-Axes.
    """
    model = AccessFailureLog
    template_name = 'accounts/failed_logins.html'
    context_object_name = 'failed_logins'
    paginate_by = 25
    ordering = ['-attempt_time']

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['active_attempts'] = AccessAttempt.objects.all().order_by('-attempt_time')
        context['total_failures_count'] = AccessFailureLog.objects.count()
        context['active_lockouts_count'] = AccessAttempt.objects.count()
        return context
