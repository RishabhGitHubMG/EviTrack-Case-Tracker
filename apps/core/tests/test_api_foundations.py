import pytest
from django.test import Client
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from apps.accounts.models import User
from apps.core.api.exceptions import api_exception_handler
from apps.core.api.pagination import StandardPagination
from apps.core.api.permissions import CaseObjectPermission, HasRole, IsApprovedUser
from apps.core.api.serializers import CaseRefSerializer, UserRefSerializer

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
    response = client.post('/api/auth/session/ping/')

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

    rejected = client.post('/api/auth/session/ping/')
    assert rejected.status_code == 403

    client.get('/api/v1/auth/csrf/')
    accepted = client.post(
        '/api/auth/session/ping/',
        HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value,
    )
    assert accepted.status_code == 200


def test_api_csrf_failure_uses_standard_error_shape(make_user):
    user = make_user()
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)

    response = client.post('/api/auth/session/ping/')

    assert response.status_code == 403
    assert response.json() == {
        'code': 'permission_denied',
        'message': 'You do not have permission to perform this action.',
        'fields': None,
        'retry_after': None,
    }


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
    schema = response.content.decode()
    assert 'openapi' in schema
    assert '/api/v1/health/' in schema
    assert '/api/v1/auth/csrf/' in schema


def test_schema_describes_authentication_requests_and_responses():
    from django.urls import include, path
    from drf_spectacular.generators import SchemaGenerator

    schema = SchemaGenerator(patterns=[path('api/v1/', include('apps.core.api.urls'))]).get_schema(
        request=None, public=True,
    )
    paths = schema['paths']
    login = paths['/api/v1/auth/login/']['post']
    assert login['requestBody']['content']['application/json']['schema']['$ref'].endswith('/LoginRequest')
    assert login['responses']['200']['content']['application/json']['schema']['$ref'].endswith('/LoginResponse')
    assert '429' in login['responses']
    assert '201' in paths['/api/v1/auth/register/']['post']['responses']
    assert '204' in paths['/api/v1/auth/logout/']['post']['responses']
    assert paths['/api/v1/auth/me/']['get']['security'] == [{'cookieAuth': []}]
    user = schema['components']['schemas']['User']['properties']
    assert user['preferences']['allOf'][0]['$ref'].endswith('/Preferences')
    assert user['pending_approvals']['nullable'] is True


def test_shared_reference_serializers_and_pagination(make_user, make_case):
    user = make_user(first_name='Ada', last_name='Lovelace')
    case = make_case(owner=user)

    assert UserRefSerializer(user).data == {
        'id': user.id,
        'name': 'Ada Lovelace',
        'role': User.Role.INVESTIGATOR,
        'initials': 'AL',
    }
    assert CaseRefSerializer(case).data == {
        'id': case.id,
        'case_no': case.case_no,
        'title': case.title,
    }
    assert StandardPagination.page_size == 20
    assert StandardPagination.max_page_size == 100


def test_role_and_case_permissions_use_existing_case_access(make_user, make_case):
    from apps.cases.models import CaseAssignment

    investigator = make_user(role=User.Role.INVESTIGATOR)
    case = make_case(assignees=(investigator,))
    request = APIRequestFactory().patch('/api/v1/cases/1/')
    request.user = investigator
    view = type('View', (), {'case_permission_level': 'edit'})()

    assert CaseObjectPermission().has_object_permission(request, view, case)

    CaseAssignment.objects.filter(case=case, user=investigator).delete()
    assert not CaseObjectPermission().has_object_permission(request, view, case)
    request.method = 'GET'
    assert not CaseObjectPermission().has_object_permission(request, view, case)
    request.user = make_user(approved=False)
    assert not IsApprovedUser().has_permission(request, None)


def test_role_permission_checks_configured_roles(make_user):
    user = make_user(role=User.Role.CUSTODIAN)
    request = type('Request', (), {'user': user})()
    permission = type(
        'CustodianPermission',
        (HasRole,),
        {'allowed_roles': (User.Role.CUSTODIAN,)},
    )()

    assert permission.has_permission(request, None)
