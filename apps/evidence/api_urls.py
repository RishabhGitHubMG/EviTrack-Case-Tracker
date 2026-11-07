"""
REST API URL routing configuration for Evidence Vault.
"""
from django.urls import path
from apps.evidence import api_views

app_name = 'evidence_api'

urlpatterns = [
    path('', api_views.EvidenceListAPIView.as_view(), name='api_evidence_list'),
    path('<int:pk>/verify/', api_views.EvidenceVerifyAPIView.as_view(), name='api_evidence_verify'),
]
