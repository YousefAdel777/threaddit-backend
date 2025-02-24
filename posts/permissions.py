from rest_framework.permissions import BasePermission, SAFE_METHODS
from .services import PostService
from communities.services import BanService, MemberService

class CanPost(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            community_id = request.data.get('community')
            if not community_id:
                return True
            return not BanService.is_banned(request.user, community_id)
        return True

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
        if request.method == 'DELETE':
            return False
        return MemberService.is_moderator(request.user.id, obj.community.id)

class CanCrossPost(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            original_post_id = request.data.get('original_post')
            if not original_post_id:
                return True
            original_post = PostService.get_post(original_post_id, request.user)
            if not original_post:
                return False 
        return True

class IsAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user == obj.user

class CanInteract(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        post_id = request.data.get('post')
        if not post_id:
            return True
        post = PostService.get_post(post_id, request.user)
        if not post:
            return False
        return True
