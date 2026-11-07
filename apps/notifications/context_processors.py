"""
Notification context processors for EviTrack.
"""
from django.http import HttpRequest


def unread_notifications(request: HttpRequest) -> dict:
    """
    Provide unread notification count for authenticated users.
    """
    if hasattr(request, 'user') and request.user.is_authenticated:
        # Placeholder count; will query Notification model when models are migrated
        return {
            'unread_notifications_count': 0,
        }
    return {
        'unread_notifications_count': 0,
    }
