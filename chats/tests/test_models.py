# from django.contrib.auth import get_user_model
import pytest
from .factories import (
    UserFactory,
    ChatFactory,
    MessageFactory,
    BlockFactory
)

@pytest.mark.django_db
class TestChatModel:
    def test_chat_model_creation(self):
        user = UserFactory()
        user2 = UserFactory()
        chat = ChatFactory(participants=[user, user2])
        assert set(chat.participants.all()) == {user, user2}
        assert chat.created_at is not None

    def test_string_representation(self):
        user = UserFactory()
        user2 = UserFactory()
        chat = ChatFactory(participants=[user, user2])
        assert str(chat) == f"Chat {chat.id}"

    def test_last_message_property(self):
        user = UserFactory()
        user2 = UserFactory()
        chat = ChatFactory(participants=[user, user2])
        message = MessageFactory(chat=chat, user=user)
        assert chat.last_message == message
    
    def test_unread_messages_count(self):
        user = UserFactory()
        user2 = UserFactory()
        chat = ChatFactory(participants=[user, user2])
        message = MessageFactory(chat=chat, user=user)
        assert chat.get_unread_messages_count(user) == 0
        assert chat.get_unread_messages_count(user2) == 1
        message.is_read = True
        message.save()
        assert chat.get_unread_messages_count(user2) == 0

    def test_get_other_participant_with_blocked_user(self):
        user = UserFactory()
        user2 = UserFactory()
        chat = ChatFactory(participants=[user, user2])
        BlockFactory(blocked_by=user, blocked_user=user2)
        assert chat.get_other_participant(user) is None
        assert chat.get_other_participant(user2) is None

    def test_get_other_participant(self):
        user = UserFactory()
        user2 = UserFactory()
        chat = ChatFactory(participants=[user, user2])
        assert chat.get_other_participant(user) == user2
        assert chat.get_other_participant(user2) == user

@pytest.mark.django_db
class TestMessageModel:
    def test_message_model_creation(self):
        user = UserFactory()
        user2 = UserFactory()
        chat = ChatFactory(participants=[user, user2])
        message = MessageFactory(chat=chat, user=user, content='test_content')
        assert message.user == user
        assert message.chat == chat
        assert message.content == 'test_content'
        assert message.created_at is not None
        assert message.is_read == False
    
    def test_string_representation(self):
        user = UserFactory()
        user2 = UserFactory()
        chat = ChatFactory(participants=[user, user2])
        message = MessageFactory(chat=chat, user=user)
        assert str(message) == message.content