import pytest
from datetime import timedelta
from django.test import Client
from django.utils import timezone
from django.urls import reverse

from apps.accounts.models import User
from apps.hearings.models import Hearing
from apps.hearings.services import schedule_hearing_reminders
from apps.notifications.models import Reminder


@pytest.mark.django_db
@pytest.mark.parametrize('name', ['accounts:login', 'accounts:register'])
def test_public_account_pages_render(name):
    response = Client().get(reverse(name))

    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize('name', ['cases:case_list', 'core:dashboard', 'accounts:profile'])
def test_protected_pages_redirect_anonymous_users_to_login(name):
    response = Client().get(reverse(name))

    assert response.status_code == 302
    assert reverse('accounts:login') in response['Location']


@pytest.mark.django_db
@pytest.mark.parametrize('name', [
    'accounts:profile', 'accounts:password_change', 'accounts:otp_setup', 'accounts:user_list',
    'accounts:user_approval', 'accounts:failed_logins', 'accounts:preferences',
])
def test_account_pages_render_for_admin(make_user, client_for, name):
    admin = make_user(role=User.Role.ADMIN)

    response = client_for(admin).get(reverse(name))

    assert response.status_code == 200


@pytest.mark.django_db
def test_notification_preferences_update_and_reschedule(make_user, make_case, client_for):
    user = make_user()
    case = make_case(assignees=[user])
    hearing = Hearing.objects.create(
        case=case,
        hearing_date=timezone.now() + timedelta(days=10),
        court='District Court',
        purpose='Status hearing',
        created_by=case.created_by,
    )
    schedule_hearing_reminders(hearing)

    response = client_for(user).post(reverse('accounts:preferences'), {
        'notify_email': 'on',
        'notify_inapp': 'on',
        'hearing_reminder_minutes': ['1440'],
        'deadline_reminder_minutes': [],
    })

    assert response.status_code == 302
    user.refresh_from_db()
    assert user.hearing_reminder_minutes == [1440]
    assert user.deadline_reminder_minutes == []
    user_reminders = Reminder.objects.filter(user=user, target_id=hearing.pk)
    assert user_reminders.count() == 2
    assert set(user_reminders.values_list('remind_at', flat=True)) == {hearing.hearing_date - timedelta(days=1)}


@pytest.mark.django_db
def test_notification_preferences_can_disable_all_channels(make_user, make_case, client_for):
    user = make_user()
    case = make_case(assignees=[user])
    hearing = Hearing.objects.create(
        case=case,
        hearing_date=timezone.now() + timedelta(days=10),
        court='District Court',
        purpose='Status hearing',
        created_by=case.created_by,
    )
    schedule_hearing_reminders(hearing)

    response = client_for(user).post(reverse('accounts:preferences'), {
        'hearing_reminder_minutes': [],
        'deadline_reminder_minutes': [],
    })

    assert response.status_code == 302
    user.refresh_from_db()
    assert not user.notify_email
    assert not user.notify_sms
    assert not user.notify_inapp
    assert not Reminder.objects.filter(user=user, status=Reminder.Status.PENDING).exists()
