from channels.generic.websocket import AsyncWebsocketConsumer
import json

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({
            'message': 'WebSocket bağlantısı başarılı!'
        }))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        
        await self.send(text_data=json.dumps({
            'message': f"Mesaj alındı: {data}"
        }))
