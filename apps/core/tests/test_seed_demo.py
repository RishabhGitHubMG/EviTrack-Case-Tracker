from pathlib import Path

import pytest
from django.core.management import call_command
from django.conf import settings

from apps.accounts.models import User
from apps.cases.models import Case
from apps.custody.models import CustodyEvent
from apps.evidence.models import Evidence, IntegrityCheck
from apps.hearings.models import Hearing, Task
from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db


@pytest.fixture
def seeded(capsys):
    call_command('seed_demo')
    return capsys.readouterr().out


def test_seed_creates_one_user_per_role(seeded):
    roles = set(User.objects.filter(email__endswith='@demo.evitrack.test').values_list('role', flat=True))
    assert roles == {User.Role.ADMIN, User.Role.CASE_MANAGER, User.Role.INVESTIGATOR,
                     User.Role.CUSTODIAN, User.Role.REVIEWER}


def test_seed_volume_matches_demo_brief(seeded):
    assert Case.objects.count() == 8
    assert Evidence.objects.count() >= 15
    assert Hearing.objects.filter(hearing_date__lt=_now()).exists()
    assert Hearing.objects.filter(hearing_date__gt=_now()).exists()
    assert Task.objects.exists()
    assert Notification.objects.exists()


def test_seed_has_one_pending_transfer_and_history(seeded):
    pending = CustodyEvent.objects.filter(status=CustodyEvent.Status.REQUESTED)
    assert pending.count() == 1
    assert CustodyEvent.objects.filter(status=CustodyEvent.Status.ACCEPTED).count() >= 2
    assert CustodyEvent.objects.filter(status=CustodyEvent.Status.REJECTED).count() == 1


def test_seed_has_exactly_one_tampered_file(seeded):
    flagged = Evidence.objects.filter(status=Evidence.Status.FLAGGED)
    assert flagged.count() == 1
    assert IntegrityCheck.objects.filter(evidence=flagged.first(), result=IntegrityCheck.Result.MODIFIED).exists()
    assert Evidence.objects.exclude(status=Evidence.Status.FLAGGED).count() >= 15


def test_seed_prints_credentials(seeded):
    assert 'admin@demo.evitrack.test' in seeded
    assert 'reviewer@demo.evitrack.test' in seeded


def test_seed_is_idempotent(seeded):
    users_before = User.objects.count()

    call_command('seed_demo')

    assert User.objects.count() == users_before


def test_seeded_files_exist_on_disk(seeded):
    root = Path(settings.EVIDENCE_ROOT)
    for evidence in Evidence.objects.all():
        assert (root / evidence.file_path).is_file()


def _now():
    from django.utils import timezone
    return timezone.now()
