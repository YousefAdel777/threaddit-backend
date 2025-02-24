from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.NotificationsListView.as_view(), name='notifications-list'),
    path('notifications/<int:pk>/', views.NotificationsDetailView.as_view(), name='notifications-detail'),
]