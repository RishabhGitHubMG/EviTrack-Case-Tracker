"""
URL configuration for reports app.
"""
from django.http import HttpResponse
from django.urls import path

app_name = 'reports'

urlpatterns = [
    path('', lambda r: HttpResponse('Reports and Analytics'), name='report_list'),
]
