"""
Notification context processors for EviTrack.
"""
from django.http import HttpRequest

from apps.notifications.models import Notification


def unread_notifications(request: HttpRequest) -> dict:
    """
    Provide the bell count and the five most recent notifications for authenticated users.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {'unread_notification_count': 0, 'recent_notifications': []}

    notifications = Notification.objects.filter(user=user)
    return {
        'unread_notification_count': notifications.filter(is_read=False).count(),
        'recent_notifications': notifications[:5],
    }
