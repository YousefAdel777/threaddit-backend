from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comment
from notifications.models import Notification
from django.contrib.contenttypes.models import ContentType

@receiver(post_save, sender=Comment)
def send_comment_notification(sender, instance, created, **kwargs):
    if not created:
        return
    content_type = ContentType.objects.get_for_model(instance)
    if instance.parent:
        if instance.parent.user == instance.user:
            return
        Notification.objects.create(    
            message=f"u/{instance.user.username} replied to your comment.", 
            user=instance.parent.user,
            object_id=instance.parent.id,
            content_type=content_type
        )
    else:
        if instance.post.user == instance.user:
            return
        Notification.objects.create(
            message=f"u/{instance.user.username} commented on your post.", 
            user=instance.post.user,
            object_id=instance.id,
            content_type=content_type
        )