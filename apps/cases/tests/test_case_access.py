import pytest
from django.urls import reverse

from apps.accounts.mixins import get_user_accessible_cases
from apps.accounts.models import User


@pytest.mark.django_db
def test_unassigned_investigator_cannot_open_case(make_user, make_case, client_for):
    case = make_case()
    investigator = make_user(role=User.Role.INVESTIGATOR)

    response = client_for(investigator).get(reverse('cases:case_detail', args=[case.pk]))

    assert response.status_code == 403


@pytest.mark.django_db
def test_assigned_investigator_sees_only_assigned_cases(make_user, make_case):
    investigator = make_user(role=User.Role.INVESTIGATOR)
    assigned = make_case(assignees=[investigator])
    make_case(title='Other case')

    assert list(get_user_accessible_cases(investigator)) == [assigned]


@pytest.mark.django_db
def test_case_manager_sees_only_own_or_assigned_cases(make_user, make_case):
    manager = make_user(role=User.Role.CASE_MANAGER)
    own = make_case(owner=manager)
    make_case(title='Someone else')

    assert list(get_user_accessible_cases(manager)) == [own]


@pytest.mark.django_db
def test_admin_sees_every_case(make_user, make_case):
    admin = make_user(role=User.Role.ADMIN)
    cases = [make_case(), make_case(title='Second')]

    assert set(get_user_accessible_cases(admin)) == set(cases)
