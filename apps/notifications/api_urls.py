"""
REST API URL configuration for notifications app.
"""
from django.urls import path

from apps.notifications import views

app_name = 'notifications_api'

urlpatterns = [
    path('unread-count/', views.UnreadCountAPIView.as_view(), name='unread_count'),
]
