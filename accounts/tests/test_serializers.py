import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from accounts.serializers import (
        CustomLoginSerializer, 
        CustomUserSerializer, 
        CustomUserCreateSerializer, 
        BlockSerializer, 
        FollowSerializer
    )
User = get_user_model()
from accounts.models import Follow, Block

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='testpassword', email='test@example.com', image='testimage', bio='testbio')

@pytest.fixture
def user2():
    return User.objects.create_user(username='testuser2', password='testpassword2', email='test2@example.com')

@pytest.fixture
def serializer_context(user):
    request = APIRequestFactory().get('/')
    request.user = user
    return {'request': request}

@pytest.mark.django_db
class TestCustomLoginSerializer:
    def test_valid_login_serializer(self, user):        
        serializer = CustomLoginSerializer(data={'email': 'test@example.com', 'password': 'testpassword'})
        assert serializer.is_valid()
        assert serializer.validated_data['email'] == 'test@example.com'
        assert serializer.validated_data['password'] == 'testpassword'
        
    def test_invalid_login_serializer(self, user):
        serializer = CustomLoginSerializer(data={'email': 'test@example.com', 'password': 'wrongpassword'})
        assert serializer.is_valid() is False

    def test_invalid_email(self, user):
        serializer = CustomLoginSerializer(data={'email': 'test', 'password': 'testpassword'})
        assert serializer.is_valid() is False
        assert 'email' in serializer.errors

@pytest.mark.django_db
class TestRegisterSerializer:
    def test_valid_register_serializer(self):
        serializer = CustomUserCreateSerializer(data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword',
        })
        assert serializer.is_valid()
        assert serializer.validated_data['username'] == 'testuser'
        assert serializer.validated_data['email'] == 'test@example.com'
        assert serializer.validated_data['password'] == 'testpassword'

    def test_register_serializer_used_email(self, user):
        serializer = CustomUserCreateSerializer(data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword',
        })
        assert serializer.is_valid() is False
        assert 'email' in serializer.errors

    def test_register_serializer_invalid_email(self, user):
        serializer = CustomUserCreateSerializer(data={
            'username': 'testuser',
            'email': 'test',
            'password': 'testpassword',
        })
        assert serializer.is_valid() is False
        assert 'email' in serializer.errors

@pytest.mark.django_db
class TestCustomUserSerializer:
    def test_user_serializer_fields(self, user, serializer_context):
        serializer = CustomUserSerializer(user, context=serializer_context)
        assert serializer.data['id'] == user.id
        assert serializer.data['username'] == 'testuser'
        assert serializer.data['bio'] == 'testbio'
        assert 'testimage' in serializer.data['image']
        assert serializer.data['post_karma'] == 0
        assert serializer.data['comment_karma'] == 0
        assert 'created_at' in serializer.data
        assert serializer.data['is_current_user'] is True

    def test_custom_user_serializer_block_id(self, user, user2, serializer_context):
        block = Block.objects.create(blocked_by=user, blocked_user=user2)
        serializer = CustomUserSerializer(user2, context=serializer_context)
        block_id = serializer.data['block_id']
        assert block_id == block.id
    
    def test_custom_user_serializer_follow_id(self, user, user2, serializer_context):
        follow = Follow.objects.create(follower=user, followed=user2)
        serializer = CustomUserSerializer(user2, context=serializer_context)
        follow_id = serializer.data['follow_id']
        assert follow_id == follow.id

    def test_custom_user_serializer_followers_count(self, user, user2, serializer_context):
        Follow.objects.create(follower=user, followed=user2)
        serializer = CustomUserSerializer(user2, context=serializer_context)
        followers_count = serializer.data['followers_count']
        assert followers_count == 1

@pytest.mark.django_db
class TestBlockSerializer:

    def test_valid_block_serializer(self, user, user2):
        serializer = BlockSerializer(data={'blocked_by': user.id, 'blocked_user': user2.id})
        assert serializer.is_valid()
        assert serializer.validated_data['blocked_by'] == user
        assert serializer.validated_data['blocked_user'] == user2

    def test_default_blocked_by(self, user2, serializer_context):
        serializer = BlockSerializer(data={'blocked_user': user2.id}, context=serializer_context)
        assert serializer.is_valid()
        assert serializer.validated_data['blocked_by'] == serializer_context['request'].user
        assert serializer.validated_data['blocked_user'] == user2

    def test_self_block(self, user):
        serializer = BlockSerializer(data={'blocked_by': user.id, 'blocked_user': user.id})
        assert serializer.is_valid() is False
        assert 'non_field_errors' in serializer.errors
        assert serializer.errors['non_field_errors'][0] == 'User cannot block themselves'

    def test_block_serializer_unique_together(self, user, user2):
        Block.objects.create(blocked_by=user, blocked_user=user2)
        serializer = BlockSerializer(data={'blocked_by': user.id, 'blocked_user': user2.id})
        assert serializer.is_valid() is False
        assert 'non_field_errors' in serializer.errors
        assert serializer.errors['non_field_errors'][0] == 'User has already blocked this user'

@pytest.mark.django_db
class TestFollowSerializer:
    def test_valid_follow_serializer(self, user, user2):
        serializer = FollowSerializer(data={'follower': user.id, 'followed': user2.id})
        assert serializer.is_valid()
        follow = serializer.save()
        assert follow.follower == user
        assert follow.followed == user2

    def test_default_follower(self, user2, serializer_context):
        serializer = FollowSerializer(data={'followed': user2.id}, context=serializer_context)
        assert serializer.is_valid()
        follow = serializer.save()
        assert follow.follower == serializer_context['request'].user
        assert follow.followed == user2

    def test_follow_serializer_unique_together(self, user, user2):
        Follow.objects.create(follower=user, followed=user2)
        serializer = FollowSerializer(data={'follower': user.id, 'followed': user2.id})
        assert serializer.is_valid() is False
        assert 'non_field_errors' in serializer.errors
        assert serializer.errors['non_field_errors'][0] == 'User is already following this user'

    def test_self_follow(self, user):
        serializer = FollowSerializer(data={'follower': user.id, 'followed': user.id})
        assert serializer.is_valid() is False
        assert 'non_field_errors' in serializer.errors
        assert serializer.errors['non_field_errors'][0] == 'User cannot follow themselves'