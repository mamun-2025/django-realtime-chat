from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Message, PrivateChatRoom, PrivateMessage
from django.db.models import Q
from django.http import JsonResponse


def search_private_messages(request, room_id):
   query = request.GET.get('q', '').strip()
   if not query:
      return JsonResponse({'results': []})
   
   messages = PrivateMessage.objects.filter(
      room_id = room_id
   ).filter(
      Q(content__icontains=query) | Q(sender_username_icontains=query)
   ).order_by('-timestamp')[:20]

   results = []
   for msg in messages:
        results.append({
            'sender': msg.sender.username,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%H:%M %p'),
        })

   return JsonResponse({'results': results})



def get_or_create_private_room(u1, u2):
   user_ids = sorted([u1.id, u2.id])
   unique_room_id = f"private_{user_ids[0]}_{user_ids[1]}"
   room, created = PrivateChatRoom.objects.get_or_create(
      room_id = unique_room_id,
      defaults={'user1': u1, 'user2': u2}
   )
   return room 



def signup(request):
   if request.method == "POST":
      form = UserCreationForm(request.POST)
      if form.is_valid():
         user = form.save()
         login(request, user)
         return redirect('index')
   else:
      form = UserCreationForm()
   return render(request, 'chat/signup.html', {'form': form})


@login_required
def index(request):
   all_users = User.objects.exclude(id=request.user.id)
   return render(request, 'chat/index.html', {'all_users': all_users})

@login_required
def room(request, room_name):

   message = Message.objects.filter(room_name=room_name,).order_by('timestamp')[:50]
   return render(request, 'chat/room.html', {
      'room_name': room_name,
      'messages': message
      })


@login_required
def private_chat_view(request, target_user_id):
   target_user = get_object_or_404(User, id=target_user_id)
   room = get_or_create_private_room(request.user, target_user)

   messages = room.private_messages.all().order_by('timestamp')[:50]

   return render(request, 'chat/private_room.html', {
      'room': room,
      'target_user': target_user,
      'messages': messages,
      'room_name': room.room_id
   })
