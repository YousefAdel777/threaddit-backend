from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import sync_to_async

online_members = {}

class CommunityConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from .models import Member

        self.user = self.scope['user']
        self.community_id = self.scope['url_route']['kwargs']['id']
        self.group_name = f"community_{self.community_id}"
        
        if self.user.is_authenticated:
            is_member = await sync_to_async(
                lambda: Member.objects.filter(user=self.user, community_id=self.community_id).exists()
            )()
            if is_member:
                if self.community_id not in online_members:
                    online_members[self.community_id] = set()
                online_members[self.community_id].add(self.user.id)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'update_online_members_count',
                'online_members_count': len(online_members.get(self.community_id, []))
            }
        )

    async def disconnect(self, code):
        if self.community_id in online_members:
            online_members[self.community_id].discard(self.user.id)
            if not online_members[self.community_id]:
                del online_members[self.community_id]

        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'update_online_members_count',
                'members': len(online_members.get(self.community_id, [])),
            }
        )

    async def update_online_members_count(self, event):
        online_members_count = event['online_members_count']
        await self.send(text_data=json.dumps({
            'type': 'online_members_count',
            'online_members_count': online_members_count
        }))


# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.exceptions import DenyConnection
# import json
# from urllib.parse import parse_qs
# from django.apps import apps

# online_members = {}

# class CommunityConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         print(self.scope)
#         query_params = parse_qs(self.scope['query_string'].decode())
#         token = query_params.get('token', [None])[0]
#         # print(token)
#         if token:
#             # try:
#                 # validated_data = None
#             validated_data = await self.validate_token(token)
#             self.scope['user'] = validated_data
#             # except InvalidToken:
#             # except:
#             #     self.close()
#             #     raise DenyConnection("Invalid token")
#         print(token)

#         self.user = self.scope.get('user')
#         print(self.user)
#         self.community_id = self.scope['url_route']['kwargs']['id']
#         self.group_name = f"community_{self.community_id}"
        
#         if self.user:
#             if self.community_id not in online_members:
#                 online_members[self.community_id] = set()
#             online_members[self.community_id].add(self.user['user_id'])

#         await self.channel_layer.group_add(self.group_name, self.channel_name)
#         await self.accept()

#         await self.channel_layer.group_send(
#             self.group_name,
#             {
#                 'type': 'update_online_members_count',
#                 'online_members_count': len(online_members.get(self.community_id, []))
#             }
#         )

#     async def disconnect(self, code):
#         if self.community_id in online_members:
#             online_members[self.community_id].discard(self.user['user_id'])
#             if not online_members[self.community_id]:
#                 del online_members[self.community_id]

#         await self.channel_layer.group_discard(self.group_name, self.channel_name)
#         await self.channel_layer.group_send(
#             self.group_name,
#             {
#                 'type': 'update_online_members_count',
#                 'members': len(online_members.get(self.community_id, [])),
#             }
#         )

#     async def update_online_members_count(self, event):
#         online_members_count = event['online_members_count']
#         await self.send(text_data=json.dumps({
#             'type': 'online_members_count',
#             'online_members_count': online_members_count
#         }))

#     async def validate_token(self, token):
#         from rest_framework_simplejwt.exceptions import InvalidToken
#         from rest_framework_simplejwt.backends import TokenBackend
#         from django.conf import settings
#         try:
#             token_backend = TokenBackend(algorithm="HS256", signing_key=settings.SECRET_KEY)
#             return token_backend.decode(token=token, verify=True)
#         except InvalidToken as e:
#             raise InvalidToken("Token validation failed") from e
