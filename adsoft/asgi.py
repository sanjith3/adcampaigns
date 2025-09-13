# adsoft/asgi.py
import os
from django.core.asgi import get_asgi_application #type: ignore
from channels.routing import ProtocolTypeRouter, URLRouter #type: ignore
from channels.auth import AuthMiddlewareStack #type: ignore
import django_eventstream.routing #type: ignore
from django.urls import path #type: ignore

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adsoft.settings')

application = ProtocolTypeRouter({
    "http": URLRouter([
        path('events/', AuthMiddlewareStack(
            URLRouter(django_eventstream.routing.urlpatterns)
        )),
        path('', get_asgi_application()),
    ]),
})