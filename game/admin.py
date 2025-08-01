from django.contrib import admin
from .models import Player, Question, Answer, Room

admin.site.register(Player)
admin.site.register(Room)
admin.site.register(Question)
admin.site.register(Answer)
