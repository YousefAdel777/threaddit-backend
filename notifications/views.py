from django.shortcuts import render
from rest_framework import generics
from .models import Notification
from rest_framework.permissions import IsAuthenticated
from .serializers import NotificationSerializer

class NotificationsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

class NotificationsDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(user=self.request.user)