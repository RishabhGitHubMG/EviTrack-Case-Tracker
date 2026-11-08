"""
Session Timeout Middleware for EviTrack.
Enforces session timeout and tracks user activity.
"""
import time
from django.conf import settings
from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin


class SessionTimeoutMiddleware(MiddlewareMixin):
    """
    Middleware that checks if a user session has exceeded SESSION_TIMEOUT_SECONDS
    of inactivity. If so, logs out the user. Web pages redirect to the login page;
    /api/v1/ requests receive a JSON 401 so the SPA can show its sign-in screen.
    """

    def process_request(self, request):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None

        current_time = time.time()
        last_activity = request.session.get('last_activity')
        timeout_seconds = getattr(settings, 'SESSION_TIMEOUT_SECONDS', 900)

        if last_activity is not None and (current_time - last_activity) > timeout_seconds:
            logout(request)
            if request.path.startswith('/api/v1/'):
                return JsonResponse(
                    {
                        'code': 'session_expired',
                        'message': 'Your session has expired due to inactivity. Sign in again.',
                        'fields': None,
                        'retry_after': None,
                    },
                    status=401,
                )
            return redirect(getattr(settings, 'LOGIN_URL', '/accounts/login/'))

        request.session['last_activity'] = current_time
        return None
