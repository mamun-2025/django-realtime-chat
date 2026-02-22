from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
   user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
   room_name = models.CharField(max_length=255)
   content = models.TextField(null=True, blank=True)
   timestamp = models.DateTimeField(auto_now_add=True)
   is_read = models.BooleanField(default=False)
   image = models.ImageField(upload_to='chat_images/', null=True, blank=True)

   def __str__(self):
      return f'{self.user.username}:{self.content[:20] if self.content else "Image"}'
   
   class Meta:
      ordering = ('timestamp',)
      

class PrivateChatRoom(models.Model):
   user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user1_private_rooms')
   user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user2_private_rooms')
   room_id = models.CharField(max_length=255, unique=True)

   def __str__(self):
      return f"Private Chat: {self.user1.username} & {self.user2.username}"
   

class PrivateMessage(models.Model):
   room = models.ForeignKey(PrivateChatRoom, on_delete=models.CASCADE, related_name='private_messages')
   sender = models.ForeignKey(User, on_delete=models.CASCADE)
   content = models.TextField(null=True, blank=True)
   image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
   timestamp = models.DateTimeField(auto_now_add=True)
   is_read = models.BooleanField(default=False)

   def __str__(self):
      return f'{self.sender.username}: {self.content[:20] if self.content else "Image"}'
   
   class Meta:
      ordering = ('timestamp', )