"""
REST API Views for EviTrack Accounts & Session Management.
Provides endpoints for theme preference toggles, session status monitoring, and keep-alive pings.
"""
import time
from typing import Any

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class DarkModeToggleAPIView(APIView):
    """
    POST /api/auth/dark-mode/
    Updates or toggles the user's dark_mode preference.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        data = request.data

        if 'theme' in data:
            user.dark_mode = (str(data.get('theme')).lower() == 'dark')
        elif 'dark_mode' in data:
            val = data.get('dark_mode')
            if isinstance(val, str):
                user.dark_mode = val.lower() in ('true', '1', 'yes')
            else:
                user.dark_mode = bool(val)
        else:
            user.dark_mode = not user.dark_mode

        user.save(update_fields=['dark_mode'])
        theme = 'dark' if user.dark_mode else 'light'

        return Response({
            'status': 'ok',
            'dark_mode': user.dark_mode,
            'theme': theme,
        }, status=status.HTTP_200_OK)

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        theme = 'dark' if request.user.dark_mode else 'light'
        return Response({
            'dark_mode': request.user.dark_mode,
            'theme': theme,
        })


class SessionStatusAPIView(APIView):
    """
    GET /api/auth/session/status/
    Returns current session authentication state and remaining inactivity seconds.
    Used by the client-side JavaScript watchdog (evitrack.js).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if not request.user.is_authenticated:
            return Response({
                'is_authenticated': False,
                'remaining_seconds': 0,
                'timeout_seconds': getattr(settings, 'SESSION_TIMEOUT_SECONDS', 900),
            }, status=status.HTTP_200_OK)

        now = time.time()
        last_activity = request.session.get('last_activity', now)
        timeout_seconds = getattr(settings, 'SESSION_TIMEOUT_SECONDS', 900)
        warning_seconds = getattr(settings, 'SESSION_WARNING_SECONDS', 120)

        elapsed = now - last_activity
        remaining = max(0, int(timeout_seconds - elapsed))

        return Response({
            'is_authenticated': True,
            'timeout_seconds': timeout_seconds,
            'warning_seconds': warning_seconds,
            'remaining_seconds': remaining,
            'user': {
                'id': request.user.pk,
                'email': request.user.email,
                'full_name': request.user.get_full_name(),
                'role': request.user.role,
                'dark_mode': request.user.dark_mode,
            },
        }, status=status.HTTP_200_OK)


class SessionPingAPIView(APIView):
    """
    POST /api/auth/session/ping/
    Refreshes session last_activity timestamp to prevent inactivity timeout when user interacts with warning modal.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        now = time.time()
        request.session['last_activity'] = now
        return Response({
            'status': 'ok',
            'last_activity': now,
        }, status=status.HTTP_200_OK)
