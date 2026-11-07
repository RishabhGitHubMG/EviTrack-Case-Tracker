"""
Notification services for EviTrack.
"""
from typing import Any

from django.db.models import Q

from apps.accounts.models import User
from apps.notifications.models import Notification


def create_notification(
    user: Any,
    message: str,
    link: str = '',
    notification_type: str = Notification.NotificationType.INFO,
) -> Notification:
    """
    Creates an in-app notification for a user.
    """
    return Notification.objects.create(
        user=user,
        message=message,
        link=link,
        notification_type=notification_type,
    )


def notify_case_managers(
    case: Any,
    message: str,
    link: str = '',
    notification_type: str = Notification.NotificationType.INFO,
) -> list[Notification]:
    """
    Notifies the case's Case Managers (creator or assigned). Falls back to admins when none exist.
    """
    managers = list(
        User.objects.filter(is_active=True, role=User.Role.CASE_MANAGER)
        .filter(Q(pk=case.created_by_id) | Q(case_assignments__case=case))
        .distinct()
    )
    recipients = managers or list(User.objects.filter(is_active=True, role=User.Role.ADMIN))
    return [
        create_notification(user=user, message=message, link=link, notification_type=notification_type)
        for user in recipients
    ]
