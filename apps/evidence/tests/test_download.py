import hashlib
from pathlib import Path

import pytest
from django.test import override_settings
from django.urls import reverse

from apps.accounts.models import User
from apps.evidence.models import Evidence

pytestmark = pytest.mark.django_db

CONTENT = b'synthetic download bytes'


@pytest.fixture
def stored_evidence(make_user, make_case, settings):
    manager = make_user(role=User.Role.CASE_MANAGER)
    investigator = make_user(role=User.Role.INVESTIGATOR)
    outsider = make_user(role=User.Role.INVESTIGATOR)
    case = make_case(owner=manager, assignees=[investigator])
    relative = 'case_download/evidence.txt'
    path = Path(settings.EVIDENCE_ROOT) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(CONTENT)
    evidence = Evidence.objects.create(
        case=case, title='Download target', file_path=relative, original_filename='evidence.txt',
        mime_type='text/plain', file_size=len(CONTENT), sha256=hashlib.sha256(CONTENT).hexdigest(),
        uploaded_by=investigator, current_holder=investigator,
    )
    return {'investigator': investigator, 'outsider': outsider, 'evidence': evidence}


def _url(evidence):
    return reverse('evidence:evidence_download', kwargs={'pk': evidence.pk})


def test_download_streams_file_when_x_accel_disabled(client_for, stored_evidence):
    response = client_for(stored_evidence['investigator']).get(_url(stored_evidence['evidence']))

    assert response.status_code == 200
    assert b''.join(response.streaming_content) == CONTENT
    assert 'attachment' in response['Content-Disposition']
    assert 'X-Accel-Redirect' not in response


@override_settings(EVIDENCE_USE_X_ACCEL=True, EVIDENCE_X_ACCEL_LOCATION='/protected-evidence/')
def test_download_uses_x_accel_redirect_when_enabled(client_for, stored_evidence):
    response = client_for(stored_evidence['investigator']).get(_url(stored_evidence['evidence']))

    assert response.status_code == 200
    assert response['X-Accel-Redirect'] == '/protected-evidence/case_download/evidence.txt'
    assert response['Content-Type'] == 'text/plain'
    assert 'attachment' in response['Content-Disposition']
    assert response.content == b''


def test_download_denied_for_user_without_case_access(client_for, stored_evidence):
    response = client_for(stored_evidence['outsider']).get(_url(stored_evidence['evidence']))

    assert response.status_code in (403, 404)
