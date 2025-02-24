from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import sync_to_async
from .models import Chat
from django.db.models import Q
from accounts.services import BlockService
import json
from urllib.parse import parse_qs

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.group_name = f"user_chats_{self.user.id}"
        self.chats = await sync_to_async(list)(Chat.objects.filter(participants=self.user.id))

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
    
    async def send_chats(self, event):
        chats = event['chats']
        await self.send(text_data=json.dumps({'type': 'send_chats', 'chats': chats}))

    async def update_chat(self, event):
        chat = event['chat']
        await self.send(text_data=json.dumps({'type': 'update_chats', 'chat': chat}))

class MessagesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.participant = parse_qs(self.scope['query_string'].decode('utf-8'))['participant'][0]
        if not self.user.is_authenticated or not self.participant:
            await self.close()
            return
        self.chat = await sync_to_async(Chat.objects.filter(participants=self.user).filter(participants__id=self.participant).first)()
        self.is_blocked = await sync_to_async(BlockService.is_blocked)(self.participant, self.user)
        if not self.chat or self.is_blocked:
            await self.close()
            return
        
        self.group_name = f"chat_{self.chat.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'type': 'send_message', 'message': message}))
    
    async def delete_message(self, event):
        message_id = event['message_id']
        await self.send(text_data=json.dumps({'type': 'delete_message', 'message_id': message_id}))

    async def update_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'type': 'update_message', 'message': message}))

    async def mark_as_read(self, event):
        messages_ids = event['messages_ids']
        await self.send(text_data=json.dumps({'type': 'mark_as_read', 'messages_ids': messages_ids}))