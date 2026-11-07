"""
Authentication and OTP service layer for EviTrack accounts.
Handles TOTP generation, validation, QR code creation, and user lifecycle emails.
"""
import base64
import hmac
import io
import logging
import secrets
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import salted_hmac
import pyotp
import qrcode
from qrcode.image.pil import PilImage

from apps.accounts.models import EmailOTPChallenge, User

logger = logging.getLogger(__name__)


def _email_otp_hash(code: str) -> str:
    return salted_hmac('accounts.email_otp', code, secret=settings.SECRET_KEY).hexdigest()


@transaction.atomic
def send_email_otp(user: User) -> bool:
    now = timezone.now()
    challenge, _ = EmailOTPChallenge.objects.select_for_update().get_or_create(
        user=user,
        defaults={'code_hash': '', 'expires_at': now},
    )
    if challenge.locked_until and challenge.locked_until > now:
        return False
    if challenge.locked_until:
        challenge.attempts = 0
        challenge.locked_until = None

    code = f'{secrets.randbelow(1_000_000):06d}'
    challenge.code_hash = _email_otp_hash(code)
    challenge.expires_at = now + timedelta(minutes=settings.EMAIL_OTP_TTL_MINUTES)
    challenge.save()

    try:
        sent = send_mail(
            'Your EviTrack sign-in code',
            f'Your EviTrack sign-in code is {code}. It expires in {settings.EMAIL_OTP_TTL_MINUTES} minutes.',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception('Unable to send sign-in code to user %s', user.pk)
        return False
    return bool(sent)


@transaction.atomic
def verify_email_otp(user: User, code: str) -> bool:
    now = timezone.now()
    challenge = EmailOTPChallenge.objects.select_for_update().filter(user=user).first()
    if not challenge or (challenge.locked_until and challenge.locked_until > now):
        return False
    if challenge.expires_at <= now:
        return False

    if hmac.compare_digest(challenge.code_hash, _email_otp_hash(code)):
        challenge.delete()
        return True

    challenge.attempts += 1
    if challenge.attempts >= settings.EMAIL_OTP_MAX_ATTEMPTS:
        challenge.locked_until = now + timedelta(minutes=settings.EMAIL_OTP_LOCKOUT_MINUTES)
    challenge.save(update_fields=['attempts', 'locked_until', 'updated_at'])
    return False


def generate_otp_secret() -> str:
    """
    Generate a 32-character base32 secret suitable for TOTP authentication.
    """
    return pyotp.random_base32()


def verify_otp(user: User, code: str, secret: Optional[str] = None) -> bool:
    """
    Verify a TOTP token against the user's configured OTP secret or an explicit test secret.
    Allows a 1-step window (30 seconds before/after) for clock drift.
    """
    token_secret = secret or user.otp_secret
    if not token_secret or not code:
        return False

    # Strip any spaces or hyphens from input
    clean_code = str(code).strip().replace(' ', '').replace('-', '')
    if not clean_code.isdigit() or len(clean_code) != 6:
        return False

    totp = pyotp.TOTP(token_secret)
    return bool(totp.verify(clean_code, valid_window=1))


def get_otp_uri(user: User, secret: Optional[str] = None) -> str:
    """
    Generate the standard otpauth URI used by authenticator apps (e.g. Google Authenticator, Authy).
    """
    token_secret = secret or user.otp_secret
    if not token_secret:
        token_secret = generate_otp_secret()

    totp = pyotp.TOTP(token_secret)
    return totp.provisioning_uri(
        name=user.email,
        issuer_name='EviTrack',
    )


def generate_qr_code_b64(uri: str) -> str:
    """
    Generate a PNG QR code for the provisioning URI and return it as a base64 Data URI string.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=3,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    img: PilImage = qr.make_image(fill_color="#14213D", back_color="#FFFFFF")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64_encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{b64_encoded}"


def send_approval_email(user: User) -> None:
    """
    Send an email notification when a pending user account is approved by an administrator.
    """
    subject = "[EviTrack] Your Account Has Been Approved"
    message = (
        f"Hello {user.first_name or user.email},\n\n"
        "Your account registration for EviTrack (Digital Evidence & Chain of Custody System) "
        "has been reviewed and approved by an administrator.\n\n"
        f"Assigned Role: {user.get_role_display()}\n\n"
        "You can now sign in to your account at:\n"
        f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/accounts/login/\n\n"
        "If you encounter any issues accessing your account, please reach out to your system administrator.\n\n"
        "Best regards,\n"
        "EviTrack Security Administration"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as exc:
        logger.error("Failed to send approval email to %s: %s", user.email, exc)


def send_rejection_email(user: User, reason: str = "") -> None:
    """
    Send an email notification when a user registration is rejected or account is deactivated.
    """
    subject = "[EviTrack] Account Registration Status Update"
    reason_text = f"\nReason: {reason}\n" if reason else ""
    message = (
        f"Hello {user.first_name or user.email},\n\n"
        "Thank you for your interest in EviTrack. Your registration request has been reviewed "
        f"and could not be approved at this time.{reason_text}\n\n"
        "If you believe this was in error, please contact your internal EviTrack administrator.\n\n"
        "Best regards,\n"
        "EviTrack Security Administration"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as exc:
        logger.error("Failed to send rejection email to %s: %s", user.email, exc)
