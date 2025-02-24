from celery import shared_task
from django.core.cache import cache
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Chat, Message
from .serializers import MessageReadSerializer


@shared_task
def send_message_task(message_id):
    message = Message.objects.get(id=message_id)
    message_data = MessageReadSerializer(message).data
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{message_data['chat']}",
        {
            "type": "send_message",
            "message": message_data
        }
    )
    # async_to_sync(channel_layer.group_send)(
    #     f"user_chats_{message_data['user']['id']}",
    #     {
    #         "type": "update_chat",
    #         "chat": chat_data
    #     }
    # )
    # async_to_sync(channel_layer.group_send)(
    #     f"user_chats_{chat_data['other_participant']['id']}",
    #     {
    #         "type": "update_chat",
    #         "chat": chat_data
    #     }
    # )

@shared_task
def delete_message_task(message_id, chat_id):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{chat_id}",
        {
            "type": "delete_message",
            "message_id": message_id
        }
    )

@shared_task
def mark_as_read_task(chat_id, user_id):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{user_id}",
        {
            "type": "mark_as_read",
            "messages_ids": chat_id
        }
    )