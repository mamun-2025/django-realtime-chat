
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
   # ws/chat/ROOM_NAME/ এই প্যাটার্নে কানেকশন আসবে
   re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
   re_path(r'ws/chat/private/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]