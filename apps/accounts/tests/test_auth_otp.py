import re
from datetime import timedelta

import pyotp
import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import EmailOTPChallenge, User

pytestmark = pytest.mark.django_db


def start_login(client, user, password='Sample#Pass1'):
    return client.post(reverse('accounts:login'), {
        'email': user.email,
        'password': password,
        'remember_me': '',
    })


def test_login_requires_email_otp_and_verifies_code(client, make_user):
    user = make_user(email='login@example.test')

    response = start_login(client, user)

    assert response.status_code == 302
    assert response['Location'] == reverse('accounts:otp_verify')
    assert not response.wsgi_request.user.is_authenticated
    assert len(mail.outbox) == 1
    assert user.email in mail.outbox[0].to
    code = re.search(r'\b(\d{6})\b', mail.outbox[0].body).group(1)

    verify_page = client.get(reverse('accounts:otp_verify'))
    assert verify_page.status_code == 200
    assert 'code sent to' in verify_page.content.decode().lower()

    response = client.post(reverse('accounts:otp_verify'), {'otp_code': code})

    assert response.status_code == 302
    assert response['Location'] == '/dashboard/'
    assert response.wsgi_request.user.is_authenticated
    assert not EmailOTPChallenge.objects.filter(user=user).exists()


def test_totp_is_an_additional_step_after_email_otp(client, make_user):
    secret = pyotp.random_base32()
    user = make_user(otp_secret=secret, otp_enabled=True)

    response = start_login(client, user)

    assert response.status_code == 302
    assert response['Location'] == reverse('accounts:otp_verify')
    assert len(mail.outbox) == 1
    email_code = re.search(r'\b(\d{6})\b', mail.outbox[0].body).group(1)
    response = client.post(reverse('accounts:otp_verify'), {'otp_code': email_code})

    assert response.status_code == 302
    assert response['Location'] == reverse('accounts:otp_verify')
    verify_page = client.get(reverse('accounts:otp_verify'))
    assert 'authenticator app' in verify_page.content.decode().lower()

    response = client.post(reverse('accounts:otp_verify'), {'otp_code': pyotp.TOTP(secret).now()})

    assert response.status_code == 302
    assert response.wsgi_request.user.is_authenticated


def test_email_otp_locks_after_five_invalid_codes(client, make_user):
    user = make_user()
    start_login(client, user)
    sent_code = re.search(r'\b(\d{6})\b', mail.outbox[0].body).group(1)
    wrong_code = f'{(int(sent_code) + 1) % 1_000_000:06d}'

    for _ in range(5):
        response = client.post(reverse('accounts:otp_verify'), {'otp_code': wrong_code})

    assert response.status_code == 302
    assert response['Location'] == reverse('accounts:login')
    assert not response.wsgi_request.user.is_authenticated
    challenge = EmailOTPChallenge.objects.get(user=user)
    assert challenge.attempts == 5
    assert challenge.locked_until > timezone.now()

    login_response = start_login(client, user)
    assert login_response.status_code == 200
    assert 'Unable to send a sign-in code' in login_response.content.decode()
    assert len(mail.outbox) == 1


def test_expired_email_otp_requires_a_fresh_login(client, make_user):
    user = make_user()
    start_login(client, user)
    challenge = EmailOTPChallenge.objects.get(user=user)
    challenge.expires_at = timezone.now() - timedelta(seconds=1)
    challenge.save(update_fields=['expires_at'])

    response = client.get(reverse('accounts:otp_verify'))

    assert response.status_code == 302
    assert response['Location'] == reverse('accounts:login')
    assert 'pre_otp_user_id' not in client.session
