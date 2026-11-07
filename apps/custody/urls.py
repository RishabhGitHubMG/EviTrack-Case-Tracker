from django.urls import path

from apps.custody import views

app_name = 'custody'

urlpatterns = [
    path('', views.CustodyListView.as_view(), name='custody_list'),
    path('evidence/<int:evidence_id>/request/', views.CustodyRequestView.as_view(), name='custody_request'),
    path('<int:pk>/respond/', views.CustodyRespondView.as_view(), name='custody_respond'),
    path('evidence/<int:evidence_id>/timeline/', views.CustodyTimelineView.as_view(), name='custody_timeline'),
    path('evidence/<int:evidence_id>/label/', views.CustodyQRLabelView.as_view(), name='custody_qr_label'),
]
