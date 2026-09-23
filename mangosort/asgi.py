import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mangosort.settings')

# Inicializar la aplicación Django ASGI para que cargue los modelos antes de importar routing
django_asgi_app = get_asgi_application()

import mangosort.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            mangosort.routing.websocket_urlpatterns
        )
    ),
})

