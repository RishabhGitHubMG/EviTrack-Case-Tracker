import re
import time
from datetime import timedelta

import pyotp
import pytest
from django.conf import settings
from django.core import mail
from django.core.cache import cache
from django.test import Client, override_settings
from django.utils import timezone

from apps.accounts.models import EmailOTPChallenge, User
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db

BASE = '/api/v1/auth/'
PASSWORD = 'Sample#Pass1'


@pytest.fixture(autouse=True)
def clear_rate_limit_cache():
    cache.clear()
    yield
    cache.clear()


def post(client, path, data=None, **kwargs):
    return client.post(BASE + path, data or {}, content_type='application/json', **kwargs)


def start_login(client, user, **extra):
    return post(client, 'login/', {'email': user.email, 'password': PASSWORD, **extra})


def email_code():
    match = re.search(r'\b(\d{6})\b', mail.outbox[-1].body)
    assert match is not None
    return match.group(1)


def registration_data(**overrides):
    return {
        'name': 'Case Worker',
        'email': 'case.worker@example.test',
        'phone': '',
        'requested_role': User.Role.INVESTIGATOR,
        'password': 'Strong#Pass123',
        'password2': 'Strong#Pass123',
        **overrides,
    }


def test_register_creates_pending_user_and_audit_event(client):
    response = post(client, 'register/', registration_data())

    assert response.status_code == 201
    assert response.json() == {'status': 'pending_approval'}
    user = User.objects.get(email='case.worker@example.test')
    assert (user.first_name, user.last_name, user.role) == ('Case', 'Worker', User.Role.INVESTIGATOR)
    assert user.is_active and not user.is_approved
    assert user.check_password('Strong#Pass123')
    assert AuditLog.objects.filter(user=user, action='account.registered').exists()
    assert client.get(BASE + 'me/').status_code == 401


@pytest.mark.parametrize(('overrides', 'field'), [
    ({'password': 'weak', 'password2': 'weak'}, 'password'),
    ({'password2': 'Different#Pass123'}, 'password2'),
    ({'requested_role': User.Role.ADMIN}, 'requested_role'),
    ({'email': 'not-an-email'}, 'email'),
    ({'name': 'Single'}, 'name'),
])
def test_register_rejects_invalid_fields(client, overrides, field):
    response = post(client, 'register/', registration_data(**overrides))
    assert response.status_code == 400
    assert response.json()['code'] == 'validation_error'
    assert field in response.json()['fields']
    assert not User.objects.exists()


def test_register_rejects_duplicate_email_case_insensitively(client, make_user):
    make_user(email='case.worker@example.test')
    response = post(client, 'register/', registration_data(email='CASE.WORKER@example.test'))
    assert response.status_code == 400
    assert 'email' in response.json()['fields']
    assert User.objects.count() == 1


@pytest.mark.parametrize('remember_me', [False, True])
def test_email_login_me_and_logout(client, make_user, remember_me):
    user = make_user(email='login@example.test')
    response = start_login(client, user, remember_me=remember_me)
    assert response.status_code == 200
    assert response.json() == {
        'status': 'otp_required',
        'otp': {
            'sent_to_masked': 'lo***@example.test',
            'expires_in': settings.EMAIL_OTP_TTL_MINUTES * 60,
            'resend_in': settings.EMAIL_OTP_RESEND_COOLDOWN_SECONDS,
        },
    }
    assert len(mail.outbox) == 1 and mail.outbox[0].to == [user.email]
    assert email_code() not in response.content.decode()
    assert client.get(BASE + 'me/').status_code == 401

    response = post(client, 'otp/verify/', {'code': email_code()})
    assert response.status_code == 200
    assert response.json() == {'status': 'authenticated'}
    assert not EmailOTPChallenge.objects.filter(user=user).exists()
    assert 'pre_otp_user_id' not in client.session
    assert client.session.get_expire_at_browser_close() is (not remember_me)

    response = client.get(BASE + 'me/')
    assert response.status_code == 200
    data = response.json()
    assert (data['id'], data['email'], data['name'], data['role']) == (
        user.pk, user.email, user.get_full_name(), user.role,
    )
    assert 'cases.view' in data['permissions'] and 'admin.manage' not in data['permissions']
    assert data['preferences']['theme'] == 'light'
    assert data['totp_enabled'] is False
    assert data['unread_notifications'] == data['pending_custody'] == 0
    assert data['pending_approvals'] is None

    assert post(client, 'logout/').status_code == 204
    assert client.get(BASE + 'me/').status_code == 401
    assert post(client, 'session/ping/').status_code == 401


