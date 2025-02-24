from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import sync_to_async
from redis import from_url
from django.conf import settings

redis_client = from_url(settings.REDIS_URL, decode_responses=True)

class CommunityConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from .services import MemberService

        self.user = self.scope['user']
        self.community_id = self.scope['url_route']['kwargs']['id']
        self.group_name = f"community_{self.community_id}"
        
        if self.user.is_authenticated:
            is_member = await sync_to_async(MemberService.is_member)(self.user.id, self.community_id)
            if is_member:
                await self.add_online_member()

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'update_online_members_count',
                'online_members_count': await self.get_online_members_count()
            }
        )

    async def disconnect(self, code):
        if self.user.is_authenticated:
            await self.remove_online_member()
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'update_online_members_count',
                'members': await self.get_online_members_count()
            }
        )

    async def add_online_member(self):
        redis_client.sadd(f"community:{self.community_id}:online_members", self.user.id)

    async def remove_online_member(self):
        redis_client.srem(f"community:{self.community_id}:online_members", self.user.id)
        if redis_client.scard(f"community:{self.community_id}:online_members") == 0:
            redis_client.delete(f"community:{self.community_id}:online_members")

    async def get_online_members_count(self):
        return redis_client.scard(f"community:{self.community_id}:online_members")

    async def update_online_members_count(self, event):
        online_members_count = event['online_members_count']
        await self.send(text_data=json.dumps({
            'type': 'online_members_count',
            'online_members_count': online_members_count
        }))
