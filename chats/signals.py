from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Message
from .tasks import send_message_task, delete_message_task
from django.db import transaction
# @receiver(post_save, sender=Message)
# def send_message(sender, instance, created, **kwargs):
#     channel_layer = get_channel_layer()
#     print(instance)
#     message_serializer = MessageReadSerializer(instance)
#     chat_serializer = ChatReadSerializer(instance.chat)
#     if created:
#         async_to_sync(channel_layer.group_send)(
#             f"chat_{instance.chat.id}",
#             {
#                 "type": "send_message",
#                 "message": message_serializer.data
#             }
#         )
#     else:
#         async_to_sync(channel_layer.group_send)(
#             f"chat_{instance.chat.id}",
#             {
#                 "type": "update_message",
#                 "message": message_serializer.data
#             }
#         )
#     async_to_sync(channel_layer.group_send)(
#         f"user_chats_{instance.user.id}",
#         {
#             "type": "update_chat",
#             "chat": chat_serializer.data
#         }
#     )

@receiver(post_save, sender=Message)
def send_message(sender, instance, created, **kwargs):
    # channel_layer = get_channel_layer()
    # print(instance)
    if created:
        transaction.on_commit(lambda: send_message_task.delay(instance.id))
        # send_message_task.delay(instance)
    # if created:
    #     async_to_sync(channel_layer.group_send)(
    #         f"chat_{instance.chat.id}",
    #         {
    #             "type": "send_message",
    #             "message": message_serializer.data
    #         }
    #     )
    # else:
    #     async_to_sync(channel_layer.group_send)(
    #         f"chat_{instance.chat.id}",
    #         {
    #             "type": "update_message",
    #             "message": message_serializer.data
    #         }
    #     )
    # async_to_sync(channel_layer.group_send)(
    #     f"user_chats_{instance.user.id}",
    #     {
    #         "type": "update_chat",
    #         "chat": chat_serializer.data
    #     }
    # )

@receiver(post_delete, sender=Message)
def delete_message(sender, instance, **kwargs):
    transaction.on_commit(lambda: delete_message_task.delay(instance.id, instance.chat.id))


# def message_save(sender, instance, **kwargs):

# from django.db.models.signals import post_save, post_delete
# from django.contrib.contenttypes.models import ContentType
# from django.dispatch import receiver
# from .models import Notification
# from .serializers import NotificationSerializer
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync

# @receiver(post_save, sender=Notification)
# def send_notification(sender, instance, created, **kwargs):
#     if not created:
#         return
#     channel_layer = get_channel_layer()
#     serializer = NotificationSerializer(instance)
#     async_to_sync(channel_layer.group_send)(
#         f"user_notifications_{instance.user.id}",
#         {
#             'type': 'send_notification',
#             'notification': serializer.data
#         }
#     )

# @receiver(post_delete)
# def cascade_generic_relation(sender, instance, **kwargs):
#     content_type = ContentType.objects.get_for_model(sender)
#     Notification.objects.filter(
#         content_type=content_type,
#         object_id=instance.id
#     ).delete()
