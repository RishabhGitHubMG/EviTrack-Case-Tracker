import hashlib
from pathlib import Path

import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.evidence.models import Evidence, IntegrityCheck
from apps.evidence.tasks import verify_case_evidence_task
from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db

CONTENT = b'synthetic evidence bytes'


@pytest.fixture
def stored_evidence(make_user, make_case, settings):
    manager = make_user(role=User.Role.CASE_MANAGER)
    investigator = make_user(role=User.Role.INVESTIGATOR)
    case = make_case(owner=manager, assignees=[investigator])
    relative = 'case_integrity/evidence.txt'
    path = Path(settings.EVIDENCE_ROOT) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(CONTENT)
    evidence = Evidence.objects.create(
        case=case, title='Integrity target', file_path=relative, original_filename='evidence.txt',
        mime_type='text/plain', file_size=len(CONTENT), sha256=hashlib.sha256(CONTENT).hexdigest(),
        uploaded_by=investigator, current_holder=investigator,
    )
    return {'manager': manager, 'investigator': investigator, 'case': case, 'evidence': evidence, 'path': path}


def _tamper(world):
    world['path'].write_bytes(b'altered bytes')


def test_untampered_verify_records_pass_and_sends_no_alert(client_for, stored_evidence):
    world = stored_evidence
    url = reverse('evidence:evidence_verify', kwargs={'pk': world['evidence'].pk})

    response = client_for(world['investigator']).post(url)

    assert response.status_code == 200
    world['evidence'].refresh_from_db()
    assert world['evidence'].status != Evidence.Status.FLAGGED
    assert IntegrityCheck.objects.get(evidence=world['evidence']).result == IntegrityCheck.Result.VERIFIED
    assert not Notification.objects.filter(notification_type=Notification.NotificationType.DANGER).exists()


def test_tampered_verify_flags_evidence_and_alerts_case_manager(client_for, stored_evidence):
    world = stored_evidence
    _tamper(world)
    url = reverse('evidence:evidence_verify', kwargs={'pk': world['evidence'].pk})

    response = client_for(world['investigator']).post(url)

    assert response.status_code == 200
    world['evidence'].refresh_from_db()
    assert world['evidence'].status == Evidence.Status.FLAGGED
    assert IntegrityCheck.objects.get(evidence=world['evidence']).result == IntegrityCheck.Result.MODIFIED
    alert = Notification.objects.get(user=world['manager'], notification_type=Notification.NotificationType.DANGER)
    assert world['evidence'].evidence_no in alert.message
    assert not Notification.objects.filter(user=world['investigator']).exists()


def test_bulk_verify_task_alerts_case_manager_on_tamper(stored_evidence):
    world = stored_evidence
    _tamper(world)

    result = verify_case_evidence_task(world['case'].pk, world['investigator'].pk)

    assert result['failed'] == 1
    assert Notification.objects.filter(
        user=world['manager'], notification_type=Notification.NotificationType.DANGER,
    ).exists()
