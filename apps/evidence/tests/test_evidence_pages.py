import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.evidence.models import Evidence


@pytest.fixture
def evidence(make_case, make_user):
    case = make_case()
    uploader = make_user(role=User.Role.ADMIN)
    return Evidence.objects.create(
        case=case,
        title='Phone image',
        original_filename='scan.png',
        mime_type='image/png',
        file_size=10,
        sha256='a' * 64,
        uploaded_by=uploader,
        current_holder=uploader,
        file_path='evidence/scan.png',
    )


@pytest.mark.django_db
@pytest.mark.parametrize('name', ['evidence:evidence_list', 'evidence:evidence_upload_generic'])
def test_evidence_list_and_upload_render(make_user, client_for, name):
    response = client_for(make_user(role=User.Role.ADMIN)).get(reverse(name))

    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize('name', ['evidence:evidence_detail', 'evidence:evidence_update', 'evidence:evidence_qr'])
def test_evidence_item_pages_render(make_user, client_for, evidence, name):
    response = client_for(make_user(role=User.Role.ADMIN)).get(reverse(name, args=[evidence.pk]))

    assert response.status_code == 200
