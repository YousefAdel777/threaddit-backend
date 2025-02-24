from .models import Chat, Message
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from rest_framework import serializers
from accounts.serializers import CustomUserSerializer
from accounts.services import UserService
from .services import ChatService

User = get_user_model()

class MessageWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=serializers.CurrentUserDefault())
    chat = serializers.PrimaryKeyRelatedField(queryset=Chat.objects.all())
    class Meta:
        model = Message
        fields = ['chat', 'content', 'user']

class MessageReadSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    class Meta:
        model = Message
        fields = '__all__'

class MarkAsReadSerializer(serializers.Serializer):
    chat = serializers.PrimaryKeyRelatedField(queryset=Chat.objects.all())

class ChatReadSerializer(serializers.ModelSerializer):
    participants = CustomUserSerializer(many=True)
    last_message = MessageReadSerializer()
    unread_messages_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'last_message', 'unread_messages_count', 'created_at', 'other_participant', 'participants']

    def get_unread_messages_count(self, obj):
        request = self.context.get("request")
        return obj.get_unread_messages_count(request.user) if request is not None else 0
    
    def get_other_participant(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        other_participant = obj.get_other_participant(request.user)
        return CustomUserSerializer(other_participant).data if other_participant is not None else None

class ChatWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ['participants']

    def validate(self, attrs):
        instance = self.instance
        if instance and 'participants' in attrs:
            raise serializers.ValidationError("Participants cannot be updated")
        return attrs

    def validate_participants(self, participants):
        user = self.context.get('request').user
        if len(participants) != 2:
            raise serializers.ValidationError('Chat must have 2 participants')
        if participants[0] == participants[1]:
            raise serializers.ValidationError('Chat must have 2 different participants')
        participants_ids = sorted([participant.id for participant in participants])
        if user.id not in participants_ids:
            raise serializers.ValidationError('Chat must have one of the participants as the current user')
        self._validate_chat_does_not_exist(participants)
        return participants
    
    def _validate_chat_does_not_exist(self, participants):
        participant_ids = [participant.id for participant in participants]
        if Chat.objects.annotate(participants_count=Count('participants', filter=Q(participants__id__in=participant_ids))).filter(participants_count=2).exists():
            raise serializers.ValidationError('Chat already exists')