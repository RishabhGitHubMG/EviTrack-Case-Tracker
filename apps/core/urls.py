from django.urls import path

from apps.core import views

app_name = 'core'

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('search/', views.SearchPageView.as_view(), name='search'),
    path('api/search/', views.SearchAPIView.as_view(), name='search_api'),
    path('api/dashboard/charts/', views.DashboardChartsAPIView.as_view(), name='dashboard_charts'),
]
