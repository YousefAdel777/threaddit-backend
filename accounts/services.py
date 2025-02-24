from django.contrib.auth import get_user_model
from .models import Follow, Block
from django.db.models import Q

User = get_user_model()

class UserService:
    @classmethod
    def get_users(cls, user):
        users = User.objects.all()
        users = cls._exclude_blocked(users, user)
        return cls._optimize_users_queryset(users)
    
    @classmethod
    def get_user(cls, user_id, user):
        users = User.objects.filter(id=user_id)
        users = cls._exclude_blocked(users, user)
        return cls._optimize_users_queryset(users).first()
    
    @classmethod
    def _exclude_blocked(cls, users, user):
        if user.is_authenticated:
            users = users.exclude(blocked_by__blocked_by=user).exclude(blocks__blocked_user=user)
        return users

    @classmethod
    def _optimize_users_queryset(cls, users):
        return users.prefetch_related('blocks', 'blocked_by', 'followers', 'following', 'saved_posts')

    @classmethod
    def get_blocked_users(cls, user):
        blocked_users = User.objects.filter(blocked_by__blocked_by=user)
        return cls._optimize_users_queryset(blocked_users)

    @classmethod
    def get_followed_users(cls, user):
        followed_users = User.objects.filter(followers__follower=user)
        followed_users = cls._exclude_blocked(followed_users, user)
        return cls._optimize_users_queryset(followed_users)

class BlockService:
    @staticmethod
    def get_blocks(user):
        return Block.objects.filter(blocked_by=user)
    
    @staticmethod
    def block_user(user, blocked_user):
        follow_id = blocked_user.get_follow_id(user)
        if follow_id:
            Follow.objects.get(id=follow_id).delete()
        follow_id = user.get_follow_id(blocked_user)
        if follow_id:
            Follow.objects.get(id=follow_id).delete()
        Block.objects.create(blocked_by=user, blocked_user=blocked_user)

    @staticmethod
    def is_blocked(user, blocked_user):
        return Block.objects.filter(Q(blocked_by=user, blocked_user=blocked_user) | Q(blocked_by=blocked_user, blocked_user=user)).exists()

class FollowService:
    @staticmethod
    def get_follows(user):
        return Follow.objects.filter(follower=user)