@pytest.mark.parametrize(('role', 'allowed', 'denied'), [
    (User.Role.ADMIN, {'cases.create', 'cases.assign', 'admin.manage', 'audit.view'}, set()),
    (User.Role.CASE_MANAGER, {'cases.create', 'cases.assign', 'audit.view'}, {'admin.manage'}),
    (User.Role.INVESTIGATOR, {'cases.edit', 'evidence.upload', 'hearings.manage'}, {'cases.create', 'admin.manage', 'audit.view'}),
    (User.Role.CUSTODIAN, {'evidence.upload', 'custody.transfer'}, {'cases.edit', 'hearings.manage', 'audit.view'}),
    (User.Role.REVIEWER, {'cases.view', 'evidence.integrity.view'}, {'evidence.upload', 'custody.transfer', 'audit.view'}),
])
def test_me_permissions_follow_role_matrix(client, make_user, role, allowed, denied):
    user = make_user(role=role)
    client.force_login(user)
    data = client.get(BASE + 'me/').json()
    permissions = set(data['permissions'])
    assert allowed <= permissions
    assert not denied & permissions
    assert (data['pending_approvals'] is not None) == (role == User.Role.ADMIN)


def test_login_invalid_password_and_axes_lockout(client, make_user):
    user = make_user()
    for attempt in range(1, settings.AXES_FAILURE_LIMIT):
        response = post(client, 'login/', {'email': user.email, 'password': 'incorrect'})
        assert response.status_code == 400
        assert response.json()['code'] == 'validation_error'
        assert response.json()['attempts_left'] == settings.AXES_FAILURE_LIMIT - attempt
    response = post(client, 'login/', {'email': user.email, 'password': 'incorrect'})
    assert response.status_code == 403
    assert response.json()['code'] == 'account_locked'
    assert response.json()['retry_after'] > 0
    assert start_login(client, user).json()['code'] == 'account_locked'
    assert not EmailOTPChallenge.objects.filter(user=user).exists()


@pytest.mark.parametrize(('user_options', 'code'), [
    ({'approved': False}, 'account_pending'),
    ({'is_active': False}, 'account_inactive'),
])
def test_login_rejects_pending_and_inactive_accounts(client, make_user, user_options, code):
    user = make_user(**user_options)
    response = start_login(client, user)
    assert response.status_code == 403
    assert response.json()['code'] == code
    assert not EmailOTPChallenge.objects.filter(user=user).exists()


def test_login_rejects_invalid_payload(client):
    response = post(client, 'login/', {'email': 'bad', 'password': PASSWORD})
    assert response.status_code == 400
    assert 'email' in response.json()['fields']


@override_settings(AUTH_LOGIN_RATE_LIMIT=2, AUTH_LOGIN_RATE_WINDOW_SECONDS=60)
def test_login_throttle(client, make_user):
    user = make_user()
    for _ in range(2):
        assert post(client, 'login/', {'email': user.email, 'password': 'incorrect'}).status_code == 400
    response = start_login(client, user)
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert response.json()['retry_after'] > 0


