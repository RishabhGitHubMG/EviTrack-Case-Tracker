import pytest
from django.test import Client

from apps.accounts.models import User
from apps.cases.models import Case, CaseAssignment


@pytest.fixture(autouse=True)
def evidence_root(settings, tmp_path):
    settings.EVIDENCE_ROOT = str(tmp_path / 'evidence_store')
    return settings.EVIDENCE_ROOT


@pytest.fixture
def make_user(db):
    counter = {'n': 0}

    def _make(role=User.Role.INVESTIGATOR, approved=True, password='Sample#Pass1', **extra):
        counter['n'] += 1
        n = counter['n']
        user = User.objects.create_user(
            email=extra.pop('email', f'user{n}@example.test'),
            password=password,
            first_name=extra.pop('first_name', 'Test'),
            last_name=extra.pop('last_name', f'User{n}'),
            role=role,
            is_approved=approved,
            **extra,
        )
        return user

    return _make


@pytest.fixture
def make_case(db, make_user):
    def _make(owner=None, assignees=(), title='Sample case', **extra):
        owner = owner or make_user(role=User.Role.CASE_MANAGER)
        case = Case.objects.create(
            title=title,
            description='Synthetic test case.',
            created_by=owner,
            **extra,
        )
        CaseAssignment.objects.create(case=case, user=owner, role_on_case=CaseAssignment.RoleOnCase.LEAD)
        for user in assignees:
            CaseAssignment.objects.get_or_create(case=case, user=user)
        return case

    return _make


@pytest.fixture
def client_for():
    def _client(user):
        client = Client()
        client.force_login(user)
        return client

    return _client
