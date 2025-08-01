from django.shortcuts import render, redirect
from .models import Room, Player
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate

@login_required
def index(request):
    
    rooms = Room.objects.all()
    players = Player.objects.all()
    return render(request, 'game/index.html', {'rooms': rooms, 'players': players})

@login_required
def room(request, room_name):
    
    room, created = Room.objects.get_or_create(name=room_name)
    
    
    player, created = Player.objects.get_or_create(user=request.user)
    player.room = room
    player.save()
    
    return render(request, 'game/room.html', {'room_name': room_name})