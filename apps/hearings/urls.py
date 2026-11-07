"""
URL configuration for hearings app.
"""
from django.http import HttpResponse
from django.urls import path

app_name = 'hearings'

urlpatterns = [
    path('', lambda r: HttpResponse('Hearings and Deadlines'), name='hearing_list'),
]
