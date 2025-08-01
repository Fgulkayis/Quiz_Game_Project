import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Player, Room, Question, Answer
from django.contrib.auth.models import User
import asyncio

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'quiz_%s' % self.room_name
        
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return
        
        await self.accept()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.add_player_to_room()
        player_count = await self.get_player_count()
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Oda: {self.room_name}, Hoş geldin, {self.user.username}! Odada {player_count} oyuncu var.'
        }))
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_join',
                'message': f'Yeni bir oyuncu katıldı. Toplam oyuncu sayısı: {player_count}'
            }
        )

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.remove_player_from_room()
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        player_count = await self.get_player_count()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_leave',
                'message': f'Bir oyuncu ayrıldı. Kalan oyuncu sayısı: {player_count}'
            }
        )
        
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')

        if message_type == 'start_game':
            
            await self.start_game()

        elif message_type == 'answer_question':
            
            user_answer = text_data_json.get('answer')
            await self.check_answer(user_answer)

        else:
            
            message = text_data_json.get('message')
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': f'{self.user.username}: {message}'
                }
            )
            
    
    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'message': message}))

    async def player_join(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'message': message}))

    async def player_leave(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'message': message}))
    
    async def new_question(self, event):
        question_data = event['question']
        await self.send(text_data=json.dumps({
            'type': 'new_question',
            'question': question_data
        }))

    async def score_update(self, event):
        score_data = event['scores']
        await self.send(text_data=json.dumps({
            'type': 'score_update',
            'scores': score_data
        }))

    @sync_to_async
    def get_room(self):
        return Room.objects.get(name=self.room_name)

    @sync_to_async
    def get_current_question(self, room):
        
        questions = Question.objects.all()
        if room.current_question_index < len(questions):
            return questions[room.current_question_index]
        return None

    @sync_to_async
    def get_all_players_and_scores(self):
        room = Room.objects.get(name=self.room_name)
        players = Player.objects.filter(room=room).order_by('-score')
        return {p.user.username: p.score for p in players}

    async def start_game(self):
        room = await self.get_room()
        
        
        if room.is_game_started:
            return

        room.is_game_started = True
        room.current_question_index = 0
        await sync_to_async(room.save)()

        await self.send_question_to_all(room)

    async def send_question_to_all(self, room):
        question = await self.get_current_question(room)
        
        if not question:
            
            await self.end_game()
            return
        
        question_data = {
            'text': question.text,
            'correct_answer': question.correct_answer 
        }
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'new_question',
                'question': question_data
            }
        )

    async def check_answer(self, user_answer):
        room = await self.get_room()
        question = await self.get_current_question(room)
        
        if not question:
            return
        
        is_correct = user_answer.strip().lower() == question.correct_answer.strip().lower()
        
        if is_correct:
    
            player = await sync_to_async(Player.objects.get)(user=self.user)
            player.score += 10
            await sync_to_async(player.save)()
            
        
            scores = await self.get_all_players_and_scores()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'score_update',
                    'scores': scores
                }
            )

        
        room.current_question_index += 1
        await sync_to_async(room.save)()
        await self.send_question_to_all(room)
        
    async def end_game(self):
        room = await self.get_room()
        room.is_game_started = False
        await sync_to_async(room.save)()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_over',
                'message': 'Oyun bitti!'
            }
        )

    
    @sync_to_async
    def add_player_to_room(self):
        room, _ = Room.objects.get_or_create(name=self.room_name)
        player, _ = Player.objects.get_or_create(user=self.user)
        player.room = room
        player.save()
        
    @sync_to_async
    def remove_player_from_room(self):
        try:
            player = Player.objects.get(user=self.user)
            player.room = None
            player.save()
        except Player.DoesNotExist:
            pass
        
    @sync_to_async
    def get_player_count(self):
        try:
            room = Room.objects.get(name=self.room_name)
            return Player.objects.filter(room=room).count()
        except Room.DoesNotExist:
            return 0
        


    async def end_game(self):
        room = await self.get_room()
        room.is_game_started = False
        await sync_to_async(room.save)()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_over',
                'message': 'Oyun bitti!'
            }
        )
    
    
    async def game_over(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'game_over',
            'message': message
        }))

