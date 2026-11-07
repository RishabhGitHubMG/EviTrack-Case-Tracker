"""
URL configuration for custody app.
"""
from django.http import HttpResponse
from django.urls import path

app_name = 'custody'

urlpatterns = [
    path('', lambda r: HttpResponse('Chain of Custody'), name='custody_list'),
]
