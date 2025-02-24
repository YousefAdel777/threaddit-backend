from django.urls import path
from .consumers import CommunityConsumer

websocket_urlpatterns = [
    path('ws/community/<int:id>/', CommunityConsumer.as_asgi()),
]