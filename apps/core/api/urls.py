from django.urls import include, path

from apps.core.api.views import CsrfCookieAPIView, HealthAPIView

urlpatterns = [
    path('health/', HealthAPIView.as_view(), name='api_health'),
    path('auth/csrf/', CsrfCookieAPIView.as_view(), name='api_csrf'),
    path('auth/', include('apps.accounts.api_urls', namespace='accounts_api_v1')),
    path('cases/', include('apps.cases.api_urls', namespace='cases_api_v1')),
    path('evidence/', include('apps.evidence.api_urls', namespace='evidence_api_v1')),
    path('custody/', include('apps.custody.api_urls', namespace='custody_api_v1')),
    path('hearings/', include('apps.hearings.api_urls', namespace='hearings_api_v1')),
    path('notifications/', include('apps.notifications.api_urls', namespace='notifications_api_v1')),
    path('reports/', include('apps.reports.api_urls', namespace='reports_api_v1')),
    path('audit/', include('apps.audit.api_urls', namespace='audit_api_v1')),
]
