import pytest
from django.core.cache import cache
from django.test import Client, override_settings
from django.urls import reverse

from apps.accounts.models import EmailOTPChallenge

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clear_rate_limit_cache():
    cache.clear()
    yield
    cache.clear()


def test_security_headers_include_csp():
    response = Client().get(reverse('accounts:login'))

    assert "default-src 'self'" in response['Content-Security-Policy']
    assert "script-src 'self'" in response['Content-Security-Policy']
    assert response['Referrer-Policy'] == 'same-origin'


@override_settings(SECURE_HSTS_SECONDS=3600, SECURE_HSTS_INCLUDE_SUBDOMAINS=True)
def test_hsts_header_is_sent_over_https():
    response = Client().get(reverse('accounts:login'), secure=True)

    assert response['Strict-Transport-Security'] == 'max-age=3600; includeSubDomains'


@override_settings(AUTH_LOGIN_RATE_LIMIT=2, AUTH_LOGIN_RATE_WINDOW_SECONDS=60)
def test_login_endpoint_returns_429_after_configured_limit(client, make_user):
    user = make_user()
    url = reverse('accounts:login')

    assert client.post(url, {'email': user.email, 'password': 'incorrect'}).status_code == 200
    assert client.post(url, {'email': user.email, 'password': 'incorrect'}).status_code == 200
    assert client.post(url, {'email': user.email, 'password': 'incorrect'}).status_code == 429


@override_settings(OTP_VERIFY_RATE_LIMIT=2, OTP_VERIFY_RATE_WINDOW_SECONDS=60, EMAIL_OTP_MAX_ATTEMPTS=10)
def test_otp_endpoint_is_rate_limited(client, make_user):
    user = make_user()
    client.post(reverse('accounts:login'), {'email': user.email, 'password': 'Sample#Pass1'})
    url = reverse('accounts:otp_verify')

    assert client.post(url, {'otp_code': '111111'}).status_code == 200
    assert client.post(url, {'otp_code': '222222'}).status_code == 200
    assert client.post(url, {'otp_code': '333333'}).status_code == 429
    assert EmailOTPChallenge.objects.get(user=user).attempts == 2


@override_settings(EVIDENCE_UPLOAD_RATE_LIMIT=2, EVIDENCE_UPLOAD_RATE_WINDOW_SECONDS=60)
def test_evidence_upload_endpoint_is_rate_limited(client_for, make_user, make_case):
    user = make_user()
    case = make_case(assignees=[user])
    client = client_for(user)
    url = reverse('evidence:evidence_upload', kwargs={'case_id': case.pk})

    assert client.post(url, {}, REMOTE_ADDR='192.0.2.1').status_code == 302
    assert client.post(url, {}, REMOTE_ADDR='192.0.2.1').status_code == 302
    assert client.post(url, {}, REMOTE_ADDR='192.0.2.1').status_code == 429
