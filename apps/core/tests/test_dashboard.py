import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.cases.models import Case


@pytest.mark.django_db
def test_admin_dashboard_shows_all_cases_and_approvals(make_user, make_case, client_for):
    admin = make_user(role=User.Role.ADMIN)
    make_case(title='Case A')
    make_case(title='Case B')
    make_user(approved=False)

    response = client_for(admin).get(reverse('core:dashboard'))

    assert response.status_code == 200
    assert response.context['total_cases'] == 2
    assert response.context['pending_approvals'] == 1
    assert response.context['charts_url'] == reverse('core:dashboard_charts')


@pytest.mark.django_db
def test_investigator_dashboard_is_scoped_to_assigned_cases(make_user, make_case, client_for):
    investigator = make_user(role=User.Role.INVESTIGATOR)
    make_case(title='Not mine')
    make_case(title='Mine', assignees=[investigator])

    response = client_for(investigator).get(reverse('core:dashboard'))

    assert response.status_code == 200
    assert response.context['total_cases'] == 1
    assert response.context['pending_approvals'] is None


@pytest.mark.django_db
def test_charts_endpoint_returns_counts_per_status(make_user, make_case, client_for):
    admin = make_user(role=User.Role.ADMIN)
    make_case(title='Open one', status=Case.Status.OPEN)

    response = client_for(admin).get(reverse('core:dashboard_charts'))

    data = response.json()
    assert response.status_code == 200
    labels = data['cases_by_status']['labels']
    values = data['cases_by_status']['values']
    assert values[labels.index(Case.Status.OPEN.label)] == 1
    assert len(data['evidence_by_status']['labels']) == len(data['evidence_by_status']['values'])
