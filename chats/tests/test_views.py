from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import pytest
from .factories import (
    UserFactory,
    MessageFactory,
    ChatFactory,
    BlockFactory
)

@pytest.fixture
def user():
    return UserFactory()

@pytest.fixture
def client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.mark.django_db
class TestChatListCreateView:
    def test_get_chats(self, client, user):
        user2 = UserFactory()
        ChatFactory(participants=[user.id, user2.id])
        url = reverse('chat-list-create')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['participants'][0]['id'] == user.id
        assert response.data[0]['participants'][1]['id'] == user2.id

    def test_create_valid_chat(self, client, user):
        user2 = UserFactory()
        url = reverse('chat-list-create')
        response = client.post(url, {'participants': [user.id, user2.id]})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['participants'][0]['id'] == user.id
        assert response.data['participants'][1]['id'] == user2.id
    
    def test_create_chat_with_same_user(self, client, user):
        url = reverse('chat-list-create')
        response = client.post(url, {'participants': [user.id, user.id]})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_chat_with_non_existing_user(self, client, user):
        url = reverse('chat-list-create')
        response = client.post(url, {'participants': [user.id, 999]})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_duplicate_chat(self, client, user):
        user2 = UserFactory()
        ChatFactory(participants=[user.id, user2.id])
        url = reverse('chat-list-create')
        response = client.post(url, {'participants': [user.id, user2.id]})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_chat_with_blocked_user(self, client, user):
        user2 = UserFactory()
        BlockFactory(blocked_by=user, blocked_user=user2)
        url = reverse('chat-list-create')
        response = client.post(url, {'participants': [user.id, user2.id]})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_chat_with_current_user_blocked(self, client, user):
        user2 = UserFactory()
        BlockFactory(blocked_by=user2, blocked_user=user)
        url = reverse('chat-list-create')
        response = client.post(url, {'participants': [user.id, user2.id]})
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestChatDetailView:
    def test_get_valid_chat(self, client, user):
        user2 = UserFactory()
        chat = ChatFactory(participants=[user.id, user2.id])
        url = reverse('chat-detail', args=[chat.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_get_chat_with_blocked_user(self, client, user):
        user2 = UserFactory()
        chat = ChatFactory(participants=[user.id, user2.id])
        BlockFactory(blocked_by=user, blocked_user=user2)
        url = reverse('chat-detail', args=[chat.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['other_participant'] is None

    def test_get_chat_with_current_user_blocked(self, client, user):
        user2 = UserFactory()
        chat = ChatFactory(participants=[user.id, user2.id])
        BlockFactory(blocked_by=user2, blocked_user=user)
        url = reverse('chat-detail', args=[chat.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['other_participant'] is None

    def test_get_chat_with_invlid_id(self, client):
        url = reverse('chat-detail', args=[9999])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_chat_with_current_user_non_participant(self, client):
        user2 = UserFactory()
        user3 = UserFactory()
        chat = ChatFactory(participants=[user3.id, user2.id])
        url = reverse('chat-detail', args=[chat.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND 

    def test_delete_chat_not_allowed(self, client, user):
        user2 = UserFactory()
        chat = ChatFactory(participants=[user2.id, user.id])
        url = reverse('chat-detail', args=[chat.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_update_chat_participants_not_allowed(self, client, user):
        user2 = UserFactory()
        chat = ChatFactory(participants=[user2.id, user.id])
        url = reverse('chat-detail', args=[chat.id])
        response = client.put(url, {'participants': [user.id, user2.id]})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestMessageListCreateView:
    def test_create_message(self, client, user):
        user2 = UserFactory()
        ChatFactory(participants=[user.id, user2.id])
        data = {
            'user': user.id,
            'content': 'test_content',
            'chat': 1
        }
        url = reverse('message-list-create')
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == 'test_content'
        assert response.data['user']['id'] == user.id
        assert response.data['chat'] == 1

    def test_create_message_with_blocked_user(self, client, user):
        user2 = UserFactory()
        ChatFactory(participants=[user.id, user2.id])
        BlockFactory(blocked_by=user, blocked_user=user2)
        data = {
            'user': user.id,
            'content': 'test_content',
            'chat': 1
        }
        url = reverse('message-list-create')
        response = client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_message_with_current_user_blocked(self, client, user):
        user2 = UserFactory()
        ChatFactory(participants=[user.id, user2.id])
        BlockFactory(blocked_by=user2, blocked_user=user)
        data = {
            'user': user.id,
            'content': 'test_content',
            'chat': 1
        }
        url = reverse('message-list-create')
        response = client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_message_with_invalid_chat_id(self, client, user):
        data = {
            'user': user.id,
            'content': 'test_content',
            'chat': 9999
        }
        url = reverse('message-list-create')
        response = client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestMessageDetailView:
    def test_get_message(self, client, user):
        user2 = UserFactory()
        chat = ChatFactory(participants=[user.id, user2.id])
        message = MessageFactory(user=user, chat=chat)
        url = reverse('message-detail', args=[message.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == message.id
        assert response.data['user']['id'] == user.id
        assert response.data['content'] == message.content
        assert response.data['chat'] == chat.id
        assert response.data['created_at'] is not None

    def test_update_message(self, client, user):
        user2 = UserFactory()
        chat = ChatFactory(participants=[user.id, user2.id])
        message = MessageFactory(user=user, chat=chat, content='test_content')
        url = reverse('message-detail', args=[message.id])
        data = {
            'content': 'test_content_updated',
            'chat': 1
        }
        response = client.put(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == message.id
        assert response.data['user']['id'] == user.id
        assert response.data['content'] == 'test_content_updated'

    def test_update_message_with_not_sender(self, client, user):
        user2 = UserFactory()
        chat = ChatFactory(participants=[user.id, user2.id])
        message = MessageFactory(user=user2, chat=chat)
        url = reverse('message-detail', args=[message.id])
        data = {
            'content': 'test_content',
            'chat': 1
        }
        response = client.put(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_message(self, client, user):
        user2 = UserFactory()
        chat = ChatFactory(participants=[user.id, user2.id])
        message = MessageFactory(user=user, chat=chat)
        url = reverse('message-detail', args=[message.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_message_with_not_sender(self, client, user):
        user2 = UserFactory()
        chat = ChatFactory(participants=[user.id, user2.id])
        message = MessageFactory(user=user2, chat=chat)
        url = reverse('message-detail', args=[message.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestMarkAsReadView:
    def test_mark_as_read_with_not_sender(self, client, user):
        user2 = UserFactory()
        chat = ChatFactory(participants=[user.id, user2.id])
        message = MessageFactory(user=user2, chat=chat)
        url = reverse('mark-as-read')
        response = client.post(url, { 'chat': chat.id })
        assert response.status_code == status.HTTP_200_OK
        url = reverse('message-detail', args=[message.id])
        response = client.get(url)
        assert response.data['is_read']

    def test_mark_as_read_with_sender(self, client, user):
        user2 = UserFactory()
        chat = ChatFactory(participants=[user.id, user2.id])
        message = MessageFactory(user=user, chat=chat)
        url = reverse('mark-as-read')
        response = client.post(url, { 'chat': chat.id })
        assert response.status_code == status.HTTP_200_OK
        url = reverse('message-detail', args=[message.id])
        response = client.get(url)
        assert response.data['is_read'] is False
    
    def test_mark_as_read_with_blocked_user(self, client, user):
        user2 = UserFactory()
        chat = ChatFactory(participants=[user.id, user2.id])
        BlockFactory(blocked_by=user, blocked_user=user2)
        MessageFactory(user=user2, chat=chat)
        url = reverse('mark-as-read')
        response = client.post(url, { 'chat': chat.id })
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_mark_as_read_with_current_blocked_user(self, client, user):
        user2 = UserFactory()
        chat = ChatFactory(participants=[user.id, user2.id])
        BlockFactory(blocked_by=user2, blocked_user=user)
        MessageFactory(user=user2, chat=chat)
        url = reverse('mark-as-read')
        response = client.post(url, { 'chat': chat.id })
        assert response.status_code == status.HTTP_403_FORBIDDEN