import re
from datetime import timedelta

import pytest
from django.urls import URLResolver, get_resolver, reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.cases.models import CaseAssignment, Party
from apps.custody.models import CustodyEvent
from apps.evidence.models import Evidence
from apps.hearings.models import Hearing, Task
from apps.notifications.models import Notification

ARG_PATTERN = re.compile(r'<(?:\w+:)?(\w+)>')


def _iter_routes(patterns, prefix='', namespace=''):
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            child_ns = f'{namespace}{pattern.namespace}:' if pattern.namespace else namespace
            yield from _iter_routes(pattern.url_patterns, prefix + str(pattern.pattern), child_ns)
        elif pattern.name:
            yield prefix + str(pattern.pattern), f'{namespace}{pattern.name}'


def _named_routes():
    for route, full_name in _iter_routes(get_resolver().url_patterns):
        if route.startswith('admin/'):
            continue
        yield route, full_name


@pytest.fixture
def world(make_user, make_case):
    admin = make_user(role=User.Role.ADMIN)
    investigator = make_user(role=User.Role.INVESTIGATOR)
    case = make_case(title='Crawl case', assignees=[investigator])
    assignment = CaseAssignment.objects.get(case=case, user=investigator)
    party = Party.objects.create(case=case, name='Synthetic Party', party_type=Party.PartyType.WITNESS)
    evidence = Evidence.objects.create(
        case=case, title='Crawl evidence', file_path='evidence/crawl.txt', original_filename='crawl.txt',
        mime_type='text/plain', file_size=4, sha256='0' * 64, uploaded_by=admin, current_holder=admin,
    )
    custody = CustodyEvent.objects.create(
        evidence=evidence, from_user=admin, to_user=investigator, reason='Synthetic transfer',
    )
    hearing = Hearing.objects.create(
        case=case, hearing_date=timezone.now() + timedelta(days=7), court='Synthetic Court',
        purpose='Crawl hearing', created_by=admin,
    )
    task = Task.objects.create(
        case=case, title='Crawl task', assigned_to=investigator, due_date=timezone.now() + timedelta(days=3),
        created_by=admin,
    )
    notification = Notification.objects.create(
        user=admin, message='Synthetic notice', notification_type=Notification.NotificationType.INFO,
    )
    return {
        'notification': notification, 'admin': admin, 'case': case, 'assignment': assignment, 'party': party,
        'evidence': evidence, 'custody': custody, 'hearing': hearing, 'task': task,
        'user': investigator,
    }


ARG_SOURCES = {
    'pk': {
        'case_detail': 'case', 'case_update': 'case', 'case_assign': 'case', 'case_timeline': 'case',
        'party_create': 'case', 'party_update': 'case', 'party_delete': 'case',
        'case_unassign': 'case',
        'evidence_detail': 'evidence', 'evidence_update': 'evidence', 'evidence_download': 'evidence',
        'evidence_verify': 'evidence', 'evidence_qr': 'evidence', 'evidence_preview': 'evidence',
        'custody_respond': 'custody',
        'notification_detail': 'notification',
        'api_evidence_verify': 'evidence',
        'hearing_detail': 'hearing', 'hearing_update': 'hearing', 'hearing_outcome': 'hearing',
        'task_update': 'task', 'task_status': 'task',
        'user_approve': 'user', 'user_reject': 'user', 'user_role': 'user',
    },
    'case_id': {'evidence_upload': 'case', 'evidence_bulk_verify': 'case', 'hearing_create': 'case', 'task_create': 'case'},
    'evidence_id': {'custody_request': 'evidence', 'custody_timeline': 'evidence', 'custody_qr_label': 'evidence'},
    'party_id': {'party_update': 'party', 'party_delete': 'party'},
    'assignment_id': {'case_unassign': 'assignment'},
}


def _kwargs_for(full_name, arg_names, world):
    bare = full_name.rsplit(':', 1)[-1]
    kwargs = {}
    for arg in arg_names:
        source = ARG_SOURCES.get(arg, {}).get(bare)
        if source is None:
            return None
        kwargs[arg] = world[source].pk
    return kwargs


@pytest.mark.django_db
def test_every_named_url_renders_without_server_errors(client_for, world):
    admin = world['admin']
    checked, unmapped = [], []

    for route, full_name in _named_routes():
        arg_names = ARG_PATTERN.findall(route)
        kwargs = _kwargs_for(full_name, arg_names, world) if arg_names else {}
        if kwargs is None:
            unmapped.append(full_name)
            continue

        url = reverse(full_name, kwargs=kwargs)
        response = client_for(admin).get(url)
        assert response.status_code < 500, f'{full_name} ({url}) returned {response.status_code}'
        checked.append(full_name)

    assert not unmapped, f'Add object mapping for: {unmapped}'
    assert len(checked) >= 40
