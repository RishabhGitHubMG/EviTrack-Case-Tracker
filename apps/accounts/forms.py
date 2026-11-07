"""
Accounts and Authentication Forms for EviTrack.
Includes registration, login, multi-factor OTP verification/setup, profile editing,
password changing, and administrative user approval and role assignment.
"""
import re
from typing import Any

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


def validate_password_strength(password: str) -> None:
    """
    Validates that a password satisfies strict CJIS/ISO security standards:
    - Minimum 8 characters in length
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one numerical digit (0-9)
    - At least one special symbol (!@#$%^&* etc.)
    """
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter (A-Z).")
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter (a-z).")
    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one digit (0-9).")
    if not re.search(r'[^A-Za-z0-9]', password):
        raise ValidationError("Password must contain at least one special symbol (!@#$%^&* etc.).")


class RegistrationForm(forms.ModelForm):
    """
    User registration form. Excludes the Admin role from self-selection.
    Creates account in is_approved=False state awaiting admin authorization.
    """
    # Exclude Admin role from self-registration
    PUBLIC_ROLE_CHOICES = [
        (User.Role.INVESTIGATOR, 'Investigator/Advocate'),
        (User.Role.CASE_MANAGER, 'Case Manager'),
        (User.Role.CUSTODIAN, 'Evidence Custodian'),
        (User.Role.REVIEWER, 'Read-only Reviewer'),
    ]

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
            'autocomplete': 'given-name',
        }),
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
            'autocomplete': 'family-name',
        }),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'official@agency.gov',
            'autocomplete': 'email',
        }),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1 (555) 000-0000',
            'autocomplete': 'tel',
        }),
    )
    role = forms.ChoiceField(
        choices=PUBLIC_ROLE_CHOICES,
        initial=User.Role.INVESTIGATOR,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        help_text="Select your departmental operational capacity.",
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••••••',
            'autocomplete': 'new-password',
            'id': 'id_password1',
        }),
        help_text="Minimum 8 characters with upper, lower, digit, and special character.",
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••••••',
            'autocomplete': 'new-password',
            'id': 'id_password2',
        }),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'role']

    def clean_email(self) -> str:
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean_password1(self) -> str:
        password = self.cleaned_data.get('password1')
        if password:
            validate_password_strength(password)
        return password

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "The two password fields did not match.")
        return cleaned_data

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = True
        user.is_approved = False  # Explicitly requires admin approval
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """
    Standard email and password login form with optional remember-me.
    """
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'official@agency.gov',
            'autocomplete': 'email',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••••••',
            'autocomplete': 'current-password',
        }),
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'rememberMeCheck',
        }),
    )

    def clean_email(self) -> str:
        return self.cleaned_data.get('email', '').strip().lower()


class OTPVerificationForm(forms.Form):
    """
    Form for validating 6-digit TOTP authentication tokens.
    """
    otp_code = forms.CharField(
        label="Authentication Code",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center font-mono',
            'placeholder': '000000',
            'maxlength': '6',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'pattern': '[0-9]{6}',
            'autofocus': True,
        }),
        help_text='Enter the 6-digit code from your email or authenticator app.',
    )

    def clean_otp_code(self) -> str:
        code = self.cleaned_data.get('otp_code', '').strip().replace(' ', '')
        if not code.isdigit() or len(code) != 6:
            raise ValidationError("Please enter a valid 6-digit numerical code.")
        return code


class OTPSetupForm(forms.Form):
    """
    Form for enabling or disabling TOTP two-factor authentication.
    """
    ACTION_CHOICES = (
        ('enable', 'Enable 2FA'),
        ('disable', 'Disable 2FA'),
    )
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.HiddenInput(),
        initial='enable',
    )
    otp_code = forms.CharField(
        label="Verification Code",
        max_length=6,
        min_length=6,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center font-mono',
            'placeholder': '000000',
            'maxlength': '6',
            'inputmode': 'numeric',
        }),
        help_text="Enter the 6-digit code shown in your authenticator app to confirm setup.",
    )

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        otp_code = cleaned_data.get('otp_code', '').strip()

        if action == 'enable' and not otp_code:
            self.add_error('otp_code', "A verification code is required to enable two-factor authentication.")
        return cleaned_data


class ProfileForm(forms.ModelForm):
    """
    User self-management profile form for personal details and notification preferences.
    """
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 (555) 000-0000'}),
    )
    dark_mode = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
    )
    notify_email = forms.BooleanField(
        required=False,
        label="Email Notifications",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    notify_sms = forms.BooleanField(
        required=False,
        label="SMS Urgent Alerts",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    notify_inapp = forms.BooleanField(
        required=False,
        label="In-App Notification Feed",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'phone',
            'dark_mode',
            'notify_email',
            'notify_sms',
            'notify_inapp',
        ]


class PasswordChangeForm(forms.Form):
    """
    Secure password change form verifying current password and enforcing strength rules on the new password.
    """
    old_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••••••',
            'autocomplete': 'current-password',
        }),
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••••••',
            'autocomplete': 'new-password',
            'id': 'id_new_password1',
        }),
        help_text="Minimum 8 characters with upper, lower, digit, and special character.",
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••••••',
            'autocomplete': 'new-password',
            'id': 'id_new_password2',
        }),
    )

    def __init__(self, user: User, *args: Any, **kwargs: Any) -> None:
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self) -> str:
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError("Your current password was entered incorrectly. Please try again.")
        return old_password

    def clean_new_password1(self) -> str:
        new_password1 = self.cleaned_data.get('new_password1')
        if new_password1:
            validate_password_strength(new_password1)
            if self.cleaned_data.get('old_password') and new_password1 == self.cleaned_data.get('old_password'):
                raise ValidationError("Your new password cannot be identical to your current password.")
        return new_password1

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            self.add_error('new_password2', "The two new password fields did not match.")
        return cleaned_data

    def save(self) -> User:
        self.user.set_password(self.cleaned_data['new_password1'])
        self.user.save()
        return self.user


class UserApprovalForm(forms.Form):
    """
    Administrative form to approve or reject/deactivate user accounts with optional audit notes.
    """
    ACTION_CHOICES = (
        ('approve', 'Approve Account'),
        ('reject', 'Reject / Deactivate Account'),
    )
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='approve',
    )
    notes = forms.CharField(
        label="Administrative Remarks / Justification",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional internal notes regarding this approval or rejection decision...',
        }),
    )


class UserRoleForm(forms.ModelForm):
    """
    Administrative form to modify a user's assigned role.
    """
    role = forms.ChoiceField(
        choices=User.Role.choices,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        help_text="Determines authorization boundaries across cases, evidence vault, and administration.",
    )

    class Meta:
        model = User
        fields = ['role']
