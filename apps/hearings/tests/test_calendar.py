from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.hearings.models import Hearing


@pytest.mark.django_db
def test_calendar_exposes_accessible_cases_for_hearing_creation(make_user, make_case, client_for):
    user = make_user()
    case = make_case(assignees=[user])

    response = client_for(user).get(reverse('hearings:calendar'))

    assert response.status_code == 200
    assert case.case_no.encode() in response.content
    assert b'data-create-url="/hearings/case/0/new/"' in response.content


@pytest.mark.django_db
def test_calendar_create_route_prefills_selected_date(make_user, make_case, client_for):
    user = make_user()
    case = make_case(assignees=[user])
    selected_date = (timezone.localtime() + timedelta(days=4)).replace(hour=9, minute=0, second=0, microsecond=0)
    url = reverse('hearings:hearing_create', kwargs={'case_id': case.pk})

    response = client_for(user).get(url, {'date': selected_date.strftime('%Y-%m-%dT%H:%M')})

    assert response.status_code == 200
    assert f'value="{selected_date:%Y-%m-%dT%H:%M}"'.encode() in response.content


@pytest.mark.django_db
def test_calendar_hearing_events_link_to_detail_and_edit(make_user, make_case, client_for):
    user = make_user()
    case = make_case(assignees=[user])
    hearing = Hearing.objects.create(
        case=case,
        hearing_date=timezone.now() + timedelta(days=2),
        court='District Court',
        purpose='Status hearing',
        created_by=case.created_by,
    )

    response = client_for(user).get(reverse('hearings_api:calendar_events_api'))

    assert response.status_code == 200
    event = next(event for event in response.json() if event['id'] == f'hearing-{hearing.pk}')
    assert event['url'] == reverse('hearings:hearing_detail', kwargs={'pk': hearing.pk})
    detail = client_for(user).get(event['url'])
    assert reverse('hearings:hearing_update', kwargs={'pk': hearing.pk}).encode() in detail.content


@pytest.mark.django_db
def test_read_only_reviewer_cannot_create_or_edit_hearings(make_user, make_case, client_for):
    reviewer = make_user(role='reviewer')
    case = make_case(assignees=[reviewer])
    hearing = Hearing.objects.create(
        case=case,
        hearing_date=timezone.now() + timedelta(days=2),
        court='District Court',
        purpose='Status hearing',
        created_by=case.created_by,
    )
    client = client_for(reviewer)

    assert client.get(reverse('hearings:hearing_create', kwargs={'case_id': case.pk})).status_code == 403
    assert client.get(reverse('hearings:hearing_update', kwargs={'pk': hearing.pk})).status_code == 403
    calendar = client.get(reverse('hearings:calendar'))
    assert b'Schedule hearing for' not in calendar.content
    detail_url = reverse('hearings:hearing_detail', kwargs={'pk': hearing.pk})
    detail = client.get(detail_url)
    assert b'Edit Hearing' not in detail.content
    assert b'Record Outcome' not in detail.content
    outcome_url = reverse('hearings:hearing_outcome', kwargs={'pk': hearing.pk})
    assert client.post(outcome_url, {'outcome': 'Updated'}).status_code == 403
    hearing.refresh_from_db()
    assert hearing.outcome == ''


@pytest.mark.django_db
def test_calendar_does_not_offer_inaccessible_cases(make_user, make_case, client_for):
    user = make_user()
    case = make_case()

    response = client_for(user).get(reverse('hearings:calendar'))

    assert response.status_code == 200
    assert case.case_no.encode() not in response.content
