import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.custody.services import request_transfer
from apps.evidence.models import Evidence

pytestmark = pytest.mark.django_db


@pytest.fixture
def timeline_world(make_user, make_case):
    manager = make_user(role=User.Role.CASE_MANAGER)
    holder = make_user(role=User.Role.INVESTIGATOR)
    recipient = make_user(role=User.Role.CUSTODIAN)
    case = make_case(owner=manager, assignees=[holder, recipient])
    evidence = Evidence.objects.create(
        case=case, title='Timeline drive', file_path='evidence/timeline.txt',
        original_filename='timeline.txt', mime_type='text/plain', file_size=4, sha256='b' * 64,
        uploaded_by=holder, current_holder=holder,
    )
    request_transfer(evidence=evidence, from_user=holder, to_user=recipient, reason='Lab hand-off')
    return {'holder': holder, 'evidence': evidence}


def test_custody_timeline_page_renders_inside_layout(timeline_world, client_for):
    url = reverse('custody:custody_timeline', kwargs={'evidence_id': timeline_world['evidence'].pk})

    response = client_for(timeline_world['holder']).get(url)

    html = response.content.decode()
    assert response.status_code == 200
    assert 'class="app-sidebar"' in html
    assert 'Chain of Custody' in html
    assert 'Lab hand-off' in html


def test_custody_timeline_page_denies_outsider(timeline_world, make_user, client_for):
    outsider = make_user(role=User.Role.INVESTIGATOR)
    url = reverse('custody:custody_timeline', kwargs={'evidence_id': timeline_world['evidence'].pk})

    response = client_for(outsider).get(url)

    assert response.status_code == 403