def test_email_otp_wrong_code_and_lockout(client, make_user):
    user = make_user()
    assert start_login(client, user).status_code == 200
    wrong = f'{(int(email_code()) + 1) % 1_000_000:06d}'
    for attempt in range(1, settings.EMAIL_OTP_MAX_ATTEMPTS):
        response = post(client, 'otp/verify/', {'code': wrong})
        assert response.status_code == 400
        assert response.json()['code'] == 'otp_invalid'
        assert response.json()['attempts_left'] == settings.EMAIL_OTP_MAX_ATTEMPTS - attempt
    response = post(client, 'otp/verify/', {'code': wrong})
    assert response.status_code == 403
    assert response.json()['code'] == 'otp_locked'
    assert response.json()['retry_after'] > 0
    challenge = EmailOTPChallenge.objects.get(user=user)
    assert challenge.attempts == settings.EMAIL_OTP_MAX_ATTEMPTS
    assert challenge.locked_until > timezone.now()
    assert 'pre_otp_user_id' not in client.session
    assert client.get(BASE + 'me/').status_code == 401
    assert start_login(client, user).json()['code'] == 'otp_locked'


@override_settings(OTP_VERIFY_RATE_LIMIT=2, OTP_VERIFY_RATE_WINDOW_SECONDS=60, EMAIL_OTP_MAX_ATTEMPTS=10)
def test_otp_verification_throttle_does_not_consume_an_attempt(client, make_user):
    user = make_user()
    start_login(client, user)
    wrong = f'{(int(email_code()) + 1) % 1_000_000:06d}'
    for _ in range(2):
        assert post(client, 'otp/verify/', {'code': wrong}).status_code == 400
    response = post(client, 'otp/verify/', {'code': wrong})
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert response.json()['retry_after'] > 0
    assert EmailOTPChallenge.objects.get(user=user).attempts == 2


def test_otp_expiry_clears_pending_session(client, make_user):
    user = make_user()
    start_login(client, user)
    code = email_code()
    EmailOTPChallenge.objects.filter(user=user).update(expires_at=timezone.now() - timedelta(seconds=1))
    response = post(client, 'otp/verify/', {'code': code})
    assert response.status_code == 401
    assert response.json()['code'] == 'otp_expired'
    assert 'pre_otp_user_id' not in client.session
    assert post(client, 'otp/verify/', {'code': code}).json()['code'] == 'pending_auth_required'


def test_otp_resend_cooldown_then_sends_new_email(client, make_user):
    user = make_user()
    start_login(client, user)
    response = post(client, 'otp/resend/')
    assert response.status_code == 429
    assert response.json()['code'] == 'resend_cooldown'
    assert response.json()['retry_after'] > 0
    assert len(mail.outbox) == 1

    challenge = EmailOTPChallenge.objects.get(user=user)
    challenge.expires_at -= timedelta(seconds=settings.EMAIL_OTP_RESEND_COOLDOWN_SECONDS + 1)
    challenge.save(update_fields=['expires_at'])
    response = post(client, 'otp/resend/')
    assert response.status_code == 200
    assert response.json() == {'resend_in': settings.EMAIL_OTP_RESEND_COOLDOWN_SECONDS}
    assert len(mail.outbox) == 2 and mail.outbox[-1].to == [user.email]
    assert post(client, 'otp/verify/', {'code': email_code()}).json() == {'status': 'authenticated'}


@pytest.mark.parametrize('path', ['otp/verify/', 'totp/verify/'])
def test_verify_requires_pending_session_and_valid_code(client, path):
    response = post(client, path, {'code': '123456'})
    assert response.status_code == 401
    assert response.json()['code'] == 'pending_auth_required'
    response = post(client, path, {'code': 'bad'})
    assert response.status_code == 400
    assert 'code' in response.json()['fields']


