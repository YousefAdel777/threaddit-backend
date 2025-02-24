from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from posts.models import Post
from communities.models import Rule
User = get_user_model()

class Comment(models.Model):
    COMMENT_STATUS = [
        ('accepted', 'Accepted'), 
        ('removed', 'Removed')
    ]

    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', db_index=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, default=None, related_name='replies', db_index=True)
    status = models.CharField(max_length=255, choices=COMMENT_STATUS, default='accepted')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def get_interaction(self, user):
        if user.is_authenticated:
            return self.comment_interactions.filter(user=user).first()
        return None
    
    def get_is_reported(self, user):
        if user.is_authenticated:
            return self.comment_reports.filter(user=user, status='pending').exists()
        return None
    
    def clean(self):
        if self.parent:
            if self.parent.post != self.post:
                raise ValidationError({'post': 'Parent comment must belong to the same post'})
        return super().clean()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.content} by {self.user.username} on {self.post.title}"

class CommentReport(models.Model):
    REPORT_STATUS = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_comment_reports', db_index=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_reports', db_index=True)
    violated_rule = models.ForeignKey(Rule, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    status = models.CharField(max_length=10, choices=REPORT_STATUS, default='pending')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment Report: {self.id} by {self.user.username}"

class CommentInteraction(models.Model):
    INTERACTION_TYPES = [
        ('upvote', 'Upvote'), 
        ('downvote', 'Downvote')
    ]

    interaction_type = models.CharField(max_length=255, choices=INTERACTION_TYPES, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_interactions')

    def __str__(self):
        return f"{self.interaction_type} by {self.user.username} on {self.comment.content}"

    class Meta:
        unique_together = ('user', 'comment')
