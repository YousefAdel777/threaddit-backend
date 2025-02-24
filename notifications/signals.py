from django.db.models.signals import post_save, post_delete
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from .models import Notification
from .serializers import NotificationSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=Notification)
def send_notification(sender, instance, created, **kwargs):
    if not created:
        return
    channel_layer = get_channel_layer()
    serializer = NotificationSerializer(instance)
    async_to_sync(channel_layer.group_send)(
        f"user_notifications_{instance.user.id}",
        {
            'type': 'send_notification',
            'notification': serializer.data
        }
    )

@receiver(post_delete)
def cascade_generic_relation(sender, instance, **kwargs):
    if hasattr(instance, 'id'):
        content_type = ContentType.objects.get_for_model(sender)
        Notification.objects.filter(
            content_type=content_type,
            object_id=instance.id
        ).delete()