def test_totp_is_required_after_email_and_enforces_step_order(client, make_user):
    secret = pyotp.random_base32()
    user = make_user(otp_enabled=True, otp_secret=secret)
    start_login(client, user)
    response = post(client, 'totp/verify/', {'code': pyotp.TOTP(secret).now()})
    assert response.status_code == 409
    assert response.json()['code'] == 'auth_step_mismatch'
    response = post(client, 'otp/verify/', {'code': email_code()})
    assert response.status_code == 200
    assert response.json() == {'status': 'totp_required'}
    assert client.get(BASE + 'me/').status_code == 401
    response = post(client, 'otp/verify/', {'code': '123456'})
    assert response.status_code == 409
    assert response.json()['code'] == 'auth_step_mismatch'
    response = post(client, 'totp/verify/', {'code': pyotp.TOTP(secret).now()})
    assert response.status_code == 200
    assert response.json() == {'status': 'authenticated'}
    assert not EmailOTPChallenge.objects.filter(user=user).exists()
    assert client.get(BASE + 'me/').json()['totp_enabled'] is True


def test_totp_wrong_code_locks_pending_login(client, make_user):
    secret = pyotp.random_base32()
    user = make_user(otp_enabled=True, otp_secret=secret)
    start_login(client, user)
    assert post(client, 'otp/verify/', {'code': email_code()}).json()['status'] == 'totp_required'
    totp = pyotp.TOTP(secret)
    now = time.time()
    valid_codes = {totp.at(now + offset) for offset in (-60, -30, 0, 30, 60)}
    wrong = next(f'{n:06d}' for n in range(100) if f'{n:06d}' not in valid_codes)
    for attempt in range(1, settings.EMAIL_OTP_MAX_ATTEMPTS):
        response = post(client, 'totp/verify/', {'code': wrong})
        assert response.status_code == 400
        assert response.json()['code'] == 'otp_invalid'
        assert response.json()['attempts_left'] == settings.EMAIL_OTP_MAX_ATTEMPTS - attempt
    response = post(client, 'totp/verify/', {'code': wrong})
    assert response.status_code == 403
    assert response.json()['code'] == 'otp_locked'
    assert EmailOTPChallenge.objects.get(user=user).locked_until > timezone.now()
    assert 'pre_otp_user_id' not in client.session
    assert client.get(BASE + 'me/').status_code == 401


def test_session_ping_refreshes_activity_and_idle_expiry_logs_out(client, make_user):
    user = make_user()
    client.force_login(user)
    session = client.session
    session['last_activity'] = time.time() - 10
    session.save()
    previous = session['last_activity']
    response = post(client, 'session/ping/')
    assert response.status_code == 200
    assert response.json() == {'expires_in': settings.SESSION_TIMEOUT_SECONDS}
    assert client.session['last_activity'] > previous

    session = client.session
    session['last_activity'] = time.time() - settings.SESSION_TIMEOUT_SECONDS - 1
    session.save()
    response = post(client, 'session/ping/')
    assert response.status_code == 401
    assert response.json()['code'] == 'session_expired'
    assert client.get(BASE + 'me/').status_code == 401


def test_csrf_required_for_public_login_and_authenticated_ping(make_user):
    user = make_user()
    client = Client(enforce_csrf_checks=True)
    assert post(client, 'register/', registration_data()).status_code == 403
    assert start_login(client, user).status_code == 403
    csrf_response = client.get(BASE + 'csrf/')
    assert csrf_response.status_code == 200
    token = client.cookies['csrftoken'].value
    assert post(client, 'login/', {'email': user.email, 'password': PASSWORD}, HTTP_X_CSRFTOKEN=token).status_code == 200
    code = email_code()
    assert post(client, 'otp/verify/', {'code': code}).status_code == 403
    assert post(client, 'otp/verify/', {'code': code}, HTTP_X_CSRFTOKEN=token).status_code == 200

    assert post(client, 'session/ping/').status_code == 403
    client.get(BASE + 'csrf/')
    token = client.cookies['csrftoken'].value
    assert post(client, 'session/ping/', HTTP_X_CSRFTOKEN=token).status_code == 200
    assert post(client, 'logout/').status_code == 403
    assert post(client, 'logout/', HTTP_X_CSRFTOKEN=token).status_code == 204
