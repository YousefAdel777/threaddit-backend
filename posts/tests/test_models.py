import pytest
from .factories import (
    PostFactory, 
    UserFactory,
    PostInteractionFactory, 
    SavedPostFactory,
    AttachmentFactory,
    PostReportFactory, 
    CommentFactory
)
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

@pytest.mark.django_db
class TestPostModel:
    def test_post_creation(self):
        user = UserFactory()
        post = PostFactory(user=user, content='test_content', type='text', title='test_title')
        assert post.user == user
        assert post.content == 'test_content'
        assert post.type == 'text'
        assert post.title == 'test_title'
        assert post.created_at is not None

    def test_string_representation(self):
        post = PostFactory(type='text')
        assert str(post) == post.title

    def test_get_user_interaction(self):
        user = UserFactory()
        post = PostFactory(user=user, type='text')
        post_interaction = PostInteractionFactory(user=user, post=post)
        assert post.get_user_interaction(user) == post_interaction
    
    def test_get_saved_post_id(self):
        user = UserFactory()
        post = PostFactory(user=user, type='text')
        saved_post = SavedPostFactory(user=user, post=post)
        assert post.get_saved_post_id(user) == saved_post.id

    def test_get_is_reported_with_pending_report(self):
        user = UserFactory()
        user2 = UserFactory()
        post = PostFactory(user=user, type='text')
        PostReportFactory(user=user2, post=post, status='pending')
        assert post.get_is_reported(user2)

    def test_get_is_reported_with_non_pending_report(self):
        user = UserFactory()
        user2 = UserFactory()
        post = PostFactory(user=user, type='text')
        PostReportFactory(user=user2, post=post, status='dismissed')
        assert post.get_is_reported(user2) is False
    
    def test_comments_count(self):
        user = UserFactory()
        post = PostFactory(user=user, type='text')
        CommentFactory(post=post, user=user)
        assert post.comments_count == 1

    def test_text_post_must_have_content(self):
        with pytest.raises(ValidationError, match="Text posts must have content"):
            PostFactory(type='text', content="")

    def test_link_post_must_have_link(self):
        with pytest.raises(ValidationError, match="Link posts must have a URL"):
            PostFactory(type='link', link="")

    def test_crosspost_must_have_original_post(self):
        with pytest.raises(ValidationError, match="Crossposts must reference an original post"):
            PostFactory(type='crosspost', original_post=None)

    def test_text_poll_crosspost_cannot_have_link(self):
        with pytest.raises(ValidationError, match="Text, poll, and crosspost types should not have a link"):
            PostFactory(type='text', link="https://example.com")

    def test_link_posts_can_have_content(self):
        post = PostFactory(type='link', content="content", link="https://example.com")
        post.full_clean()
        assert post.content == "content"
        assert post.link == "https://example.com"

    def test_media_posts_can_have_content(self):
        post = PostFactory(type='media', content="content")
        post.full_clean()
        assert post.content == "content"

    def test_valid_text_post(self):
        post = PostFactory(type='text', content="This is a valid text post.")
        post.full_clean()
        assert post.content == "This is a valid text post."

    def test_valid_link_post(self):
        post = PostFactory(type='link', link="https://example.com", content="")
        post.full_clean()
        assert post.link == "https://example.com"

    def test_valid_crosspost(self):
        post = PostFactory(type='text')
        crosspost = PostFactory(type='crosspost', original_post=post)
        crosspost.full_clean()
        assert crosspost.original_post == post

@pytest.mark.django_db
class TestPostInteractionModel:
    def test_post_interaction_creation(self):
        user = UserFactory()
        post = PostFactory(user=user, type='text')
        post_interaction = PostInteractionFactory(post=post, user=user)
        assert post_interaction.interaction_type in ['upvote', 'downvote']
        assert post_interaction.user == user
        assert post_interaction.post == post

    def test_string_representation(self):
        user = UserFactory()
        post = PostFactory(user=user, type='text')
        post_interaction = PostInteractionFactory(user=user, post=post)
        assert str(post_interaction) == f"{post_interaction.interaction_type} by {user.username} on {post.title}"

    def test_unique_together(self):
        user = UserFactory()
        post = PostFactory(user=user, type='text')
        PostInteractionFactory(user=user, post=post)
        with pytest.raises(IntegrityError):
            PostInteractionFactory(user=user, post=post)

@pytest.mark.django_db
class TestSavedPostModel:
    def test_saved_post_creation(self):
        user = UserFactory()
        post = PostFactory(user=user, type='text')
        saved_post = SavedPostFactory(user=user, post=post)
        assert saved_post.user == user
        assert saved_post.post == post
    
    def test_string_representation(self):
        user = UserFactory()
        post = PostFactory(user=user, type='text')
        saved_post = SavedPostFactory(user=user, post=post)
        assert str(saved_post) == f"Saved Post: {post.title} by {user.username}"
    
    def test_unique_together(self):
        user = UserFactory()
        post = PostFactory(user=user, type='text')
        SavedPostFactory(user=user, post=post)
        with pytest.raises(IntegrityError):
            SavedPostFactory(user=user, post=post)

@pytest.mark.django_db
class TestAttachmentModel:
    def test_attachment_creation(self):
        post = PostFactory(type='text', title='test_title')
        attachment = AttachmentFactory(file='test_file', file_type='image', post=post)
        assert attachment.file == 'test_file'
        assert attachment.post == post
        assert attachment.file_type == 'image'

    def test_string_representation(self):
        post = PostFactory(type='text', title='test_title')
        attachment = AttachmentFactory(file='test_file', file_type='image', post=post)
        assert str(attachment) == f"Attachment: {attachment.file} for {post.title}"

@pytest.mark.django_db
class TestPostReportModel:
    def test_post_report_creation(self):
        user = UserFactory()
        user2 = UserFactory()
        post = PostFactory(user=user, type='text')
        post_report = PostReportFactory(user=user2, post=post, status='pending')
        assert post_report.user == user2
        assert post_report.post == post
    
    def test_string_representation(self):
        user = UserFactory()
        user2 = UserFactory()
        post = PostFactory(user=user, type='text')
        post_report = PostReportFactory(user=user2, post=post, status='pending')
        assert str(post_report) == f"Post Report: {post.title} by {user2.username}"