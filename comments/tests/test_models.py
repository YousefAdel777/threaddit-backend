import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from .factories import  (
    CommentFactory,
    CommentInteractionFactory,
    CommentReportFactory,
    PostFactory,
    UserFactory
)

@pytest.mark.django_db
class TestCommentModel:
    def test_comment_model_creation(self):
        user = UserFactory()
        post = PostFactory()
        parent_comment = CommentFactory(post=post)
        comment = CommentFactory(parent=parent_comment, content='test_content', post=post, user=user, status='accepted')
        assert comment.user == user
        assert comment.content == 'test_content'
        assert comment.post == post
        assert comment.parent == parent_comment
        assert comment.status == 'accepted'
        assert comment.created_at is not None

    def test_comment_creation_with_invalid_parent(self):
        post = PostFactory()
        parent_comment = CommentFactory(post=post)
        post2 = PostFactory()
        with pytest.raises(ValidationError, match='Parent comment must belong to the same post'):
            CommentFactory(parent=parent_comment, content='test_content', post=post2)

    def test_comment_string_representation(self):
        comment = CommentFactory()
        assert str(comment) == f"{comment.content} by {comment.user.username} on {comment.post.title}"

    def test_get_comment_interaction(self):
        comment = CommentFactory()
        user = UserFactory()
        CommentInteractionFactory(comment=comment, user=user)
        assert comment.get_interaction(user) is not None

    def test_get_is_reported(self):
        comment = CommentFactory()
        user = UserFactory()
        CommentReportFactory(comment=comment, user=user, status='pending')
        assert comment.get_is_reported(user)

@pytest.mark.django_db
class TestCommentInteractionModel:
    def test_comment_interaction_model_creation(self):
        user = UserFactory()
        comment = CommentFactory()
        interaction_type = 'upvote'
        interaction = CommentInteractionFactory(user=user, comment=comment, interaction_type=interaction_type)
        assert interaction.interaction_type == 'upvote'
        assert interaction.comment == comment
        assert interaction.user == user
        assert comment.get_interaction(user) == interaction

    def test_comment_interaction_string_representation(self):
        comment = CommentFactory()
        interaction = CommentInteractionFactory(comment=comment)
        assert str(interaction) == f"{interaction.interaction_type} by {interaction.user.username} on {interaction.comment.content}"

    def test_unique_interaction(self):
        user = UserFactory()
        comment = CommentFactory()
        CommentInteractionFactory(user=user, comment=comment, interaction_type='upvote')
        with pytest.raises(IntegrityError):
            CommentInteractionFactory(user=user, comment=comment, interaction_type='upvote')

@pytest.mark.django_db
class TestCommentReportModel:
    def test_comment_report_model_creation(self):
        user = UserFactory()
        comment = CommentFactory()
        report = CommentReportFactory(user=user, comment=comment, status='pending', reason='test_reason')
        assert report.user == user
        assert report.comment == comment
        assert report.status == 'pending'
        assert report.reason == 'test_reason'
    

    def test_comment_report_string_representation(self):
        comment = CommentFactory()
        report = CommentReportFactory(comment=comment)
        assert str(report) == f"Comment Report: {report.id} by {report.user.username}"