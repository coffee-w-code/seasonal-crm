from django.urls import path

from apps.inventory.consumers import RealtimeVoiceCRMConsumer

websocket_urlpatterns = [
    path(
        "ws/ai/<int:business_id>/",
        RealtimeVoiceCRMConsumer.as_asgi(),
    ),
]