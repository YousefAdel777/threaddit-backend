from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
import pytest
from chats.serializers import (
    ChatReadSerializer, 
    ChatWriteSerializer, 
    MessageReadSerializer, 
    MessageWriteSerializer,
    MarkAsReadSerializer
)
from .factories import (
    UserFactory,
    MessageFactory,
    ChatFactory,
    BlockFactory
)

@pytest.fixture
def serializer_context():
    user = UserFactory()
    request = APIRequestFactory().get('/')
    request.user = user
    return {'request': request}

@pytest.mark.django_db
class TestChatReadSerializer:
    def test_chat_serializer_fields(self, serializer_context):
        user = serializer_context['request'].user
        user2 = UserFactory()
        chat = ChatFactory(participants=[user, user2])
        message = MessageFactory(chat=chat, user=user2)
        serializer = ChatReadSerializer(chat, context=serializer_context)
        assert serializer.data['id'] == chat.id
        assert serializer.data['participants'][0]['id'] == user.id
        assert serializer.data['participants'][1]['id'] == user2.id
        assert serializer.data['created_at'] is not None
        assert serializer.data['last_message']['content'] == message.content
        assert serializer.data['other_participant']['id'] == chat.get_other_participant(user).id
        assert serializer.data['unread_messages_count'] == 1

    def test_blocked_other_participant(self, serializer_context):
        user = serializer_context['request'].user
        user2 = UserFactory()
        chat = ChatFactory(participants=[user, user2])
        BlockFactory(blocked_by=user, blocked_user=user2)
        serializer_data = ChatReadSerializer(chat, context=serializer_context).data
        assert serializer_data['other_participant'] is None

@pytest.mark.django_db
class TestChatWriteSerializer:
    def test_valid_chat_write_serializer(self, serializer_context):
        user = serializer_context['request'].user
        user2 = UserFactory()
        data = {
            "participants": [user.id, user2.id]
        }
        serializer = ChatWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid()
        chat = serializer.save()
        assert list(chat.participants.all()) == [user, user2]
        assert chat.created_at is not None
        assert chat.last_message is None
        assert chat.get_unread_messages_count(user) == 0

    def test_chat_invalid_participants_count_write_serializer(self, serializer_context):
        user = serializer_context['request'].user
        data = {
            "participants": [user.id]
        }
        serializer = ChatWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid() is False
        assert serializer.errors == {'participants': ['Chat must have 2 participants']}

    def test_same_user_participants_chat_write_serializer(self, serializer_context):
        user = serializer_context['request'].user
        data = {
            "participants": [user.id, user.id]
        }
        serializer = ChatWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid() is False
        assert serializer.errors == {'participants': ['Chat must have 2 different participants']}

    def test_non_current_user_participants_chat_write_serializer(self, serializer_context):
        user = UserFactory()
        user2 = UserFactory()
        data = {
            "participants": [user.id, user2.id]
        }
        serializer = ChatWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid() is False
        assert serializer.errors == {'participants': ['Chat must have one of the participants as the current user']}

    def test_duplicate_chat_write_serializer(self, serializer_context):
        user = serializer_context['request'].user
        user2 = UserFactory()
        chat = ChatFactory(participants=[user, user2])
        data = {
            "participants": [user.id, user2.id]
        }
        serializer = ChatWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid() is False
        assert serializer.errors == {'participants': ['Chat already exists']}

@pytest.mark.django_db
class TestMessageReadSerializer:
    def test_message_read_serializer_fields(self, serializer_context):
        user = serializer_context['request'].user
        user2 = UserFactory()
        chat = ChatFactory(participants=[user, user2])
        message = MessageFactory(chat=chat, user=user2)
        serializer = MessageReadSerializer(message, context=serializer_context)
        assert serializer.data['id'] == message.id
        assert serializer.data['user']['id'] == user2.id
        assert serializer.data['content'] == message.content
        assert serializer.data['chat'] == chat.id
        assert serializer.data['created_at'] is not None

@pytest.mark.django_db
class TestMessageWriteSerializer:
    def test_valid_message_write_serializer(self, serializer_context):
        user = serializer_context['request'].user
        user2 = UserFactory()
        chat = ChatFactory(participants=[user, user2])
        data = {
            "chat": chat.id,
            "user": user2.id,
            "content": "test_content"
        }
        serializer = MessageWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid()
        message = serializer.save()
        assert message.chat == chat
        assert message.content == "test_content"
        assert message.created_at is not None
        assert message.is_read == False
        assert message.user == user2

    def test_message_non_existing_chat(self, serializer_context):        
        user = serializer_context['request'].user
        user2 = UserFactory()
        data = {
            "chat": user.id,
            "user": user2.id,
            "content": "test_content"
        }
        serializer = MessageWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid() is False
        assert 'chat' in serializer.errors

@pytest.mark.django_db
class TestMarkAsReadSerializer:
    def test_mark_as_read_serializer_with_valid_chat(self, serializer_context):
        user = serializer_context['request'].user
        user2 = UserFactory()
        chat = ChatFactory(participants=[user, user2])
        data = {
            "chat": chat.id,
        }
        serializer = MarkAsReadSerializer(data=data, context=serializer_context)
        assert serializer.is_valid()
