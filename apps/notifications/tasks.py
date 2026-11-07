"""
Celery background tasks for EviTrack notifications and reminders.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.module_loading import import_string

from apps.hearings.models import Hearing, Task
from apps.hearings.services import check_overdue_tasks
from apps.notifications.models import Notification, Reminder
from apps.notifications.services import create_notification, notify_case_managers

logger = logging.getLogger(__name__)


def _reminder_content(reminder):
    target = reminder.target
    if isinstance(target, Hearing):
        subject = f"Hearing reminder: {target.case.case_no}"
        message = (
            f"Hearing for case {target.case.case_no} is scheduled for "
            f"{timezone.localtime(target.hearing_date):%b %d, %Y at %H:%M} "
            f"at {target.court}. Purpose: {target.purpose}."
        )
        link = f'/hearings/{target.pk}/'
    elif isinstance(target, Task):
        subject = f"Deadline reminder: {target.title}"
        message = (
            f"Task '{target.title}' for case {target.case.case_no} is due "
            f"{timezone.localtime(target.due_date):%b %d, %Y at %H:%M}."
        )
        link = '/hearings/tasks/'
    else:
        raise ValueError('Reminder target no longer exists')
    return subject, message, link


def _send_reminder(reminder, subject, message, link):
    if reminder.channel == Reminder.Channel.EMAIL:
        sent_count = send_mail(
            subject, message, settings.DEFAULT_FROM_EMAIL, [reminder.user.email], fail_silently=False
        )
        if not sent_count:
            raise RuntimeError('Email backend did not send reminder')
    elif reminder.channel == Reminder.Channel.INAPP:
        create_notification(
            user=reminder.user,
            message=message,
            link=link,
            notification_type=Notification.NotificationType.INFO,
        )
    elif reminder.channel == Reminder.Channel.SMS:
        gateway = import_string(settings.SMS_GATEWAY_BACKEND)()
        gateway.send(reminder.user.phone, message)
    else:
        raise ValueError(f'Unsupported reminder channel: {reminder.channel}')


def _escalate_reminder(reminder, message):
    target = reminder.target
    case = getattr(target, 'case', None)
    if case is not None:
        escalation_message = f"Reminder delivery failed for {reminder.user.email}: {message}"
        notifications = notify_case_managers(
            case=case,
            message=escalation_message,
            link='/hearings/tasks/' if isinstance(target, Task) else f'/hearings/{target.pk}/',
            notification_type=Notification.NotificationType.WARNING,
        )
        for notification in notifications:
            try:
                sent_count = send_mail(
                    'Reminder delivery failed',
                    escalation_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [notification.user.email],
                    fail_silently=False,
                )
                if not sent_count:
                    raise RuntimeError('Email backend did not send escalation')
            except Exception:
                logger.exception('Failed to email reminder escalation to %s', notification.user_id)


def _process_reminder(reminder_id, now):
    with transaction.atomic():
        try:
            reminder = Reminder.objects.select_for_update().select_related('user', 'target_type').get(pk=reminder_id)
        except Reminder.DoesNotExist:
            return 'missing'

        if reminder.status != Reminder.Status.PENDING or reminder.remind_at > now:
            return 'skipped'

        try:
            subject, message, link = _reminder_content(reminder)
            _send_reminder(reminder, subject, message, link)
        except Exception as exc:
            reminder.attempts += 1
            reminder.last_error = str(exc)
            max_attempts = reminder.max_attempts or getattr(settings, 'REMINDER_MAX_ATTEMPTS', 3)
            if reminder.attempts >= max_attempts:
                reminder.status = Reminder.Status.FAILED
                reminder.save(update_fields=['attempts', 'last_error', 'status'])
                _escalate_reminder(reminder, str(exc))
                return 'failed'

            base_minutes = getattr(settings, 'REMINDER_BACKOFF_BASE_MINUTES', 5)
            delay_minutes = base_minutes * (2 ** (reminder.attempts - 1))
            reminder.remind_at = now + timedelta(minutes=delay_minutes)
            reminder.save(update_fields=['attempts', 'last_error', 'remind_at'])
            return 'retrying'

        reminder.status = Reminder.Status.SENT
        reminder.attempts += 1
        reminder.last_error = ''
        reminder.save(update_fields=['status', 'attempts', 'last_error'])
        return 'sent'


@shared_task
def scan_and_send_due_reminders():
    now = timezone.now()
    check_overdue_tasks()
    reminder_ids = list(
        Reminder.objects.filter(status=Reminder.Status.PENDING, remind_at__lte=now)
        .order_by('remind_at', 'pk')
        .values_list('pk', flat=True)
    )
    counts = {'sent': 0, 'retrying': 0, 'failed': 0}
    for reminder_id in reminder_ids:
        result = _process_reminder(reminder_id, now)
        if result in counts:
            counts[result] += 1
    return counts
