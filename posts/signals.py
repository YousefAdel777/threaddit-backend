from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.core.cache import cache
from .models import Post, PostInteraction, SavedPost, PostReport
from .tasks import check_nsfw_post

@receiver(post_save, sender=Post)
def check_post_nsfw_status(sender, instance, created, **kwargs):
    check_nsfw_post.delay(instance.id)

@receiver([post_save, post_delete], sender=PostInteraction)
def invalidate_post_interaction_cache(sender, instance, created, **kwargs):
    cache.delete_pattern(f"*post_interaction_list_{instance.user.id}*")
    cache.delete_pattern(f"*post_interaction_detail_{instance.id}*")
    cache.delete_pattern(f"*post_list_{instance.user.id}*")
    cache.delete_pattern(f"*post_list_{instance.post.user.id}*")
    cache.delete_pattern(f"*post_detail_{instance.post.user.id}*")
    cache.delete_pattern(f"*post_detail_{instance.user.id}*")
    cache.delete_pattern(f"*user_saved_post_list_{instance.user.id}*")
    cache.delete_pattern(f"*user_upvoted_post_list_{instance.user.id}*")
    cache.delete_pattern(f"*user_downvoted_post_list_{instance.user.id}*")

@receiver([post_save, post_delete], sender=Post)
def invalidate_post_cache(sender, instance, created, **kwargs):
    cache.delete_pattern(f"*post_list*")
    cache.delete_pattern(f"*user_saved_post_list_{instance.user.id}*")
    cache.delete_pattern(f"*user_upvoted_post_list_{instance.user.id}*")
    cache.delete_pattern(f"*user_downvoted_post_list_{instance.user.id}*")

@receiver([post_save, post_delete], sender=SavedPost)
def invalidate_saved_post_cache(sender, instance, created, **kwargs):
    cache.delete_pattern(f"*user_saved_post_list_{instance.user.id}*")
    cache.delete_pattern(f"*saved_post_list_{instance.user.id}*")
    cache.delete_pattern(f"*saved_post_detail_{instance.user.id}*")
    cache.delete_pattern(f"*post_list_{instance.post.user.id}*")
    cache.delete_pattern(f"*post_detail_{instance.post.user.id}*")
    cache.delete_pattern(f"*user_saved_post_list_{instance.user.id}*")
    cache.delete_pattern(f"*user_upvoted_post_list_{instance.user.id}*")
    cache.delete_pattern(f"*user_downvoted_post_list_{instance.user.id}*")

@receiver([post_save, post_delete], sender=PostReport)
def invalidate_post_report_cache(sender, instance, created, **kwargs):
    cache.delete_pattern(f"*post_report_list_{instance.user.id}*")
    cache.delete_pattern(f"*post_report_detail_{instance.user.id}*")
    cache.delete_pattern(f"*post_list_{instance.post.user.id}*")
    cache.delete_pattern(f"*post_detail_{instance.post.user.id}*")
    cache.delete_pattern(f"*user_saved_post_list_{instance.user.id}*")
    cache.delete_pattern(f"*user_upvoted_post_list_{instance.user.id}*")
    cache.delete_pattern(f"*user_downvoted_post_list_{instance.user.id}*")