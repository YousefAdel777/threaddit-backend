from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
User = get_user_model()

class Topic(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name

class Community(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    banner = models.ImageField(upload_to='banners', blank=True, null=True)
    icon = models.ImageField(upload_to='icons', blank=True, null=True)
    topics = models.ManyToManyField(Topic, related_name='topics')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    def get_favorite_id(self, user):
        if not user.is_authenticated:
            return None
        favorite = self.favorites.filter(user=user).first()
        return favorite.id if favorite else None

    def get_member_id(self, user):
        if not user.is_authenticated:
            return None
        member = self.members.filter(user=user).first()
        return member.id if member else None
    
    def get_is_moderator(self, user):
        if not user.is_authenticated:
            return False
        return self.members.filter(is_moderator=True, user=user).exists()

    @property
    def moderators(self):
        return self.members.filter(is_moderator=True)
    
    @property
    def members_count(self):
        return self.members.count()

class Rule(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='rules')

    def __str__(self):        
        return f"{self.title} for {self.community.name}"

class Member(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='members', db_index=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_moderator = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'community')

    @property
    def ban(self):
        community_bans = self.user.bans.filter(community=self.community)
        return community_bans.filter(Q(is_permanent=True) | Q(expires_at__gt=timezone.now())).first()
    
    @property
    def is_creator(self):
        return self.community.user == self.user

    def __str__(self):
        return f"{self.user.username} in {self.community.name}"

class Ban(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bans', db_index=True)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='community_bans', db_index=True)
    reason = models.TextField()
    banned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, default=None, db_index=True)
    is_permanent = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        if self.is_permanent and self.expires_at:
            raise ValidationError("Permanent ban cannot have an expiration date.")
        if not self.is_permanent and not self.expires_at:
            raise ValidationError("Non-permanent ban must have an expiration date.")
        if self.expires_at:
            if timezone.is_naive(self.expires_at):
                self.expires_at = timezone.make_aware(self.expires_at)
            if self.expires_at < timezone.now():
                raise ValidationError("Ban expiration date cannot be in the past.")
        active_bans = self.user.bans.filter(community=self.community).filter(Q(is_permanent=True) | Q(expires_at__gt=timezone.now()))
        if self.pk:
            active_bans = active_bans.exclude(pk=self.pk)
        if active_bans.exists():
            raise ValidationError("User already has an active ban in this community.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ban on {self.user.username} - {'Permanent' if self.is_permanent else f'Until {self.expires_at}'}"
    
    @property
    def is_active(self):
        if self.is_permanent:
            return True
        return self.expires_at and self.expires_at > timezone.now()

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='favorites')

    class Meta:
        unique_together = ('user', 'community')

    def __str__(self):
        return f"{self.user.username} favorited {self.community.name}"