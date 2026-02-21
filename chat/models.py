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
      return f'{self.user.username}:{self.content[:20]}'
   
   class Meta:
      ordering = ('timestamp',)
      
