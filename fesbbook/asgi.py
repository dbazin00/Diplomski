"""
ASGI config for fesbbook project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fesbbook.settings')

# application = get_asgi_application()


import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
# from django.conf.urls import url
from django.urls import path
from django.core.asgi import get_asgi_application
from channels.security.websocket import AllowedHostsOriginValidator,OriginValidator

from fesbbook_app.consumers import ChatConsumer, ConversationConsumer, ChatbotConsumer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "employee_project.settings")

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": get_asgi_application(),

    # WebSocket chat handler
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                path("conversation", ConversationConsumer.as_asgi()),
                path("conversation/<str:username>", ChatConsumer.as_asgi()),
                path("chatbot", ChatbotConsumer.as_asgi())
            ])
        ),
    )
})