import time
from datetime import timedelta
from math import ceil

from axes.handlers.proxy import AxesProxyHandler
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.exceptions import Throttled, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api_v1.serializers import LoginSerializer, OTPCodeSerializer, RegisterSerializer, UserSerializer
from apps.accounts.forms import RegistrationForm
from apps.accounts.models import EmailOTPChallenge, User
from apps.accounts.services import mask_email, send_email_otp, verify_email_otp, verify_otp
from apps.audit.services.audit_service import log_action
from apps.core.api.exceptions import ApiError
from apps.core.api.permissions import IsApprovedUser
from apps.core.rate_limit import is_rate_limited

PENDING_SESSION_KEYS = ('pre_otp_user_id', 'pre_otp_backend', 'pre_otp_method', 'pre_otp_remember_me', 'pre_otp_next')
REGISTRATION_FIELD_MAP = {
    'first_name': 'name',
    'last_name': 'name',
    'password1': 'password',
    'role': 'requested_role',
}


def _seconds(delta: timedelta) -> int:
    return max(0, ceil(delta.total_seconds()))


def _clear_pending(request) -> None:
    for key in PENDING_SESSION_KEYS:
        request.session.pop(key, None)


def _enforce_throttle(request, scope: str, limit: int, window: int) -> None:
    if is_rate_limited(request._request, scope, limit, window):
        raise Throttled(wait=window)


def _locked_error(challenge: EmailOTPChallenge) -> ApiError:
    return ApiError(
        'otp_locked',
        'Too many invalid codes. Sign-in verification is locked temporarily.',
        403,
        retry_after=_seconds(challenge.locked_until - timezone.now()),
    )


def _account_locked_error(http_request) -> ApiError:
    # Axes would replace this JSON error with its HTML lockout page; keep the API contract.
    http_request.axes_locked_out = False
    return ApiError(
        'account_locked',
        'This account is locked after too many failed sign-in attempts.',
        403,
        retry_after=int(settings.AXES_COOLOFF_TIME.total_seconds()),
    )


def _pending_user(request, method: str) -> tuple[User, EmailOTPChallenge]:
    user_id = request.session.get('pre_otp_user_id')
    user = (
        User.objects.filter(pk=user_id, is_active=True, is_approved=True).first() if user_id else None
    )
    if user is None:
        _clear_pending(request)
        raise ApiError('pending_auth_required', 'Sign in again to continue.', 401)

    if request.session.get('pre_otp_method', 'email') != method:
        raise ApiError('auth_step_mismatch', 'This sign-in step is not active.', 409)

    if method == 'totp' and not user.otp_enabled:
        _clear_pending(request)
        raise ApiError('pending_auth_required', 'Sign in again to continue.', 401)

    challenge = EmailOTPChallenge.objects.filter(user=user).first()
    if challenge is None or challenge.expires_at <= timezone.now():
        _clear_pending(request)
        raise ApiError('otp_expired', 'Your sign-in code expired. Sign in again.', 401)

    if challenge.locked_until and challenge.locked_until > timezone.now():
        _clear_pending(request)
        raise _locked_error(challenge)

    return user, challenge


def _invalid_code_error(request, user: User, method: str) -> ApiError:
    challenge = EmailOTPChallenge.objects.filter(user=user).first()
    if challenge is not None and method == 'totp':
        challenge.attempts += 1
        if challenge.attempts >= settings.EMAIL_OTP_MAX_ATTEMPTS:
            challenge.locked_until = timezone.now() + timedelta(minutes=settings.EMAIL_OTP_LOCKOUT_MINUTES)
        challenge.save(update_fields=['attempts', 'locked_until', 'updated_at'])

    if challenge is not None and challenge.locked_until and challenge.locked_until > timezone.now():
        _clear_pending(request)
        return _locked_error(challenge)

    attempts_used = challenge.attempts if challenge is not None else settings.EMAIL_OTP_MAX_ATTEMPTS
    return ApiError(
        'otp_invalid',
        'Invalid or expired verification code.',
        400,
        extra={'attempts_left': max(0, settings.EMAIL_OTP_MAX_ATTEMPTS - attempts_used)},
    )


def _finish_login(request, user: User) -> None:
    backend = request.session.get('pre_otp_backend')
    remember_me = request.session.get('pre_otp_remember_me', False)
    _clear_pending(request)
    EmailOTPChallenge.objects.filter(user=user).delete()
    auth_login(request._request, user, backend=backend)
    request.session.set_expiry(settings.SESSION_COOKIE_AGE if remember_me else 0)


@method_decorator(csrf_protect, name='dispatch')
class PublicAuthAPIView(APIView):
    permission_classes = [AllowAny]


