from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/lots/(?P<codigo_lote>[a-zA-Z0-9_-]+)/$', consumers.LotConsumer.as_asgi()),
]
