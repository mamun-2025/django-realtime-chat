

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
        username = self.scope['user'].username if self.scope['user'].is_authenticated else 'Anonymous'
        time_now = datetime.datetime.now().strftime('%I:%M %p')
        msg_type = text_data_json.get('type')

        # ১. অডিও মেসেজ হ্যান্ডলিং (সংশোধিত)
        if msg_type == 'audio':
            file_data = text_data_json.get('file_data')
            format, audiostream = file_data.split(';base64,')
            audio_file = ContentFile(base64.b64decode(audiostream), name=f"voice_{uuid.uuid4()}.wav")

            # আর্গুমেন্ট পাসিং নিশ্চিত করা (content="" এবং image=None)
            msg_obj = await self.save_message(username, self.room_name, "", None, audio_file)

            if msg_obj:
                await self.channel_layer.group_send(
                    self.room_group_name, {
                        'type': 'chat_message_broadcast',
                        'message': '',
                        'username': username,
                        'audio_url': msg_obj.audio.url,
                        'image_url': None,
                        'timestamp': time_now,
                        'message_id': msg_obj.id
                    }
                )
            return

        # ২. ইমেজ/ফাইল হ্যান্ডলিং (সংশোধিত)
        if msg_type == 'file':
            file_data = text_data_json.get('file_data')
            file_name = text_data_json.get('file_name')
            format, imgstr = file_data.split(';base64,')
            ext = file_name.split('.')[-1]
            actual_file = ContentFile(base64.b64decode(imgstr), name=f"{uuid.uuid4()}.{ext}")

            # আর্গুমেন্ট পাসিং নিশ্চিত করা (audio=None)
            msg_obj = await self.save_message(username, self.room_name, "", actual_file, None)

            if msg_obj:
                await self.channel_layer.group_send(
                    self.room_group_name, {
                        'type': 'chat_message_broadcast',
                        'message': '',
                        'username': username,
                        'image_url': msg_obj.image.url,
                        'audio_url': None,
                        'timestamp': time_now,
                        'message_id': msg_obj.id
                    }
                )
            return

        # ৩. টাইপিং এবং রিড সিগন্যাল (অপরিবর্তিত)
        if msg_type == 'message_read':
            msg_id = text_data_json.get('message_id')
            await self.mark_message_as_read(msg_id)
            await self.channel_layer.group_send(
                self.room_group_name, {'type': 'message_read_update', 'message_id': msg_id}
            )
            return

        if msg_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name, {'type': 'typing_status', 'username': username}
            )
            return

        # ৪. সাধারণ টেক্সট মেসেজ
        if 'message' in text_data_json:
            message = text_data_json['message']
            msg_obj = await self.save_message(username, self.room_name, message)

            if msg_obj:
                await self.channel_layer.group_send(
                    self.room_group_name, {
                        'type': 'chat_message_broadcast',
                        'message': message,
                        'username': username,
                        'timestamp': time_now,
                        'message_id': msg_obj.id,
                        'image_url': None,
                        'audio_url': None
                    }
                )

    # ইভেন্ট হ্যান্ডলার মেথডস (অপরিবর্তিত)
    async def chat_message_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp'],
            'message_id': event.get('message_id'),
            'image_url': event.get('image_url'),
            'audio_url': event.get('audio_url'),
        }))

    async def typing_status(self, event):
        await self.send(text_data=json.dumps({'type': 'typing', 'username': event['username']}))

    async def user_list_update(self, event):
        await self.send(text_data=json.dumps({'type': 'user_list', 'users': event['users']}))

    async def message_read_update(self, event):
        await self.send(text_data=json.dumps({'type': 'message_read', 'message_id': event['message_id']}))

    async def send_online_users(self):
        await self.channel_layer.group_send(
            self.room_group_name, {'type': 'user_list_update', 'users': list(ChatConsumer.online_users)}
        )

    # ডাটাব্যাস মেথডস (সংশোধিত)
    @database_sync_to_async
    def save_message(self, username, room_name, message_content, image_file=None, audio_file=None):
        try:
            user = User.objects.get(username=username)
            if room_name.startswith('private_'):
                private_room = PrivateChatRoom.objects.get(room_id=room_name)
                return PrivateMessage.objects.create(
                    room=private_room,
                    sender=user,
                    content=message_content,
                    image=image_file,
                    audio=audio_file
                )
            else:
                return Message.objects.create(
                    user=user, 
                    room_name=room_name,
                    content=message_content,
                    image=image_file,
                    audio=audio_file
                )
        except Exception as e:
            print(f"Error saving message: {e}")
            return None

    @database_sync_to_async
    def mark_message_as_read(self, msg_id):
        Message.objects.filter(id=msg_id).update(is_read=True)
        PrivateMessage.objects.filter(id=msg_id).update(is_read=True)