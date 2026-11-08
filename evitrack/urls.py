"""
URL configuration for EviTrack project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core.api.views import SchemaAPIView

# Legacy API routes remain available until the SPA cutover.
api_urlpatterns = [
    path('auth/', include('apps.accounts.api_urls')),
    path('cases/', include('apps.cases.api_urls')),
    path('evidence/', include('apps.evidence.api_urls')),
    path('custody/', include('apps.custody.api_urls')),
    path('hearings/', include('apps.hearings.api_urls')),
    path('notifications/', include('apps.notifications.api_urls')),
    path('reports/', include('apps.reports.api_urls')),
    path('audit/', include('apps.audit.api_urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('cases/', include('apps.cases.urls')),
    path('evidence/', include('apps.evidence.urls')),
    path('custody/', include('apps.custody.urls')),
    path('hearings/', include('apps.hearings.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('reports/', include('apps.reports.urls')),
    path('audit/', include('apps.audit.urls')),
    path('api/v1/', include('apps.core.api.urls')),
    path('api/schema/', SchemaAPIView.as_view(), name='api_schema'),
    path('api/', include(api_urlpatterns)),
    path('', include('apps.core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler403 = 'apps.core.views.error_403'
handler404 = 'apps.core.views.error_404'
handler500 = 'apps.core.views.error_500'
