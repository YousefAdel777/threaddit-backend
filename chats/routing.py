from django.urls import path
from .consumers import MessagesConsumer, ChatConsumer

websocket_urlpatterns = [
    path('ws/chats/', ChatConsumer.as_asgi()),
    path('ws/messages', MessagesConsumer.as_asgi()),
]