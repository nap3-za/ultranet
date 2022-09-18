# chat/routing.py
from django.urls import re_path, path
from django.conf.urls import url

from main_asgi.consumers import MainConsumer
# from feature.consumers import UiConsumer
# from public_chat.consumers import PublicChatConsumer
# from notification.consumers import UiUpdateConsumer

websocket_urlpatterns = [
    path('<channel_name>/', MainConsumer.as_asgi()),
    path('private_chat/<room_id>/', MainConsumer.as_asgi()),
    path('public_chat/<room_id>/', MainConsumer.as_asgi()),
]