from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager

class CustomUser(AbstractUser):
    username = models.CharField(max_length=255, unique=False)
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    bio = models.TextField(default='')
    image = models.ImageField(upload_to='profile_images', blank=True, null=True)
    post_karma = models.IntegerField(default=0)
    comment_karma = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def get_block_id(self, user):
        try:
            return self.blocked_by.get(blocked_by=user).id
        except:
            return None

    def get_follow_id(self, user):
        try:
            return self.followers.get(follower=user).id
        except:
            return None
        
    def update_post_karma(self, amount):
        CustomUser.objects.filter(pk=self.pk).update(post_karma=models.F('post_karma') + amount)

    def update_comment_karma(self, amount):
        CustomUser.objects.filter(pk=self.pk).update(comment_karma=models.F('comment_karma') + amount)
    
    # def update_post_karma(self, amount):
    #     # self.post_karma += amount
    #     self.post_karma = models.F('post_karma') + amount
    #     self.save()
    
    # def update_comment_karma(self, amount):
    #     # self.comment_karma += amount
    #     self.comment_karma = models.F('comment_karma') + amount
    #     self.save()

    @property
    def followers_count(self):
        return self.followers.count()

    def __str__(self):
        return self.username

class Follow(models.Model):
    follower = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='following', db_index=True)
    followed = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='followers', db_index=True)

    class Meta:
        unique_together = ('follower', 'followed')

    def clean(self):
        if self.followed == self.follower:
            raise ValidationError('User cannot follow themselves')
        return super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"

class Block(models.Model):
    blocked_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='blocks', db_index=True)
    blocked_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='blocked_by', db_index=True)

    class Meta:
        unique_together = ('blocked_by', 'blocked_user')

    def clean(self):
        if self.blocked_by == self.blocked_user:
            raise ValidationError('User cannot block themselves')
        return super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.blocked_by.username} blocked {self.blocked_user.username}"

# class UserHighlight(models.Model):
#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_highlights')
#     post = models.ForeignKey('api.Post', on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)