import pytest
from rest_framework.test import APIRequestFactory
from .factories import (
    CommentFactory,
    CommentInteractionFactory,
    CommentReportFactory,
    CommunityFactory,
    UserFactory,
    PostFactory,
    RuleFactory,
    MemberFactory
)
from posts.serializers import PostReadSerializer
from communities.serializers import RuleSerializer
from accounts.serializers import CustomUserSerializer
from comments.serializers import (
    CommentWriteSerializer,
    CommentUpdateSerializer,
    CommentReadSerializer,
    CommentInteractionSerializer,
    CommentReportWriteSerializer,
    CommentReportReadSerializer
)

@pytest.fixture
def serializer_context():
    user = UserFactory()
    request = APIRequestFactory().get('/')
    request.user = user
    return {'request': request}

@pytest.mark.django_db
class TestCommentWriteSerializer:
    def test_valid_comment_serializer(self, serializer_context):
        post = PostFactory()
        parent_comment = CommentFactory(post=post)
        data = {
            'content': 'test_content',
            'post': post.id,
            'parent': parent_comment.id
        }
        serializer = CommentWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid()
        comment = serializer.save()
        assert comment.content == 'test_content'
        assert comment.post == post
        assert comment.parent == parent_comment
        assert comment.user == serializer_context['request'].user
        assert comment.created_at is not None

    def test_comment_serializer_with_invalid_parent(self, serializer_context):
        post = PostFactory()
        parent_comment = CommentFactory(post=post)
        post2 = PostFactory()
        data = {
            'content': 'test_content',
            'post': post2.id,
            'parent': parent_comment.id
        }
        serializer = CommentWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['Parent comment must belong to the same post']}

@pytest.mark.django_db
class TestCommentUpdateSerializer:
    def test_valid_comment_update_serializer(self, serializer_context):
        user = serializer_context['request'].user
        comment = CommentFactory(user=user)
        data = {'content': 'test_content'}
        serializer = CommentUpdateSerializer(instance=comment, data=data, context=serializer_context, partial=True)
        assert serializer.is_valid()
        comment = serializer.save()
        assert comment.content == 'test_content'
    
    def test_update_status_if_not_moderator(self, serializer_context):
        user = serializer_context['request'].user
        comment = CommentFactory(user=user)
        data = {'status': 'removed'}
        serializer = CommentUpdateSerializer(instance=comment, data=data, context=serializer_context, partial=True)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['Only moderators can change comment status']}
    
    def test_update_status_if_moderator(self, serializer_context):
        user = serializer_context['request'].user
        community = CommunityFactory()
        post = PostFactory(community=community)
        MemberFactory(user=user, is_moderator=True, community=community)
        comment = CommentFactory(post=post)
        data = {'status': 'removed'}
        serializer = CommentUpdateSerializer(instance=comment, data=data, context=serializer_context, partial=True)
        assert serializer.is_valid()
        comment = serializer.save()
        assert comment.status == 'removed'
    
    def test_update_comment_if_moderator_with_invalida_data(self, serializer_context):
        user = serializer_context['request'].user
        community = CommunityFactory()
        post = PostFactory(community=community)
        MemberFactory(user=user, is_moderator=True, community=community)
        comment = CommentFactory(post=post)
        data = {'content': 'test_content'}
        serializer = CommentUpdateSerializer(instance=comment, data=data, context=serializer_context, partial=True)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['Moderators can only change the status of comments']}

@pytest.mark.django_db
class TestCommentReadSerializer:
    def test_comment_read_serializer_fields(self, serializer_context):
        user = serializer_context['request'].user
        post = PostFactory()
        parent_comment = CommentFactory(post=post)
        comment = CommentFactory(user=user, parent=parent_comment, post=post)
        serializer = CommentReadSerializer(instance=comment, context=serializer_context)
        assert serializer.data['id'] == comment.id
        assert serializer.data['content'] == comment.content
        assert serializer.data['post'] == PostReadSerializer(comment.post, context=serializer_context).data
        assert serializer.data['parent'] == parent_comment.id
        assert serializer.data['user'] == CustomUserSerializer(comment.user, context=serializer_context).data
        assert serializer.data['created_at'] is not None
        assert serializer.data['is_reported'] is False
    
    def test_comment_read_serializer_is_reported(self, serializer_context):
        user = serializer_context['request'].user
        comment = CommentFactory()
        CommentReportFactory(comment=comment, user=user, status='pending')
        serializer = CommentReadSerializer(comment, context=serializer_context)
        assert serializer.data['is_reported']

    def test_comment_read_serializer_interaction(self, serializer_context):
        user = serializer_context['request'].user
        comment = CommentFactory()
        interaction = CommentInteractionFactory(user=user, comment=comment, interaction_type='upvote')
        serializer = CommentReadSerializer(comment, context=serializer_context)
        assert serializer.data['interaction'] == CommentInteractionSerializer(interaction, context=serializer_context).data

    def test_comment_read_serializer_replies(self, serializer_context):
        post = PostFactory()
        parent_comment = CommentFactory(post=post)
        CommentFactory(parent=parent_comment, post=post)
        serializer = CommentReadSerializer(parent_comment, context=serializer_context)
        assert len(serializer.data['replies']) == 1

