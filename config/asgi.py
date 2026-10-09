"""
ASGI config for the Seasonal CRM project.

This module exposes the ASGI application used by Django
for both HTTP and WebSocket connections.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

django_application = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from config.routing import websocket_urlpatterns


application = ProtocolTypeRouter(
    {
        "http": django_application,

        "websocket": AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns,
            )
        ),
    }
)