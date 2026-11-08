import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.cases.models import Case, CaseAssignment, Party


@pytest.fixture
def admin_client(make_user, client_for):
    return client_for(make_user(role=User.Role.ADMIN))


@pytest.mark.django_db
@pytest.mark.parametrize('tab', [
    'overview', 'parties', 'evidence', 'custody', 'hearings', 'tasks', 'team', 'timeline', 'audit',
])
def test_case_detail_renders_every_tab(admin_client, make_case, tab):
    case = make_case()
    Party.objects.create(case=case, name='Jane Doe', party_type=Party.PartyType.WITNESS)

    response = admin_client.get(reverse('cases:case_detail', args=[case.pk]), {'tab': tab})

    assert response.status_code == 200


@pytest.mark.django_db
def test_case_list_and_forms_render(admin_client, make_case):
    case = make_case()

    assert admin_client.get(reverse('cases:case_list')).status_code == 200
    assert admin_client.get(reverse('cases:case_create')).status_code == 200
    assert admin_client.get(reverse('cases:case_update', args=[case.pk])).status_code == 200
    assert admin_client.get(reverse('cases:party_create', args=[case.pk])).status_code in (200, 405)


@pytest.mark.django_db
def test_only_case_managers_and_admins_can_create_cases(make_user, client_for):
    manager = make_user(role=User.Role.CASE_MANAGER)
    investigator = make_user(role=User.Role.INVESTIGATOR)
    url = reverse('cases:case_create')
    assert client_for(manager).get(url).status_code == 200
    assert client_for(investigator).get(url).status_code == 403
    response = client_for(investigator).post(url, {
        'title': 'Unauthorized case',
        'case_type': Case.CaseType.CIVIL,
        'priority': Case.Priority.MEDIUM,
        'description': 'Must not be created.',
    })
    assert response.status_code == 403
    assert not Case.objects.filter(title='Unauthorized case').exists()


@pytest.mark.django_db
def test_case_lead_cannot_close_case_but_can_edit_details(make_user, make_case, client_for):
    lead = make_user(role=User.Role.INVESTIGATOR)
    case = make_case(status=Case.Status.UNDER_INVESTIGATION, assignees=[lead])
    assignment = CaseAssignment.objects.get(case=case, user=lead)
    assignment.role_on_case = CaseAssignment.RoleOnCase.LEAD
    assignment.save(update_fields=['role_on_case'])
    client = client_for(lead)
    url = reverse('cases:case_update', kwargs={'pk': case.pk})

    response = client.post(url, {
        'title': 'Updated title',
        'case_type': case.case_type,
        'status': Case.Status.CLOSED,
        'priority': case.priority,
        'description': case.description,
        'closed_on': '',
    })

    assert response.status_code == 200
    case.refresh_from_db()
    assert case.status == Case.Status.UNDER_INVESTIGATION
    assert case.title == 'Sample case'
    assert 'status' in response.context['form'].errors

    response = client.post(url, {
        'title': 'Updated title',
        'case_type': case.case_type,
        'status': Case.Status.UNDER_INVESTIGATION,
        'priority': case.priority,
        'description': case.description,
        'closed_on': '',
    })
    assert response.status_code == 302
    case.refresh_from_db()
    assert case.title == 'Updated title'
    assert case.status == Case.Status.UNDER_INVESTIGATION


@pytest.mark.django_db
def test_case_members_cannot_manage_parties(make_user, make_case, client_for):
    member = make_user(role=User.Role.INVESTIGATOR)
    case = make_case(assignees=[member])
    party = Party.objects.create(case=case, name='Witness', party_type=Party.PartyType.WITNESS)
    client = client_for(member)
    detail_url = reverse('cases:case_detail', kwargs={'pk': case.pk})
    page = client.get(detail_url, {'tab': 'parties'})

    assert page.status_code == 200
    assert b'Add party' not in page.content
    assert reverse('cases:party_update', kwargs={'pk': case.pk, 'party_id': party.pk}).encode() not in page.content
    assert client.post(reverse('cases:party_create', kwargs={'pk': case.pk}), {'name': 'New'}).status_code == 403
    assert client.get(reverse('cases:party_update', kwargs={'pk': case.pk, 'party_id': party.pk})).status_code == 403
    assert client.post(reverse('cases:party_delete', kwargs={'pk': case.pk, 'party_id': party.pk})).status_code == 403


@pytest.mark.django_db
def test_case_sorting_preserves_filters_without_duplicate_parameters(admin_client, make_case):
    make_case()
    response = admin_client.get(reverse('cases:case_list'), {
        'q': 'needle', 'status': 'open', 'priority': 'high', 'case_type': 'civil',
        'sort': 'case_no', 'dir': 'desc', 'page': '1',
    })

    sort_query = response.context['sort_urls']['case_no']
    assert sort_query.count('sort=') == 1
    assert 'q=needle' in sort_query
    assert 'status=open' in sort_query
    assert 'priority=high' in sort_query
    assert 'case_type=civil' in sort_query
    assert 'page=' not in sort_query
    assert 'dir=asc' in sort_query
