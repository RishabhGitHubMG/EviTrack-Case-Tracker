"""
URL configuration for audit app.
"""
from django.http import HttpResponse
from django.urls import path

app_name = 'audit'

urlpatterns = [
    path('', lambda r: HttpResponse('Audit Trail'), name='audit_log_list'),
    path('my-activity/', lambda r: HttpResponse('My Activity'), name='my_activity'),
]
