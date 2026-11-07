"""
Notification services for EviTrack.
"""
from typing import Any
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
