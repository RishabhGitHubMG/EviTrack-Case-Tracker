import pytest
from django.test import Client
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from apps.accounts.models import User
from apps.core.api.exceptions import api_exception_handler
from apps.core.api.permissions import IsApprovedUser

pytestmark = pytest.mark.django_db


def test_health_is_public(client):
    response = client.get('/api/v1/health/')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_csrf_endpoint_sets_cookie(client):
    response = client.get('/api/v1/auth/csrf/')

    assert response.status_code == 200
    assert 'csrftoken' in response.cookies


def test_unauthenticated_api_response_uses_standard_shape(client):
    response = client.get('/api/v1/evidence/')

    assert response.status_code == 401
    assert response.json() == {
        'code': 'not_authenticated',
        'message': 'Authentication is required.',
        'fields': None,
        'retry_after': None,
    }


def test_validation_exception_uses_standard_shape():
    request = APIRequestFactory().post('/api/v1/cases/', {}, format='json')
    response = api_exception_handler(
        ValidationError({'title': ['This field is required.']}),
        {'request': request},
    )

    assert response.status_code == 400
    assert response.data == {
        'code': 'validation_error',
        'message': 'Please fix the highlighted fields.',
        'fields': {'title': ['This field is required.']},
        'retry_after': None,
    }


def test_csrf_is_required_for_authenticated_session_post(make_user):
    user = make_user()
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)

    rejected = client.post('/api/v1/auth/session/ping/')
    assert rejected.status_code == 403

    client.get('/api/v1/auth/csrf/')
    accepted = client.post(
        '/api/v1/auth/session/ping/',
        HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value,
    )
    assert accepted.status_code == 200


def test_approved_user_permission_rejects_pending_account(make_user):
    permission = IsApprovedUser()
    user = make_user(approved=False)
    request = type('Request', (), {'user': user})()

    assert permission.has_permission(request, None) is False


def test_schema_is_available_to_an_admin(client, make_user):
    admin = make_user(role=User.Role.ADMIN)
    client.force_login(admin)
    response = client.get('/api/schema/')

    assert response.status_code == 200
    assert 'openapi' in response.content.decode()
