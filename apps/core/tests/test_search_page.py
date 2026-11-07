import pytest

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def test_search_page_requires_login(client):
    response = client.get('/search/?q=sample')

    assert response.status_code == 302
    assert '/accounts/login/' in response['Location']


def test_search_page_prompts_for_short_query(make_user, client_for):
    response = client_for(make_user(role=User.Role.INVESTIGATOR)).get('/search/?q=a')

    assert response.status_code == 200
    assert response.context['searched'] is False
    assert 'Start a search' in response.content.decode()


def test_search_page_groups_accessible_results_only(make_user, make_case, client_for):
    investigator = make_user(role=User.Role.INVESTIGATOR)
    other = make_user(role=User.Role.INVESTIGATOR)
    visible = make_case(owner=other, assignees=[investigator], title='Harbour Vault review')
    make_case(owner=other, title='Harbour Vault hidden')

    response = client_for(investigator).get('/search/?q=Harbour')

    html = response.content.decode()
    assert response.status_code == 200
    assert response.context['searched'] is True
    assert [group['name'] for group in response.context['groups']] == ['Cases']
    assert visible.case_no in html
    assert 'Harbour Vault hidden' not in html


def test_search_page_reports_no_matches(make_user, client_for):
    response = client_for(make_user(role=User.Role.INVESTIGATOR)).get('/search/?q=zzzz-nothing')

    assert response.status_code == 200
    assert response.context['total_results'] == 0
    assert 'No matches' in response.content.decode()


def test_search_api_keeps_result_shape(make_user, make_case, client_for):
    investigator = make_user(role=User.Role.INVESTIGATOR)
    make_case(owner=investigator, title='Shape check case')

    payload = client_for(investigator).get('/api/search/?q=Shape').json()

    assert payload['results']
    assert set(payload['results'][0]) == {'category', 'title', 'subtitle', 'url', 'icon'}
