
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
   
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name = 'chat/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('private/<int:target_user_id>/', views.private_chat_view, name='private_chat'),
    path('<str:room_name>/', views.room, name='room'), 
    path('search/<str:room_id>/', views.search_private_messages, name='search_messages'),
    
    
]
