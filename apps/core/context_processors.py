"""
Global context processors for EviTrack.
"""
from django.conf import settings
from django.http import HttpRequest


def global_context(request: HttpRequest) -> dict:
    """
    Expose global application settings to templates:
    session timeouts, branding, and color palette variables.
    """
    return {
        'APP_NAME': 'EviTrack',
        'APP_TAGLINE': 'Digital Evidence and Case Tracker',
        'SESSION_TIMEOUT_SECONDS': getattr(settings, 'SESSION_TIMEOUT_SECONDS', 900),
        'SESSION_WARNING_SECONDS': getattr(settings, 'SESSION_WARNING_SECONDS', 120),
    }
