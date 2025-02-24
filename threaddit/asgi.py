"""
ASGI config for threaddit project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'threaddit.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
from .middleware import JwtAuthMiddlewareStack
from communities.routing import websocket_urlpatterns as communiy_routing
from notifications.routing import websocket_urlpatterns as notifications_routing
from chats.routing import websocket_urlpatterns as chats_routing

websocket_urlpatterns = communiy_routing + notifications_routing + chats_routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JwtAuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
