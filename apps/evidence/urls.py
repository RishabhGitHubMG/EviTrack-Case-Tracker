"""
URL routing configuration for the Evidence Vault module.
"""
from django.urls import path
from apps.evidence import views

app_name = 'evidence'

urlpatterns = [
    path('', views.EvidenceListView.as_view(), name='evidence_list'),
    path('upload/', views.EvidenceUploadView.as_view(), name='evidence_upload_generic'),
    path('upload/<int:case_id>/', views.EvidenceUploadView.as_view(), name='evidence_upload'),
    path('<int:pk>/', views.EvidenceDetailView.as_view(), name='evidence_detail'),
    path('<int:pk>/edit/', views.EvidenceUpdateView.as_view(), name='evidence_update'),
    path('<int:pk>/download/', views.EvidenceDownloadView.as_view(), name='evidence_download'),
    path('<int:pk>/verify/', views.EvidenceVerifyView.as_view(), name='evidence_verify'),
    path('<int:pk>/qr/', views.EvidenceQRView.as_view(), name='evidence_qr'),
    path('<int:pk>/preview/', views.EvidencePreviewView.as_view(), name='evidence_preview'),
    path('case/<int:case_id>/bulk-verify/', views.EvidenceBulkVerifyView.as_view(), name='evidence_bulk_verify'),
]
