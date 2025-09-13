# adsoft/asgi.py
import os
from django.core.asgi import get_asgi_application #type: ignore

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adsoft.settings')

application = get_asgi_application()