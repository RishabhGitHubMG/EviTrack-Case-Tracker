from django.urls import path

from apps.reports import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportListView.as_view(), name='report_list'),
    path('cases/<int:case_id>/summary.pdf', views.CaseSummaryReportView.as_view(), name='case_summary'),
    path('cases/<int:case_id>/evidence.pdf', views.EvidenceRegisterReportView.as_view(), name='evidence_register'),
    path('cases/<int:case_id>/custody.pdf', views.CustodyHistoryReportView.as_view(), name='custody_history'),
    path('cases/<int:case_id>/hearings.pdf', views.HearingScheduleReportView.as_view(), name='hearing_schedule'),
    path('cases/<int:case_id>/integrity.pdf', views.IntegrityReportView.as_view(), name='integrity_report'),
]
