from django.db import models
from django.core.exceptions import ValidationError
from communities.models import Community, Rule
from django.contrib.auth import get_user_model

User = get_user_model()

class Post(models.Model):
    POST_STATUS = [
        ('pending', 'Pending'), 
        ('accepted', 'Accepted'), 
        ('removed', 'Removed')
    ]

    POST_TYPES = [
        ('text', 'Text'), 
        ('media', 'Media'), 
        ('link', 'Link'), 
        ('poll', 'Poll'),
        ('crosspost', 'Crosspost')
    ]

    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', db_index=True)
    status = models.CharField(max_length=10, choices=POST_STATUS, default='pending', db_index=True)
    content = models.TextField(blank=True, default='')
    type = models.CharField(max_length=10, choices=POST_TYPES)
    link = models.URLField(max_length=255, blank=True, default='')
    original_post = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, default=None, related_name='crossposts')
    community = models.ForeignKey(Community, on_delete=models.CASCADE, null=True, blank=True, default=None, db_index=True, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_spoiler = models.BooleanField(default=False)
    is_nsfw = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    
    def clean(self):
        super().clean()
        if self.type == 'text' and not self.content:
            raise ValidationError({'content': 'Text posts must have content.'})

        if self.type == 'link' and not self.link:
            raise ValidationError({'link': 'Link posts must have a URL.'})

        if self.type == 'crosspost' and not self.original_post:
            raise ValidationError({'original_post': 'Crossposts must reference an original post.'})

        if self.type in ['text', 'poll', 'crosspost'] and self.link:
            raise ValidationError({'link': 'Text, poll, and crosspost types should not have a link.'})
        
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
    
    @property
    def comments_count(self):
        return self.comments.count()
    
    def get_user_interaction(self, user):
        if user.is_authenticated:
            return self.post_interactions.filter(user=user).first()
        return None
    
    def get_is_reported(self, user):
        if user.is_authenticated:
            return self.post_reports.filter(user=user, status='pending').exists()
        return False
    
    def get_saved_post_id(self, user):
        if user.is_authenticated:
            saved_post = SavedPost.objects.filter(user=user, post=self).first()
            return saved_post.id if saved_post else None
        return None

class SavedPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True, related_name='saved_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, db_index=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"Saved Post: {self.post.title} by {self.user.username}"

class PostReport(models.Model):
    REPORT_STATUS = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
    ]

    status = models.CharField(max_length=10, choices=REPORT_STATUS, default='pending')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_post_reports', db_index=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_reports', db_index=True)
    violated_rule = models.ForeignKey(Rule, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post Report: {self.post.title} by {self.user.username}"

class Attachment(models.Model):
    FILE_TYPES = [
        ('image', 'Image'), 
        ('video', 'Video')
    ]

    file = models.FileField(upload_to='attachments')
    file_type = models.CharField(max_length=255, choices=FILE_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='attachments')
    def __str__(self):
        return f"Attachment: {self.file.name} for {self.post.title}"

class PostInteraction(models.Model):
    INTERACTION_TYPES = [
        ('upvote', 'Upvote'), 
        ('downvote', 'Downvote')
    ]

    interaction_type = models.CharField(max_length=255, choices=INTERACTION_TYPES, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_interactions')

    class Meta:
        unique_together = ('user', 'post')
    
    def __str__(self):
        return f"{self.interaction_type} by {self.user.username} on {self.post.title}"

# class CommunityPinnedPost(models.Model):
#     post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='')
#     community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='community_pinned_posts')

# class UserPinnedPost(models.Model):
#     post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='')
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_pinned_posts')