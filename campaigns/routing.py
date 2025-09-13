from django.urls import re_path #type: ignore

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/ad_updates/', consumers.AdUpdateConsumer.as_asgi()),
]
