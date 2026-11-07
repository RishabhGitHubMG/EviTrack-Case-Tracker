from django.urls import path

from apps.hearings import views

app_name = 'hearings'

urlpatterns = [
    path('', views.HearingListView.as_view(), name='hearing_list'),
    path('calendar/', views.CalendarView.as_view(), name='calendar'),
    path('case/<int:case_id>/new/', views.HearingCreateView.as_view(), name='hearing_create'),
    path('<int:pk>/', views.HearingDetailView.as_view(), name='hearing_detail'),
    path('<int:pk>/edit/', views.HearingUpdateView.as_view(), name='hearing_update'),
    path('<int:pk>/outcome/', views.HearingOutcomeView.as_view(), name='hearing_outcome'),
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/case/<int:case_id>/new/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_update'),
    path('tasks/<int:pk>/status/', views.TaskStatusUpdateView.as_view(), name='task_status'),
]
