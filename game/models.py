from django.db import models
from django.contrib.auth.models import User

class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    score = models.IntegerField(default=0)
    
    def __str__(self):
        return self.user.username

class Question(models.Model):
    text = models.TextField()
    correct_answer = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.text[:50]

class Answer(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.CharField(max_length=100)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.player.user.username} - {self.answer_text}"