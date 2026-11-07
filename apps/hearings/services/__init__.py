"""
Hearings, Tasks, Reminders, and Calendar service functions.
"""
import logging
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.services import log_audit_event
from apps.cases.models import Case
from apps.hearings.models import Hearing, Task
from apps.notifications.models import Notification, Reminder
from apps.notifications.services import create_notification

logger = logging.getLogger(__name__)


def schedule_hearing_reminders(hearing: Hearing) -> list[Reminder]:
    """
    Creates Reminder records at configured offsets (default 7d, 1d, 2h)
    before hearing_date for each user assigned to the case.
    Uses user preferences if defined, otherwise settings.REMINDER_DEFAULTS.
    Skips offsets that fall in the past.
    """
    now = timezone.now()
    hearing_dt = hearing.hearing_date
    if hearing_dt <= now:
        return []

    target_type = ContentType.objects.get_for_model(Hearing)

    # All assigned case users, case creator, and hearing creator
    assigned_users = User.objects.filter(
        Q(case_assignments__case=hearing.case) |
        Q(id=hearing.case.created_by_id) |
        Q(id=hearing.created_by_id),
        is_active=True
    ).distinct()

    reminder_defaults = getattr(settings, 'REMINDER_DEFAULTS', {})
    fallback_minutes = reminder_defaults.get(
        'hearing_reminders', [7 * 24 * 60, 24 * 60, 120]  # 7d, 1d, 2h
    )

    created_reminders: list[Reminder] = []

    for user in assigned_users:
        user_offsets = user.hearing_reminder_minutes or fallback_minutes

        # Determine channels based on preferences
        channels: list[str] = []
        if getattr(user, 'notify_email', True):
            channels.append(Reminder.Channel.EMAIL)
        if getattr(user, 'notify_inapp', True):
            channels.append(Reminder.Channel.INAPP)
        if getattr(user, 'notify_sms', False) and user.phone:
            channels.append(Reminder.Channel.SMS)

        if not channels:
            channels = [Reminder.Channel.EMAIL, Reminder.Channel.INAPP]

        for offset in user_offsets:
            remind_at = hearing_dt - timedelta(minutes=int(offset))
            if remind_at <= now:
                continue

            for channel in channels:
                dedup_key = f"h:{hearing.pk}:u:{user.pk}:m:{offset}:t:{int(remind_at.timestamp())}:c:{channel}"[:100]

                reminder, created = Reminder.objects.get_or_create(
                    dedup_key=dedup_key,
                    defaults={
                        'target_type': target_type,
                        'target_id': hearing.pk,
                        'remind_at': remind_at,
                        'channel': channel,
                        'status': Reminder.Status.PENDING,
                        'user': user,
                    }
                )
                if created:
                    created_reminders.append(reminder)

    return created_reminders


def schedule_task_reminders(task: Task) -> list[Reminder]:
    """
    Creates Reminder objects at 3d and 1d (or user preference) before due_date
    for the assigned_to user.
    """
    now = timezone.now()
    due_dt = task.due_date
    if due_dt <= now or task.status == Task.Status.COMPLETED:
        return []

    target_type = ContentType.objects.get_for_model(Task)
    user = task.assigned_to
    if not user.is_active:
        return []

    reminder_defaults = getattr(settings, 'REMINDER_DEFAULTS', {})
    fallback_minutes = reminder_defaults.get(
        'deadline_reminders', [3 * 24 * 60, 24 * 60]  # 3 days, 1 day
    )
    user_offsets = user.deadline_reminder_minutes or fallback_minutes

    channels: list[str] = []
    if getattr(user, 'notify_email', True):
        channels.append(Reminder.Channel.EMAIL)
    if getattr(user, 'notify_inapp', True):
        channels.append(Reminder.Channel.INAPP)
    if getattr(user, 'notify_sms', False) and user.phone:
        channels.append(Reminder.Channel.SMS)

    if not channels:
        channels = [Reminder.Channel.EMAIL, Reminder.Channel.INAPP]

    created_reminders: list[Reminder] = []

    for offset in user_offsets:
        remind_at = due_dt - timedelta(minutes=int(offset))
        if remind_at <= now:
            continue

        for channel in channels:
            dedup_key = f"t:{task.pk}:u:{user.pk}:m:{offset}:t:{int(remind_at.timestamp())}:c:{channel}"[:100]

            reminder, created = Reminder.objects.get_or_create(
                dedup_key=dedup_key,
                defaults={
                    'target_type': target_type,
                    'target_id': task.pk,
                    'remind_at': remind_at,
                    'channel': channel,
                    'status': Reminder.Status.PENDING,
                    'user': user,
                }
            )
            if created:
                created_reminders.append(reminder)

    return created_reminders


def cancel_pending_reminders(target: Any) -> int:
    """
    Deletes all pending Reminder objects for a given Hearing or Task.
    """
    target_type = ContentType.objects.get_for_model(target)
    count, _ = Reminder.objects.filter(
        target_type=target_type,
        target_id=target.pk,
        status=Reminder.Status.PENDING,
    ).delete()
    return count


