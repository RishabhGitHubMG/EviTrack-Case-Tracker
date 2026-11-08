from django.urls import path

from apps.core.api.views import CsrfCookieAPIView, HealthAPIView

urlpatterns = [
    path('health/', HealthAPIView.as_view(), name='api_health'),
    path('auth/csrf/', CsrfCookieAPIView.as_view(), name='api_csrf'),
]
