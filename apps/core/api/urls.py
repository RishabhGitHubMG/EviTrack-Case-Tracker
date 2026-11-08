from django.urls import include, path

from apps.core.api.views import CsrfCookieAPIView, HealthAPIView

urlpatterns = [
    path('health/', HealthAPIView.as_view(), name='api_health'),
    path('auth/csrf/', CsrfCookieAPIView.as_view(), name='api_csrf'),
    path('', include('apps.accounts.api_v1.urls')),
]