@transaction.atomic
def create_hearing(
    case: Case,
    data: dict[str, Any],
    user: User,
    ip_address: str | None = None,
    user_agent: str = '',
) -> Hearing:
    """
    Creates a new Hearing, schedules court date reminders for assigned users,
    and logs the action in the audit trail.
    """
    hearing = Hearing.objects.create(
        case=case,
        hearing_date=data['hearing_date'],
        court=data['court'],
        purpose=data['purpose'],
        outcome=data.get('outcome', ''),
        next_hearing_date=data.get('next_hearing_date'),
        notes=data.get('notes', ''),
        created_by=user,
    )

    # Schedule reminders
    schedule_hearing_reminders(hearing)

    # Audit log
    log_audit_event(
        action='hearing.created',
        user=user,
        target=hearing,
        case=case,
        details={
            'hearing_id': hearing.pk,
            'hearing_date': str(hearing.hearing_date),
            'court': hearing.court,
            'purpose': hearing.purpose,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return hearing


@transaction.atomic
def update_hearing(
    hearing: Hearing,
    data: dict[str, Any],
    user: User,
    ip_address: str | None = None,
    user_agent: str = '',
) -> Hearing:
    """
    Updates an existing Hearing. If hearing_date changed, cancels old pending reminders
    and reschedules new ones.
    """
    old_date = hearing.hearing_date
    new_date = data.get('hearing_date', old_date)
    date_changed = (old_date != new_date)

    hearing.hearing_date = new_date
    hearing.court = data.get('court', hearing.court)
    hearing.purpose = data.get('purpose', hearing.purpose)
    hearing.outcome = data.get('outcome', hearing.outcome)
    hearing.next_hearing_date = data.get('next_hearing_date', hearing.next_hearing_date)
    hearing.notes = data.get('notes', hearing.notes)
    hearing.save()

    if date_changed:
        cancel_pending_reminders(hearing)
        schedule_hearing_reminders(hearing)

    # Audit log
    log_audit_event(
        action='hearing.updated',
        user=user,
        target=hearing,
        case=hearing.case,
        details={
            'hearing_id': hearing.pk,
            'date_changed': date_changed,
            'old_date': str(old_date),
            'new_date': str(hearing.hearing_date),
            'court': hearing.court,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return hearing


@transaction.atomic
def create_task(
    case: Case,
    data: dict[str, Any],
    user: User,
    ip_address: str | None = None,
    user_agent: str = '',
) -> Task:
    """
    Creates a new investigative or legal task, schedules deadline reminders,
    and logs the action in the audit trail.
    """
    task = Task.objects.create(
        case=case,
        title=data['title'],
        description=data.get('description', ''),
        assigned_to=data['assigned_to'],
        due_date=data['due_date'],
        is_filing_deadline=data.get('is_filing_deadline', False),
        created_by=user,
    )

    # Schedule reminders for assignee
    schedule_task_reminders(task)

    # Notify assignee if creator is different
    if task.assigned_to_id != user.id:
        try:
            task_url = reverse('hearings:task_list')
        except Exception:
            task_url = '/hearings/tasks/'

        create_notification(
            user=task.assigned_to,
            message=f"New task assigned: '{task.title}' on case {case.case_no} (Due: {task.due_date:%b %d, %H:%M}).",
            link=task_url,
            notification_type=Notification.NotificationType.INFO,
        )

    # Audit log
    log_audit_event(
        action='task.created',
        user=user,
        target=task,
        case=case,
        details={
            'task_id': task.pk,
            'title': task.title,
            'assigned_to_id': task.assigned_to_id,
            'due_date': str(task.due_date),
            'is_filing_deadline': task.is_filing_deadline,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return task


@transaction.atomic
def check_overdue_tasks() -> int:
    """
    Scans for tasks whose due_date is in the past and status is Pending or InProgress.
    Transitions their status to Overdue and dispatches urgent notifications to the
    assignee and Case Managers.
    """
    now = timezone.now()
    overdue_qs = Task.objects.filter(
        due_date__lt=now,
        status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS]
    ).select_related('case', 'assigned_to', 'case__created_by')

    updated_count = 0
    for task in overdue_qs:
        task.status = Task.Status.OVERDUE
        task.save(update_fields=['status'])
        updated_count += 1

        try:
            task_url = reverse('hearings:task_list')
        except Exception:
            task_url = '/hearings/tasks/'

        # Notification to assignee
        create_notification(
            user=task.assigned_to,
            message=f"OVERDUE: Task '{task.title}' for Case {task.case.case_no} is past deadline ({task.due_date:%Y-%m-%d %H:%M}).",
            link=task_url,
            notification_type=Notification.NotificationType.DANGER if task.is_filing_deadline else Notification.NotificationType.WARNING,
        )

        case_managers = list(
            User.objects.filter(is_active=True, role=User.Role.CASE_MANAGER)
            .filter(Q(pk=task.case.created_by_id) | Q(case_assignments__case=task.case))
            .exclude(pk=task.assigned_to_id)
            .distinct()
        )
        recipients = case_managers or list(
            User.objects.filter(is_active=True, role=User.Role.ADMIN).exclude(pk=task.assigned_to_id)
        )
        overdue_message = (
            f"Overdue task in {task.case.case_no}: '{task.title}' assigned to "
            f"{task.assigned_to.get_full_name() or task.assigned_to.email}."
        )
        for recipient in recipients:
            create_notification(
                user=recipient,
                message=overdue_message,
                link=task_url,
                notification_type=Notification.NotificationType.WARNING,
            )
        for recipient in recipients:
            try:
                send_mail(
                    f"Overdue task: {task.title}",
                    overdue_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient.email],
                    fail_silently=False,
                )
            except Exception:
                logger.exception('Failed to email overdue task escalation to %s', recipient.pk)

        # Audit record
        log_audit_event(
            action='task.marked_overdue',
            target=task,
            case=task.case,
            details={
                'task_id': task.pk,
                'due_date': str(task.due_date),
                'assigned_to_id': task.assigned_to_id,
            }
        )

    return updated_count
