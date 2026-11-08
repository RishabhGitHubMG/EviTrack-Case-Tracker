import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.cases.models import CaseAssignment


@pytest.mark.django_db
def test_manager_can_assign_and_remove_case_members(make_user, make_case, client_for):
    manager = make_user(role=User.Role.CASE_MANAGER)
    case = make_case(owner=manager)
    candidate = make_user()
    client = client_for(manager)
    detail_url = reverse('cases:case_detail', kwargs={'pk': case.pk})
    assign_url = reverse('cases:case_assign', kwargs={'pk': case.pk})

    page = client.get(detail_url, {'tab': 'team'})
    assert page.status_code == 200
    assert f'action="{assign_url}"'.encode() in page.content

    response = client.post(assign_url, {'user': candidate.pk, 'role_on_case': CaseAssignment.RoleOnCase.MEMBER})

    assert response.status_code == 302
    assert response['Location'] == f'{detail_url}?tab=team#team'
    assignment = CaseAssignment.objects.get(case=case, user=candidate)
    remove_url = reverse('cases:case_unassign', kwargs={'pk': case.pk, 'assignment_id': assignment.pk})
    response = client.post(remove_url)

    assert response.status_code == 302
    assert response['Location'] == f'{detail_url}?tab=team#team'
    assert not CaseAssignment.objects.filter(pk=assignment.pk).exists()


@pytest.mark.django_db
def test_case_lead_cannot_manage_assignments(make_user, make_case, client_for):
    lead = make_user(role=User.Role.INVESTIGATOR)
    case = make_case(assignees=[lead])
    assignment = CaseAssignment.objects.get(case=case, user=lead)
    assignment.role_on_case = CaseAssignment.RoleOnCase.LEAD
    assignment.save(update_fields=['role_on_case'])
    client = client_for(lead)
    detail_url = reverse('cases:case_detail', kwargs={'pk': case.pk})
    assign_url = reverse('cases:case_assign', kwargs={'pk': case.pk})

    page = client.get(detail_url, {'tab': 'team'})

    assert page.status_code == 200
    assert b'Assign user' not in page.content
    assert b'/unassign/' not in page.content
    assert client.post(assign_url, {'user': make_user().pk, 'role_on_case': CaseAssignment.RoleOnCase.MEMBER}).status_code == 403
