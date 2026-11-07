"""
URL configuration for notifications app.
"""
from django.http import HttpResponse
from django.urls import path

app_name = 'notifications'

urlpatterns = [
    path('', lambda r: HttpResponse('Notifications'), name='notification_list'),
    path('<int:pk>/', lambda r, pk: HttpResponse(f'Notification {pk}'), name='notification_detail'),
]
