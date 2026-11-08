from django.urls import path
from apps.accounts import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('otp/', views.OTPVerifyView.as_view(), name='otp_verify'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('preferences/', views.NotificationPreferencesView.as_view(), name='preferences'),
    path('password/', views.PasswordChangeView.as_view(), name='password_change'),
    path('security/otp/', views.OTPSetupView.as_view(), name='otp_setup'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/approvals/', views.UserApprovalView.as_view(), name='user_approval'),
    path('users/<int:pk>/approve/', views.ApproveUserView.as_view(), name='user_approve'),
    path('users/<int:pk>/reject/', views.RejectUserView.as_view(), name='user_reject'),
    path('users/<int:pk>/role/', views.UserRoleChangeView.as_view(), name='user_role'),
    path('failed-logins/', views.FailedLoginListView.as_view(), name='failed_logins'),
    path('security/', views.SecurityPolicyView.as_view(), name='security_settings'),
]
