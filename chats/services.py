import copy
from .models import Message, Chat
from django.db.models.query import Q
from django.db import transaction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class ChatService:
    @classmethod
    def get_chats(cls, user):
        chats = Chat.objects.filter(participants=user)
        return cls._optimize_chat_queryset(chats)
    
    @classmethod
    def _optimize_chat_queryset(cls, chats):
        return chats.prefetch_related('messages', 'participants')

class MessageService:
    @classmethod
    def get_messages(cls, user):
        return Message.objects.filter(chat__participants=user)
    
    @staticmethod
    def mark_as_read(chat_id, user):
        Message.objects.filter(~Q(user=user), chat__id=chat_id, is_read=False).update(is_read=True)

    @staticmethod
    def notify_read_messages(chat_id, user):
        messages_ids = list(Message.objects.filter(~Q(user=user), chat__id=chat_id, is_read=False).values_list("id", flat=True))
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_id}",
            {
                "type": "mark_as_read",
                "messages_ids": messages_ids
            }
        )
