from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.contrib.contenttypes.models import ContentType
from notifications.models import Notification
from .models import Follow, Block
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()

@receiver(post_save, sender=Follow)
def send_follow_notification(sender, instance, created, **kwargs):
    if not created:
        return
    content_type = ContentType.objects.get_for_model(instance)
    Notification.objects.create(
        user=instance.followed, 
        content_type=content_type,
        object_id=instance.id, 
        message=f"u/{instance.follower.username} followed you."
    )
    # channel_layer = get_channel_layer()
    # notification = Notification.objects.create(user=instance.followed, message=f"u/{instance.user.username} followed you.")
    # serializer = NotificationSerializer(notification)
    # async_to_sync(channel_layer.group_send)(
    #     f"user_notifications_{notification.user.id}",
    #     {
    #         'type': 'send_notification',
    #         'notification': serializer.data
    #     }
    # )

@receiver([post_save, post_delete], sender=User)
def invalidate_user_cache(sender, instance, **kwargs):
    cache.delete_pattern("*user_list*")
    cache.delete(f"user_{instance.id}")

@receiver([post_save, post_delete], sender=Follow)
def invalidate_follow_cache(sender, instance, **kwargs):
    cache.delete_pattern("*user_list*")
    cache.delete(f"user_{instance.followed.id}")

@receiver([post_save, post_delete], sender=Block)
def invalidate_block_cache(sender, instance, **kwargs):    
    cache.delete_pattern("*user_list*")
    cache.delete_many([f"user_{instance.blocked_user.id}", f"user_{instance.blocked_by.id}"])
