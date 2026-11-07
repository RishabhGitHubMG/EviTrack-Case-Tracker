"""
REST API URL configuration for hearings app.
"""
from django.urls import path
from apps.hearings import views

app_name = 'hearings_api'

urlpatterns = [
    path('events/', views.CalendarEventsAPIView.as_view(), name='calendar_events_api'),
]
