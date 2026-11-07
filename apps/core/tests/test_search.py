import pytest
from django.urls import reverse

from apps.cases.models import Party
from apps.evidence.models import Evidence, Tag

pytestmark = pytest.mark.django_db


def test_search_groups_cases_parties_and_evidence(client_for, make_user, make_case):
    user = make_user()
    case = make_case(assignees=[user], title='Needle investigation')
    Party.objects.create(case=case, name='Needle witness', party_type=Party.PartyType.WITNESS)
    evidence = Evidence.objects.create(
        case=case,
        title='Needle sealed exhibit',
        file_path='evidence/sealed.pdf',
        original_filename='sealed.pdf',
        mime_type='application/pdf',
        file_size=10,
        sha256='a' * 64,
        uploaded_by=user,
    )
    tag = Tag.objects.create(name='NeedleTag')
    evidence.tags.add(tag)

    response = client_for(user).get(reverse('core:search_api'), {'q': 'needle'})

    assert response.status_code == 200
    grouped = {}
    for result in response.json()['results']:
        grouped.setdefault(result['category'], []).append(result)
    assert set(grouped) == {'Cases', 'Parties', 'Evidence'}
    assert grouped['Cases'][0]['url'] == reverse('cases:case_detail', kwargs={'pk': case.pk})
    assert grouped['Parties'][0]['title'] == 'Needle witness'
    assert grouped['Evidence'][0]['url'] == reverse('evidence:evidence_detail', kwargs={'pk': evidence.pk})

    hash_response = client_for(user).get(reverse('core:search_api'), {'q': 'aaaa'})
    assert any(result['category'] == 'Evidence' for result in hash_response.json()['results'])
    number_response = client_for(user).get(
        reverse('core:search_api'), {'q': evidence.evidence_no[:4]}
    )
    assert any(result['category'] == 'Evidence' for result in number_response.json()['results'])


def test_search_never_returns_records_from_inaccessible_cases(client_for, make_user, make_case):
    user = make_user()
    hidden_case = make_case(title='Hidden case')
    Party.objects.create(case=hidden_case, name='Hidden Needle person')
    Evidence.objects.create(
        case=hidden_case,
        title='Hidden Needle evidence',
        file_path='evidence/hidden.pdf',
        original_filename='hidden.pdf',
        mime_type='application/pdf',
        file_size=10,
        sha256='needle' + 'b' * 58,
        uploaded_by=hidden_case.created_by,
    )

    response = client_for(user).get(reverse('core:search_api'), {'q': 'needle'})

    assert response.status_code == 200
    assert response.json()['results'] == []


def test_search_requires_login(client):
    response = client.get(reverse('core:search_api'), {'q': 'case'})

    assert response.status_code == 302
    assert reverse('accounts:login') in response['Location']


def test_search_ignores_queries_shorter_than_two_characters(client_for, make_user):
    response = client_for(make_user()).get(reverse('core:search_api'), {'q': 'a'})

    assert response.status_code == 200
    assert response.json() == {'results': []}


def test_authenticated_header_exposes_search_and_shortcut(client_for, make_user):
    response = client_for(make_user()).get(reverse('core:dashboard'))

    assert response.status_code == 200
    assert 'id="topbarSearchInput"' in response.content.decode()
    assert 'Press / to focus' in response.content.decode()
