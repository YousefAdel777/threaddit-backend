from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied
from accounts.services import BlockService, UserService
from .models import Chat

class CanSendMessage(BasePermission):
    def has_permission(self, request, view):
        if request.method != 'POST':
            return True
        chat_id = request.data.get('chat')
        if not chat_id:
            return False
        chat = Chat.objects.filter(id=chat_id, participants=request.user).first()
        if not chat:
            return False
        other_participant = chat.get_other_participant(request.user)
        return other_participant is not None

class IsSender(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user == obj.user

class CanStartChat(BasePermission):
    def has_permission(self, request, view):
        if request.method != 'POST':
            return True
        participants_ids = request.data.getlist('participants')
        if not participants_ids:
            return False
        if len(participants_ids) != 2:
            return False
        other_participant_id = participants_ids[0] if participants_ids[0] != str(request.user.id) else participants_ids[1]
        other_participant = UserService.get_user(other_participant_id, request.user)
        return other_participant is not None