class RegisterAPIView(PublicAuthAPIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        first_name, _, last_name = data['name'].strip().partition(' ')

        form = RegistrationForm({
            'first_name': first_name,
            'last_name': last_name.strip(),
            'email': data['email'],
            'phone': data['phone'],
            'role': data['requested_role'],
            'password1': data['password'],
            'password2': data['password2'],
        })
        if not form.is_valid():
            fields = {}
            for field, errors in form.errors.items():
                fields.setdefault(REGISTRATION_FIELD_MAP.get(field, field), []).extend(errors)
            raise ValidationError(fields)

        user = form.save()
        log_action(user, 'account.registered', request=request._request, details={'role': user.role})
        return Response({'status': 'pending_approval'}, status=status.HTTP_201_CREATED)


class LoginAPIView(PublicAuthAPIView):
    def post(self, request):
        _enforce_throttle(request, 'api-login', settings.AUTH_LOGIN_RATE_LIMIT, settings.AUTH_LOGIN_RATE_WINDOW_SECONDS)
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].lower()
        password = serializer.validated_data['password']
        remember_me = serializer.validated_data['remember_me']

        http_request = request._request
        credentials = {'username': email}
        if not AxesProxyHandler.is_allowed(http_request, credentials):
            raise _account_locked_error(http_request)

        existing = User.objects.filter(email=email).first()
        if existing and not existing.is_active and existing.check_password(password):
            raise ApiError('account_inactive', 'This account has been deactivated. Contact your administrator.', 403)

        user = authenticate(http_request, username=email, password=password)
        if user is None:
            if not AxesProxyHandler.is_allowed(http_request, credentials):
                raise _account_locked_error(http_request)
            failures = AxesProxyHandler.get_failures(http_request, credentials)
            raise ApiError(
                'validation_error',
                'Invalid email address or password.',
                400,
                extra={'attempts_left': max(0, settings.AXES_FAILURE_LIMIT - failures)},
            )

        if not user.is_approved:
            raise ApiError('account_pending', 'Your account is awaiting administrator approval.', 403)

        if not send_email_otp(user):
            challenge = EmailOTPChallenge.objects.filter(user=user).first()
            if challenge is not None and challenge.locked_until and challenge.locked_until > timezone.now():
                raise _locked_error(challenge)
            raise ApiError('otp_send_failed', 'Unable to send a sign-in code. Please try again later.', 503)

        request.session['pre_otp_user_id'] = user.pk
        request.session['pre_otp_backend'] = getattr(user, 'backend', settings.AUTHENTICATION_BACKENDS[0])
        request.session['pre_otp_method'] = 'email'
        request.session['pre_otp_remember_me'] = remember_me
        request.session['pre_otp_next'] = settings.LOGIN_REDIRECT_URL

        return Response({
            'status': 'otp_required',
            'otp': {
                'sent_to_masked': mask_email(user.email),
                'expires_in': settings.EMAIL_OTP_TTL_MINUTES * 60,
                'resend_in': settings.EMAIL_OTP_RESEND_COOLDOWN_SECONDS,
            },
        })


class OTPVerifyAPIView(PublicAuthAPIView):
    def post(self, request):
        _enforce_throttle(request, 'api-otp-verify', settings.OTP_VERIFY_RATE_LIMIT, settings.OTP_VERIFY_RATE_WINDOW_SECONDS)
        serializer = OTPCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, _ = _pending_user(request, 'email')

        if not verify_email_otp(user, serializer.validated_data['code']):
            raise _invalid_code_error(request, user, 'email')

        if user.otp_enabled:
            EmailOTPChallenge.objects.update_or_create(
                user=user,
                defaults={
                    'code_hash': '',
                    'expires_at': timezone.now() + timedelta(minutes=settings.EMAIL_OTP_TTL_MINUTES),
                    'attempts': 0,
                    'locked_until': None,
                },
            )
            request.session['pre_otp_method'] = 'totp'
            return Response({'status': 'totp_required'})

        _finish_login(request, user)
        return Response({'status': 'authenticated'})


class OTPResendAPIView(PublicAuthAPIView):
    def post(self, request):
        user, challenge = _pending_user(request, 'email')
        sent_at = challenge.expires_at - timedelta(minutes=settings.EMAIL_OTP_TTL_MINUTES)
        cooldown_ends = sent_at + timedelta(seconds=settings.EMAIL_OTP_RESEND_COOLDOWN_SECONDS)
        wait = _seconds(cooldown_ends - timezone.now())
        if wait > 0:
            raise ApiError('resend_cooldown', 'Wait before requesting another code.', 429, retry_after=wait)

        if not send_email_otp(user):
            challenge.refresh_from_db()
            if challenge.locked_until and challenge.locked_until > timezone.now():
                raise _locked_error(challenge)
            raise ApiError('otp_send_failed', 'Unable to send a sign-in code. Please try again later.', 503)

        return Response({'resend_in': settings.EMAIL_OTP_RESEND_COOLDOWN_SECONDS})


class TOTPVerifyAPIView(PublicAuthAPIView):
    def post(self, request):
        _enforce_throttle(request, 'api-otp-verify', settings.OTP_VERIFY_RATE_LIMIT, settings.OTP_VERIFY_RATE_WINDOW_SECONDS)
        serializer = OTPCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, _ = _pending_user(request, 'totp')

        if not verify_otp(user, serializer.validated_data['code']):
            raise _invalid_code_error(request, user, 'totp')

        _finish_login(request, user)
        return Response({'status': 'authenticated'})


class MeAPIView(APIView):
    permission_classes = [IsApprovedUser]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class LogoutAPIView(APIView):
    permission_classes = [IsApprovedUser]

    def post(self, request):
        auth_logout(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionPingAPIView(APIView):
    permission_classes = [IsApprovedUser]

    def post(self, request):
        request.session['last_activity'] = time.time()
        return Response({'expires_in': settings.SESSION_TIMEOUT_SECONDS})
