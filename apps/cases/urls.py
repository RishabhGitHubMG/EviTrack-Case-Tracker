"""
URL routing configuration for the Cases module.
"""
from django.urls import path
from apps.cases import views

app_name = 'cases'

urlpatterns = [
    path('', views.CaseListView.as_view(), name='case_list'),
    path('create/', views.CaseCreateView.as_view(), name='case_create'),
    path('<int:pk>/', views.CaseDetailView.as_view(), name='case_detail'),
    path('<int:pk>/edit/', views.CaseUpdateView.as_view(), name='case_update'),
    path('<int:pk>/assign/', views.CaseAssignView.as_view(), name='case_assign'),
    path('<int:pk>/unassign/<int:assignment_id>/', views.CaseUnassignView.as_view(), name='case_unassign'),
    path('<int:pk>/parties/add/', views.PartyCreateView.as_view(), name='party_create'),
    path('<int:pk>/parties/<int:party_id>/edit/', views.PartyUpdateView.as_view(), name='party_update'),
    path('<int:pk>/parties/<int:party_id>/delete/', views.PartyDeleteView.as_view(), name='party_delete'),
    path('<int:pk>/timeline/', views.CaseTimelineView.as_view(), name='case_timeline'),
    # Aliases for dashboard and task list navigation
    path('dashboard/', views.CaseListView.as_view(), name='dashboard'),
    path('tasks/', views.CaseListView.as_view(), name='task_list'),
]
