from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import annotator_api.routing
import os

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "annotator.settings")

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter(
            annotator_api.routing.websocket_urlpatterns
        )
    ),
})

