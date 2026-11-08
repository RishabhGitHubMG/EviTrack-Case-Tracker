from django.urls import path

from apps.audit import views

app_name = 'audit'

urlpatterns = [
    path('', views.AuditLogListView.as_view(), name='audit_log_list'),
    path('my-activity/', views.MyActivityView.as_view(), name='my_activity'),
    path('export.csv', views.AuditLogExportView.as_view(), name='audit_log_export'),
    path('verify-chain/', views.AuditVerifyChainView.as_view(), name='audit_verify_chain'),
]
