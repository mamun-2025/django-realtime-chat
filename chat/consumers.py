
from channels.db import database_sync_to_async
from .models import Message
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import datetime

class ChatConsumer(AsyncWebsocketConsumer):

   online_users = set()

   async def connect(self):
      self.room_name = self.scope['url_route']['kwargs']['room_name']
      self.room_group_name = f'chat_{self.room_name}'
      self.user = self.scope['user']

      if self.user.is_authenticated:
         ChatConsumer.online_users.add(self.user.username)

      await self.channel_layer.group_add(
         self.room_group_name,
         self.channel_name
      )
      await self.accept()

      await self.send_online_users()



   async def disconnect(self, close_code):

      if self.user.is_authenticated:
         ChatConsumer.online_users.discard(self.user.username)

      await self.channel_layer.group_discard(
         self.room_group_name,
         self.channel_name
      )

      await self.send_online_users()



   async def receive(self, text_data):
      text_data_json = json.loads(text_data)

      if text_data_json.get('type') == 'typing':
         await self.channel_layer.group_send(
            self.room_group_name,
            {
               'type': 'typing_status',
               'username': self.scope['user'].username
            }
         )
         return
   
      message = text_data_json['message']
      user = self.scope['user']
      time_now = datetime.datetime.now().strftime('%I:%M %p')


      username = user.username if user.is_authenticated else 'Anonymous'

      if user.is_authenticated:
         await self.save_message(username, self.room_name, message)

      await self.channel_layer.group_send(
         self.room_group_name,
         {
            'type': 'chat_message',
            'message': message,
            'username': username,
            'timestamp': time_now,
         }
      )

   async def typing_status(self, event):
      await self.send(text_data=json.dumps({
         'type': 'typing',
         'username': event['username']
      }))



   async def chat_message(self, event):
      message = event['message']
      username = event['username']
      timestamp = event['timestamp']

      await self.send(text_data=json.dumps({
         'message': message,
         'username': username,
         'timestamp': timestamp                                      
      }))

   async def send_online_users(self):
      await self.channel_layer.group_send(
         self.room_group_name,{
            'type': 'user_list_update',
            'users': list(ChatConsumer.online_users)
         }
      )

   async def user_list_update(self, event):
      await self.send(text_data=json.dumps({
         'type': 'user_list',
         'users': event['users']
      }))


   @database_sync_to_async
   def save_message(self, username, room, message):
      from django.contrib.auth.models import User
      user = User.objects.get(username=username)
      Message.objects.create(user=user, room_name= room, content=message)

