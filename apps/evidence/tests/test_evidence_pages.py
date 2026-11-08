import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.evidence.models import Evidence, Tag


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


@pytest.mark.django_db
def test_evidence_tag_filter_selects_tag_and_limits_results(make_user, client_for, evidence):
    tag = Tag.objects.create(name='phone-extraction')
    evidence.tags.add(tag)
    other = Evidence.objects.create(
        case=evidence.case,
        title='Other file',
        original_filename='other.pdf',
        mime_type='application/pdf',
        file_size=10,
        sha256='b' * 64,
        uploaded_by=evidence.uploaded_by,
        current_holder=evidence.current_holder,
        file_path='evidence/other.pdf',
    )

    response = client_for(make_user(role=User.Role.ADMIN)).get(
        reverse('evidence:evidence_list'), {'tag': tag.name}
    )

    assert response.status_code == 200
    assert list(response.context['evidence_list']) == [evidence]
    assert response.context['selected_tag'] == tag.name
    assert f'<option value="{tag.name}" selected>'.encode() in response.content
    assert other.pk not in [item.pk for item in response.context['evidence_list']]


@pytest.mark.django_db
def test_evidence_tag_filter_does_not_expose_inaccessible_case_tags(make_user, make_case, client_for, evidence):
    user = make_user()
    accessible_case = make_case(assignees=[user])
    hidden_tag = Tag.objects.create(name='hidden-case-only')
    evidence.tags.add(hidden_tag)

    response = client_for(user).get(
        reverse('evidence:evidence_list'), {'tag': hidden_tag.name}
    )

    assert response.status_code == 200
    assert list(response.context['evidence_list']) == []
    assert hidden_tag not in response.context['all_tags']
    assert accessible_case.case_no.encode() in response.content
