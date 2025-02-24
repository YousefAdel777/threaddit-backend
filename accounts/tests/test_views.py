from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Block, Follow
import pytest
User = get_user_model()

@pytest.fixture
def user():
    return User.objects.create(username='testuser', password='testpassword', email='test@example.com', bio='testbio')

@pytest.fixture
def user2():
        return User.objects.create(username='testuser2', password='testpassword2', email='test2@example.com', bio='testbio2')


@pytest.fixture
def client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client 

@pytest.mark.django_db
def test_users_list_view(client, user):
    url = reverse('users-list')
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) > 0

@pytest.mark.django_db
def test_search_by_username(client, user):
    url = reverse('users-list')
    response = client.get(url, {'search': 'testuser'})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1

@pytest.mark.django_db
def test_search_by_bio(client, user):
    url = reverse('users-list')
    response = client.get(url, {'search': 'testbio'})
    print(response.data)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1

@pytest.mark.django_db
def test_user_detail_view_with_valid_id(client, user2):
    url = reverse('user-detail', args=[user2.id])
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['username'] == 'testuser2'

@pytest.mark.django_db
def test_user_detail_view_with_invalid_id(client, user):
    url = reverse('user-detail', args=[9999])
    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_get_blocked_user(client, user, user2):
    block = Block.objects.create(blocked_by=user, blocked_user=user2)
    url = reverse('user-detail', args=[user2.id])
    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_get_blocked_by_user(client, user, user2):
    block = Block.objects.create(blocked_by=user2, blocked_user=user)
    url = reverse('user-detail', args=[user2.id])
    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_get_blocked_users(client, user, user2):
    Block.objects.create(blocked_by=user, blocked_user=user2)
    url = reverse('blocked-users-list')
    response = client.get(url)
    assert len(response.data) == 1
    assert response.data[0]['username'] == 'testuser2'

@pytest.mark.django_db
def test_create_block_with_valid_id(client, user, user2):
    url = reverse('blocks-create')
    data = {'blocked_user': user2.id}
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['blocked_user'] == user2.id
    assert response.data['blocked_by'] == user.id

@pytest.mark.django_db
def test_create_block_with_invalid_id(client, user, user2):
    url = reverse('blocks-create')
    data = {'blocked_user': 9999}
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_delete_block_with_valid_id(client, user, user2):
    block = Block.objects.create(blocked_by=user, blocked_user=user2)
    url = reverse('blocks-delete', args=[block.id])
    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT

@pytest.mark.django_db
def test_delete_block_with_invalid_id(client):
    url = reverse('blocks-delete', args=[9999])
    response = client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_create_follow_with_valid_id(client, user, user2):
    url = reverse('follows-create')
    data = {'followed': user2.id}
    response = client.post(url, data, format='json')
    print(response.data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['followed'] == user2.id
    assert response.data['follower'] == user.id

@pytest.mark.django_db
def test_create_follow_with_existing_follow(client, user, user2):
    Follow.objects.create(followed=user2, follower=user)
    url = reverse('follows-create')
    data = {'followed': user2.id}
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_follow_with_same_id(client, user, user2):
    url = reverse('follows-create')
    data = {'followed': user.id}
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_follow_with_invalid_id(client, user):
    url = reverse('follows-create')
    data = {'followed': 9999}
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_follow_with_blocked_user(client, user, user2):
    Block.objects.create(blocked_by=user, blocked_user=user2)
    url = reverse('follows-create')
    data = {'followed': user2.id}
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_delete_follow_with_valid_id(client, user, user2):
    follow = Follow.objects.create(followed=user2, follower=user)
    url = reverse('follows-delete', args=[follow.id])
    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT

@pytest.mark.django_db
def test_delete_follow_with_invalid_id(client, user):
    url = reverse('follows-delete', args=[9999])
    response = client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_get_followed_users(client, user, user2):
    Follow.objects.create(followed=user2, follower=user)
    url = reverse('followed-users-list')
    response = client.get(url)
    assert len(response.data) == 1
    assert response.data[0]['username'] == 'testuser2'