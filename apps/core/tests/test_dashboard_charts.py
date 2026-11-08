import pytest
from django.urls import reverse

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def test_charts_api_returns_all_dashboard_datasets(make_user, make_case, client_for):
    investigator = make_user(role=User.Role.INVESTIGATOR)
    make_case(owner=investigator, title='Chart case')

    payload = client_for(investigator).get(reverse('core:dashboard_charts')).json()

    assert set(payload) == {
        'cases_by_status', 'evidence_by_status', 'cases_by_type',
        'hearings_per_week', 'evidence_uploads', 'workload_per_user',
    }
    assert len(payload['hearings_per_week']['values']) == 8
    assert len(payload['evidence_uploads']['values']) == 8
    assert sum(payload['cases_by_type']['values']) == 1


def test_charts_api_excludes_inaccessible_cases(make_user, make_case, client_for):
    investigator = make_user(role=User.Role.INVESTIGATOR)
    other = make_user(role=User.Role.INVESTIGATOR)
    make_case(owner=other, title='Not mine')

    payload = client_for(investigator).get(reverse('core:dashboard_charts')).json()

    assert sum(payload['cases_by_type']['values']) == 0
    assert sum(payload['cases_by_status']['values']) == 0


def test_dashboard_page_has_all_chart_canvases(make_user, client_for):
    html = client_for(make_user(role=User.Role.INVESTIGATOR)).get('/dashboard/').content.decode()

    for canvas_id in ('cases-chart', 'evidence-chart', 'cases-type-chart',
                      'hearings-chart', 'workload-chart', 'uploads-chart'):
        assert f'id="{canvas_id}"' in html
