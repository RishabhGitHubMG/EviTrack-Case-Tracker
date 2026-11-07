import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.cases.models import Party


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
