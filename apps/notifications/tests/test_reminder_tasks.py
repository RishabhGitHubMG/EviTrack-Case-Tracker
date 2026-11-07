from datetime import timedelta
import logging
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.utils import timezone

from apps.accounts.models import User
from apps.hearings.models import Hearing, Task
from apps.hearings.services import check_overdue_tasks, schedule_hearing_reminders, schedule_task_reminders
from apps.notifications.models import Notification, Reminder
from apps.notifications.tasks import scan_and_send_due_reminders

pytestmark = pytest.mark.django_db


def make_reminder(user, target, channel=Reminder.Channel.EMAIL, **values):
    return Reminder.objects.create(
        target_type=ContentType.objects.get_for_model(target),
        target_id=target.pk,
        remind_at=timezone.now() - timedelta(minutes=1),
        channel=channel,
        user=user,
        dedup_key=f'test:{target._meta.model_name}:{target.pk}:{channel}:{values.get("dedup_suffix", "default")}',
        **{key: value for key, value in values.items() if key != 'dedup_suffix'},
    )


def make_hearing(case, creator, date=None):
    return Hearing.objects.create(
        case=case,
        hearing_date=date or timezone.now() + timedelta(days=2),
        court='District Court',
        purpose='Status hearing',
        created_by=creator,
    )


def test_default_schedules_create_hearing_and_task_offsets(make_user, make_case):
    assignee = make_user()
    case = make_case(assignees=[assignee])
    hearing = make_hearing(case, case.created_by, timezone.now() + timedelta(days=10))
    task = Task.objects.create(
        case=case,
        title='File response',
        assigned_to=assignee,
        due_date=timezone.now() + timedelta(days=5),
        created_by=case.created_by,
    )

    schedule_hearing_reminders(hearing)
    schedule_hearing_reminders(hearing)
    schedule_task_reminders(task)
    schedule_task_reminders(task)

    hearing_reminders = Reminder.objects.filter(
        target_type=ContentType.objects.get_for_model(Hearing), target_id=hearing.pk
    )
    task_reminders = Reminder.objects.filter(
        target_type=ContentType.objects.get_for_model(Task), target_id=task.pk
    )
    assert hearing_reminders.count() == 12
    assert task_reminders.count() == 4
    assert set(hearing_reminders.values_list('channel', flat=True)) == {Reminder.Channel.EMAIL, Reminder.Channel.INAPP}
    assert set(task_reminders.values_list('remind_at', flat=True)) == {
        task.due_date - timedelta(days=3), task.due_date - timedelta(days=1)
    }


def test_email_and_in_app_reminders_send_once(make_user, make_case):
    user = make_user()
    case = make_case(assignees=[user])
    hearing = make_hearing(case, case.created_by)
    email_reminder = make_reminder(user, hearing)
    inapp_reminder = make_reminder(user, hearing, Reminder.Channel.INAPP)

    assert scan_and_send_due_reminders() == {'sent': 2, 'retrying': 0, 'failed': 0}
    assert scan_and_send_due_reminders() == {'sent': 0, 'retrying': 0, 'failed': 0}

    email_reminder.refresh_from_db()
    inapp_reminder.refresh_from_db()
    assert email_reminder.status == Reminder.Status.SENT
    assert inapp_reminder.status == Reminder.Status.SENT
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [user.email]
    assert Notification.objects.filter(user=user, message__contains='Hearing for case').count() == 1


def test_sms_reminder_uses_mock_gateway(make_user, make_case, caplog):
    user = make_user(phone='+15555550123')
    case = make_case(assignees=[user])
    hearing = make_hearing(case, case.created_by)
    make_reminder(user, hearing, Reminder.Channel.SMS)

    with caplog.at_level(logging.INFO):
        result = scan_and_send_due_reminders()

    assert result['sent'] == 1
    assert 'Mock SMS to +15555550123' in caplog.text
    assert not mail.outbox


def test_email_failure_retries_with_backoff_then_escalates(make_user, make_case):
    manager = make_user(role=User.Role.CASE_MANAGER)
    user = make_user()
    case = make_case(owner=manager, assignees=[user])
    hearing = make_hearing(case, manager)
    reminder = make_reminder(user, hearing)
    with patch('apps.notifications.tasks.send_mail', side_effect=RuntimeError('mail unavailable')) as send_mail_mock:
        assert scan_and_send_due_reminders()['retrying'] == 1
        reminder.refresh_from_db()
        assert reminder.attempts == 1
        assert timezone.now() + timedelta(minutes=4) < reminder.remind_at < timezone.now() + timedelta(minutes=6)

        reminder.remind_at = timezone.now() - timedelta(minutes=1)
        reminder.save(update_fields=['remind_at'])
        assert scan_and_send_due_reminders()['retrying'] == 1
        reminder.refresh_from_db()
        assert reminder.attempts == 2
        assert timezone.now() + timedelta(minutes=9) < reminder.remind_at < timezone.now() + timedelta(minutes=11)

        reminder.remind_at = timezone.now() - timedelta(minutes=1)
        reminder.save(update_fields=['remind_at'])
        assert scan_and_send_due_reminders()['failed'] == 1

    reminder.refresh_from_db()
    assert reminder.status == Reminder.Status.FAILED
    assert reminder.attempts == 3
    assert send_mail_mock.call_count == 4
    assert send_mail_mock.call_args_list[-1].args[3] == [manager.email]
    assert Notification.objects.filter(user=manager, message__contains='Reminder delivery failed').count() == 1


def test_overdue_task_notifies_and_emails_case_manager_once(make_user, make_case):
    manager = make_user(role=User.Role.CASE_MANAGER)
    assignee = make_user()
    case = make_case(owner=manager, assignees=[assignee])
    task = Task.objects.create(
        case=case,
        title='Submit filing',
        assigned_to=assignee,
        due_date=timezone.now() - timedelta(minutes=1),
        created_by=manager,
    )

    assert check_overdue_tasks() == 1
    assert check_overdue_tasks() == 0
    task.refresh_from_db()

    assert task.status == Task.Status.OVERDUE
    assert Notification.objects.filter(user=manager, message__contains='Overdue task').count() == 1
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [manager.email]
