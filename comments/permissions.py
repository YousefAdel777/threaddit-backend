from rest_framework.permissions import BasePermission, SAFE_METHODS
from posts.services import PostService
from .services import CommentService

class CanComment(BasePermission):
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

class IsAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user == obj.user

class CanInteract(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        comment_id = request.data.get('comment')
        if not comment_id:
            return True
        comment = CommentService.get_comment(comment_id, request.user)
        if not comment:
            return False
        return True