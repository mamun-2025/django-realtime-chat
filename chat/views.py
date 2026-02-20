from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Message


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
   return render(request, 'chat/index.html')

@login_required
def room(request, room_name):

   message = Message.objects.filter(room_name=room_name,).order_by('timestamp')[:50]
   return render(request, 'chat/room.html', {
      'room_name': room_name,
      'messages': message
      })
