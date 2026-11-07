"""
URL configuration for accounts app.
"""
from django.http import HttpResponse
from django.urls import path

app_name = 'accounts'

urlpatterns = [
    path('login/', lambda r: HttpResponse('Login'), name='login'),
    path('logout/', lambda r: HttpResponse('Logout'), name='logout'),
    path('users/', lambda r: HttpResponse('User Directory'), name='user_list'),
    path('profile/', lambda r: HttpResponse('User Profile'), name='profile'),
    path('preferences/', lambda r: HttpResponse('User Preferences'), name='preferences'),
    path('security/', lambda r: HttpResponse('Security Settings'), name='security_settings'),
]
