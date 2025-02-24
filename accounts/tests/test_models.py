import pytest
from django.contrib.auth import get_user_model
from accounts.models import Follow, Block
from django.db.utils import IntegrityError
User = get_user_model()

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='testpassword', email='test@example.com', bio='testbio')

@pytest.fixture
def user2():
    return User.objects.create_user(username='testuser2', password='testpassword2', email='test2@example.com')

@pytest.fixture
def follow(user, user2):
    return Follow.objects.create(followed=user2, follower=user)

@pytest.fixture
def block(user, user2):
    return Block.objects.create(blocked_by=user, blocked_user=user2)

@pytest.mark.django_db
def test_user_model_creation(user):
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'
    assert user.check_password('testpassword')
    assert user.bio == 'testbio'
    assert user.post_karma == 0
    assert user.comment_karma == 0
    assert User.objects.count() == 1
    assert str(user) == 'testuser'

@pytest.mark.django_db
def test_user_model_update(user):
    user.bio = 'test bio'
    user.save()
    updated_user = User.objects.get(id=user.id)
    assert updated_user.bio == 'test bio'

@pytest.mark.django_db
def test_email_unique_constraint(user):
    with pytest.raises(IntegrityError):
        User.objects.create_user(username='testuser', password='testpassword', email='test@example.com')

@pytest.mark.django_db
def test_update_post_karma(user):
    user.update_post_karma(5)
    user = User.objects.get(id=user.id)
    assert user.post_karma == 5

@pytest.mark.django_db
def test_update_comment_karma(user):
    user.update_comment_karma(5)
    user = User.objects.get(id=user.id)
    assert user.comment_karma == 5

@pytest.mark.django_db
def test_get_block_id(user):
    user2 = User.objects.create_user(email='user2@example.com', username='user2', password='password')
    block = Block.objects.create(blocked_by=user, blocked_user=user2)
    block_id = user2.get_block_id(user)
    assert block_id == block.id

@pytest.mark.django_db
def test_get_follow_id(user):
    user2 = User.objects.create_user(email='user2@example.com', username='user2', password='password')
    follow = Follow.objects.create(follower=user, followed=user2)
    follow_id = user2.get_follow_id(user)
    assert follow_id == follow.id

@pytest.mark.django_db
def test_followers_count_property(user):
    user2 = User.objects.create_user(email='user2@example.com', username='user2', password='password')
    Follow.objects.create(follower=user2, followed=user)
    assert user.followers_count == 1

@pytest.mark.django_db
def test_follow_creation(user, user2, follow):
    assert follow.followed == user2
    assert follow.follower == user
    assert str(follow) == f"{user.username} follows {user2.username}"

@pytest.mark.django_db
def test_block_uniqueness(user, user2, block):
    with pytest.raises(IntegrityError):
        Block.objects.create(blocked_by=user, blocked_user=user2)

@pytest.mark.django_db
def test_follow_creation(user, user2, block):
    assert block.blocked_user == user2
    assert block.blocked_by == user
    assert str(block) == f"{user.username} blocked {user2.username}"

@pytest.mark.django_db
def test_follow_uniqueness(user, user2, follow):
    with pytest.raises(IntegrityError):
        Follow.objects.create(follower=user, followed=user2)