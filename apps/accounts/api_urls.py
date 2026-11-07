"""
REST API URL configuration for accounts app.
"""
from django.urls import path
from apps.accounts import api_views

app_name = 'accounts_api'

urlpatterns = [
    # Dark mode & preferences
    path('dark-mode/', api_views.DarkModeToggleAPIView.as_view(), name='dark_mode'),
    path('preferences/theme/', api_views.DarkModeToggleAPIView.as_view(), name='preferences_theme'),

    # Session monitoring & keep-alive
    path('session/status/', api_views.SessionStatusAPIView.as_view(), name='session_status'),
    path('session/ping/', api_views.SessionPingAPIView.as_view(), name='session_ping'),
]
