from django.shortcuts import render
from .models import Message

def index(request):
   return render(request, 'chat/index.html')

def room(request, room_name):

   message = Message.objects.filter(room_name=room_name,).order_by('timestamp')[:50]
   return render(request, 'chat/room.html', {
      'room_name': room_name,
      'messages': message
      })
