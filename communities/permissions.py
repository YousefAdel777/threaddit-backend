from rest_framework.permissions import SAFE_METHODS, BasePermission
from .services import BanService, MemberService
from posts.models import Post, PostInteraction
from comments.models import Comment, CommentInteraction

class CanModerate(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        community_id = request.data.get('community')
        if not community_id:
            return True
        return MemberService.is_moderator(request.user.id, community_id)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if isinstance(obj, Post):
            if not obj.community:
                return False
            return MemberService.is_moderator(request.user.id, obj.community.id)
        if isinstance(obj, Comment):
            if not obj.post.community:
                return False
            return MemberService.is_moderator(request.user.id, obj.post.community.id)
        return MemberService.is_moderator(request.user.id, obj.id)

class IsNotBanned(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        community_id = request.data.get('community')
        if not community_id:
            return True
        return not BanService.is_banned(request.user, community_id)

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user

class CanBan(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user_id = request.data.get('user')
        community_id = request.data.get('community')
        if not user_id or not community_id:
            return True
        is_moderator = MemberService.is_moderator(user_id, community_id)
        if is_moderator:
            return False
        return True