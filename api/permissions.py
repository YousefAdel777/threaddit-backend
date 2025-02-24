from rest_framework.permissions import BasePermission, SAFE_METHODS
from posts.models import Post
from communities.models import Community

class IsNotBanned(BasePermission):
    pass

class IsModerator(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_moderator

class IsModeratorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        community_id = request.data.get('community')
        post_id = request.data.get('post')
        if request.method in SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            return False
        if community_id:
            return Community.objects.filter(id=community_id, members__user=request.user, members__is_moderator=True).exists()
        if post_id:
            return Post.objects.filter(id=post_id, community__members__user=request.user, community__members__is_moderator=True).exists()
        return True
    
    def has_object_permission(self, request, view, obj): 
        print("asdasdasd")      
        if request.method in SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            return False
        if hasattr(obj, 'members'):
            return obj.members.filter(user=request.user, is_moderator=True).exists()
        if hasattr(obj, 'community'):
            return obj.community.members.filter(user=request.user, is_moderator=True).exists()
        if hasattr(obj, 'member'):
            return obj.member.community.members.filter(user=request.user, is_moderator=True).exists()
        return False

class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.user

    def has_permission(self, request, view):
        return True