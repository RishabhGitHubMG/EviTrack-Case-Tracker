from django.urls import path

from apps.notifications import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('mark-all-read/', views.NotificationMarkAllReadView.as_view(), name='notification_mark_all_read'),
    path('<int:pk>/', views.NotificationOpenView.as_view(), name='notification_detail'),
    path('<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification_mark_read'),
]
