from django.urls import path
from . import views

urlpatterns = [
    path('chats/', views.ChatListCreateView.as_view(), name='chat-list-create'),
    path('chats/<int:pk>/', views.ChatDetailView.as_view(), name='chat-detail'),
    path('messages/', views.MessageListCreateView.as_view(), name='message-list-create'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='message-detail'),
    path('mark-as-read/', views.MarkAsReadView.as_view(), name='mark-as-read')
]