@pytest.mark.django_db
class TestCommentInteractionSerializer:
    def test_valid_comment_interaction_serializer(self, serializer_context):
        comment = CommentFactory()
        data = {
            'comment': comment.id,
            'interaction_type': 'upvote'
        }
        serializer = CommentInteractionSerializer(data=data, context=serializer_context)
        assert serializer.is_valid()
        interaction = serializer.save()
        assert interaction.comment == comment
        assert interaction.user == serializer_context['request'].user

    def test_duplicate_comment_interaction(self, serializer_context):
        comment = CommentFactory()
        CommentInteractionFactory(comment=comment, user=serializer_context['request'].user)
        data = {
            'comment': comment.id,
            'interaction_type': 'upvote'
        }
        serializer = CommentInteractionSerializer(data=data, context=serializer_context)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['User has already interacted with this comment']}

    def test_comment_interaction_serializer_fields(self, serializer_context):
        comment = CommentFactory()
        interaction = CommentInteractionFactory(comment=comment, interaction_type='upvote', user=serializer_context['request'].user)
        serializer = CommentInteractionSerializer(interaction, context=serializer_context)
        assert serializer.data['id'] == interaction.id
        assert serializer.data['interaction_type'] == 'upvote'
        assert serializer.data['comment'] == comment.id
        assert serializer.data['user'] == serializer_context['request'].user.id

@pytest.mark.django_db
class TestCommentReportWriteSerializer:
    def test_valid_comment_report_serializer(self, serializer_context):
        comment = CommentFactory()
        rule = RuleFactory(community=comment.post.community)
        data = {
            'comment': comment.id,
            'violated_rule': rule.id,
            'reason': 'test_reason'
        }
        serializer = CommentReportWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid()
        report = serializer.save()
        assert report.comment == comment
        assert report.violated_rule == rule
        assert report.user == serializer_context['request'].user
        assert report.reason == 'test_reason'

    def test_comment_report_serializer_with_invalid_rule(self, serializer_context):
        comment = CommentFactory()
        rule = RuleFactory()
        data = {
            'comment': comment.id,
            'reason': 'test_reason',
            'violated_rule': rule.id
        }
        serializer = CommentReportWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['Violated rule must belong to the same community as the comment']}

    def test_comment_report_on_post_without_community(self, serializer_context):
        post = PostFactory(community=None)
        comment = CommentFactory(post=post)
        data = {
            'comment': comment.id,
            'reason': 'test_reason',
        }
        serializer = CommentReportWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid() is False
        assert serializer.errors == {'comment': ['Comment must belong to a community']}

    def test_comment_report_serializer_with_pending_report(self, serializer_context):
        user = serializer_context['request'].user
        comment = CommentFactory()
        CommentReportFactory(comment=comment, user=user, status='pending')
        data = {
            'comment': comment.id,
            'reason': 'test_reason',
        }
        serializer = CommentReportWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid() is False
        assert serializer.errors == {'comment': ['You already have a pending report for this comment']}

    def test_comment_report_serializer_if_user_is_author(self, serializer_context):
        user = serializer_context['request'].user
        comment = CommentFactory(user=user)
        data = {
            'comment': comment.id,
            'reason': 'test_reason',
        }
        serializer = CommentReportWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid() is False
        assert serializer.errors == {'comment': ['You cannot report your own comment']}

@pytest.mark.django_db
class TestCommentReportReadSerializer:
    def test_comment_report_read_serializer_fields(self, serializer_context):
        user = serializer_context['request'].user
        comment = CommentFactory()
        report = CommentReportFactory(comment=comment, user=user, status='pending')
        serializer = CommentReportReadSerializer(report, context=serializer_context)
        assert serializer.data['id'] == report.id
        assert serializer.data['reason'] == report.reason
        assert serializer.data['status'] == report.status
        assert serializer.data['created_at'] is not None
        assert serializer.data['comment'] == CommentReadSerializer(comment, context=serializer_context).data
        assert serializer.data['violated_rule'] == RuleSerializer(report.violated_rule, context=serializer_context).data
        assert serializer.data['user'] == CustomUserSerializer(user, context=serializer_context).data