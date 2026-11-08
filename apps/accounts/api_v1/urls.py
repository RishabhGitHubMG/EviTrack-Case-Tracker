from django.urls import path

from apps.accounts.api_v1 import views

urlpatterns = [
    path('auth/register/', views.RegisterAPIView.as_view(), name='api_v1_register'),
    path('auth/login/', views.LoginAPIView.as_view(), name='api_v1_login'),
    path('auth/otp/verify/', views.OTPVerifyAPIView.as_view(), name='api_v1_otp_verify'),
    path('auth/otp/resend/', views.OTPResendAPIView.as_view(), name='api_v1_otp_resend'),
    path('auth/totp/verify/', views.TOTPVerifyAPIView.as_view(), name='api_v1_totp_verify'),
    path('auth/me/', views.MeAPIView.as_view(), name='api_v1_me'),
    path('auth/logout/', views.LogoutAPIView.as_view(), name='api_v1_logout'),
    path('auth/session/ping/', views.SessionPingAPIView.as_view(), name='api_v1_session_ping'),
]
