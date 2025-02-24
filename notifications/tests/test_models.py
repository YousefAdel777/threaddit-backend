import pytest
from comments.models import Comment
from posts.models import Post
from notifications.models import Notification
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from notifications.signals import send_notification

User = get_user_model()

@pytest.fixture
def user():
    return User.objects.create(username='test', email='test@example.com')

@pytest.fixture
def post(user):
    return Post.objects.create(user=user, content='test_content', type='text', title='test_title')

@pytest.fixture
def comment(user, post):
    return Comment.objects.create(user=user, content='test_content', post=post)

@pytest.fixture
def notification(comment, user):
    content_type = ContentType.objects.get_for_model(comment)
    return Notification.objects.create(
        user=user,
        message='test_message',
        content_type=content_type,
        object_id=comment.pk
    )

@pytest.fixture(autouse=True)
def notifications_setup():
    post_save.disconnect(send_notification, sender=Notification)
    yield
    post_save.connect(send_notification, sender=Notification)

@pytest.mark.django_db
def test_notification_model_creation(notification, comment, user):
    content_type = ContentType.objects.get_for_model(comment)

    assert notification.user == user
    assert notification.message == 'test_message'
    assert notification.object_id == comment.pk
    assert notification.content_type == content_type
    assert notification.created_at is not None
    assert notification.is_read == False
    assert notification.content_object == comment
    assert str(notification) == 'Notification test_message'

@pytest.mark.django_db
def test_notification_model_update(notification):
    notification.is_read = True
    notification.message = 'test_message_updated'
    notification.save()


    updated_notification = Notification.objects.get(id=notification.id)
    assert updated_notification.is_read == True
    assert updated_notification.message == 'test_message_updated'

@pytest.mark.django_db
def test_notification_delete(notification):
    notification.delete()
    assert Notification.objects.count() == 0