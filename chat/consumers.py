
from channels.db import database_sync_to_async
from .models import Message, PrivateChatRoom, PrivateMessage
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import datetime
import base64
import uuid
from django.core.files.base import ContentFile
from django.contrib.auth.models import User


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
        
        # শুরুতেই ইউজারনেম এবং সময় ডিফাইন করে নিন
        user = self.scope['user']
        username = user.username if user.is_authenticated else 'Anonymous'
        time_now = datetime.datetime.now().strftime('%I:%M %p')

        # ১. ইমেজ/ফাইল হ্যান্ডলিং
        if text_data_json.get('type') == 'file':
            file_data = text_data_json.get('file_data')
            file_name = text_data_json.get('file_name')
            format, imgstr = file_data.split(';base64,')
            ext = file_name.split('.')[-1]
            actual_file = ContentFile(base64.b64decode(imgstr), name=f"{uuid.uuid4()}.{ext}")

            # এখন 'username' ভেরিয়েবলটি উপরে ডিফাইন করা আছে, তাই এরর দেবে না
            msg_obj = await self.save_message(username, self.room_name, "", actual_file)

            await self.channel_layer.group_send(
                self.room_group_name, {
                    'type': 'chat_message',
                    'message': '',
                    'username': username,
                    'image_url': msg_obj.image.url,
                    'timestamp': time_now,
                    'message_id': msg_obj.id
                }
            )
            return

        # ২. রিড সিগন্যাল হ্যান্ডলিং
        if text_data_json.get('type') == 'message_read':
            msg_id = text_data_json.get('message_id')
            await self.mark_message_as_read(msg_id)
            await self.channel_layer.group_send(
                self.room_group_name, {
                    'type': 'message_read_update',
                    'message_id': msg_id
                }
            )
            return

        # ৩. টাইপিং হ্যান্ডলিং
        if text_data_json.get('type') == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name, {
                    'type': 'typing_status',
                    'username': username
                }
            )
            return

        # ৪. সাধারণ টেক্সট মেসেজ হ্যান্ডলিং
        if 'message' in text_data_json:
            message = text_data_json['message']
            msg_obj = await self.save_message(username, self.room_name, message)

            await self.channel_layer.group_send(
                self.room_group_name, {
                    'type': 'chat_message',
                    'message': message,
                    'username': username,
                    'timestamp': time_now,
                    'message_id': msg_obj.id,
                    'image_url': None
                }
            )


   async def typing_status(self, event):
      await self.send(text_data=json.dumps({
         'type': 'typing',
         'username': event['username']
      }))


   async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp'],
            'message_id': event.get('message_id'),
            'image_url': event.get('image_url'),
            'type': 'chat_message'
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

   async def message_read_update(self, event):
      await self.send(text_data=json.dumps({
         'type': 'message_read',
         'message_id': event['message_id']
      }))



   @database_sync_to_async
   def save_message(self, username, room_name, message_content, image_file=None):
      user = User.objects.get(username=username)

      if room_name.startswith('private_'):
         try:
            private_room = PrivateChatRoom.objects.get(room_id=room_name)
            return PrivateMessage.objects.create(
               room = private_room,
               sender = user,
               content = message_content,
               image = image_file
            )
         except PrivateChatRoom.DoesNotExist:
            return None
      else:
         return Message.objects.create(
            user=user, 
            room_name=room_name,
            content = message_content,
            image = image_file
         )


   @database_sync_to_async
   def mark_message_as_read(self, msg_id):
       try:
            if Message.objects.filter(id=msg_id).exists():
               Message.objects.filter(id=msg_id).update(is_read=True)
            else:
               PrivateMessage.objects.filter(id=msg_id).update(is_read=True)
       except:
          pass