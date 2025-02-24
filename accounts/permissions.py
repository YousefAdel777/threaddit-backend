from rest_framework.permissions import SAFE_METHODS, BasePermission

from .services import BlockService

class CanFollow(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            followed = request.data.get('followed')
            if followed:
                is_blocked = BlockService.is_blocked(followed, request.user)
                return not is_blocked
            return False
        return True