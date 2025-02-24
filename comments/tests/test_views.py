import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.core.cache import cache
from .factories import (
    CommentFactory,
    CommentInteractionFactory,
    CommentReportFactory,
    UserFactory,
    PostFactory,
    RuleFactory,
    BlockFactory,
    BanFactory,
    CommunityFactory,
    MemberFactory
)
from posts.serializers import PostReadSerializer
from accounts.serializers import CustomUserSerializer

@pytest.fixture(autouse=True)
def disable_cache():
    cache.clear()

@pytest.fixture
def user():
    return UserFactory()

@pytest.fixture
def client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.mark.django_db
class TestCommentListCreateView:
    def test_get_comments(self, client):
        CommentFactory()
        url = reverse('comment-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
    
    def test_get_comments_from_blocked_user(self, client, user):
        user2 = UserFactory()
        BlockFactory(blocked_by=user, blocked_user=user2)
        CommentFactory(user=user2)
        url = reverse('comment-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0
    
    def test_get_comments_with_banned_user(self, client, user):
        community = CommunityFactory()
        post = PostFactory(community=community)
        BanFactory(user=user, community=community)
        CommentFactory(post=post)
        url = reverse('comment-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0
    
    def test_create_comment(self, client, user):
        post = PostFactory()
        parent_comment = CommentFactory(post=post)
        url = reverse('comment-list')
        data = {'post': post.id, 'content': 'test_content', 'parent': parent_comment.id}
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['post']['id'] == post.id
        assert response.data['content'] == 'test_content'
        assert response.data['user']['id'] == user.id
        assert response.data['parent'] == parent_comment.id
        assert response.data['interaction'] is None
        assert response.data['interaction_diff'] == 0
        assert response.data['is_reported'] is False
        assert response.data['created_at'] is not None
        assert response.data['is_author']

    def test_create_comment_with_blocked_user(self, client, user):
        user2 = UserFactory()
        post = PostFactory(user=user2)
        BlockFactory(blocked_by=user, blocked_user=user2)
        url = reverse('comment-list')
        data = {'post': post.id, 'content': 'test_content'}
        response = client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_comment_with_banned_user(self, client, user):
        community = CommunityFactory()
        post = PostFactory(community=community)
        BanFactory(user=user, community=community, is_permanent=True)
        url = reverse('comment-list')
        data = {'post': post.id, 'content': 'test_content'}
        response = client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestCommentDetailView:
    def get_comment(self, client, user):
        comment = CommentFactory(user=user, parent=None)
        url = reverse('comment-detail', args=[comment.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == comment.id
        assert response.data['interaction_diff'] == 0
        assert response.data['interaction'] is None
        assert response.data['user']['id'] == user.id
        assert response.data['content'] == comment.content
        assert response.data['parent'] is None
        assert response.data['post']['id'] == comment.post.id
        assert response.data['created_at'] is not None
        assert response.data['is_reported'] is False
        assert response.data['is_author']

    def test_get_comment_with_blocked_user(self, client, user):
        user2 = UserFactory()
        post = PostFactory(user=user2)
        comment = CommentFactory(user=user2, post=post)
        BlockFactory(blocked_by=user, blocked_user=user2)
        url = reverse('comment-detail', args=[comment.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_comment_with_banned_user(self, client, user):
        community = CommunityFactory()
        post = PostFactory(community=community)
        comment = CommentFactory(post=post)
        BanFactory(user=user, community=community)
        url = reverse('comment-detail', args=[comment.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_comment(self, client, user):
        comment = CommentFactory(user=user, parent=None)
        url = reverse('comment-detail', args=[comment.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_comment_if_not_author(self, client):
        user2 = UserFactory()
        comment = CommentFactory(user=user2, parent=None)
        url = reverse('comment-detail', args=[comment.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_comment(self, client, user):
        comment = CommentFactory(user=user, parent=None)
        url = reverse('comment-detail', args=[comment.id])
        data = {'content': 'test_content'}
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['content'] == 'test_content'

    def test_update_comment_status_if_not_moderator(self, client, user):
        comment = CommentFactory(user=user, parent=None)
        url = reverse('comment-detail', args=[comment.id])
        data = {'status': 'removed'}
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_comment_if_not_author(self, client):
        user2 = UserFactory()
        comment = CommentFactory(user=user2, parent=None)
        url = reverse('comment-detail', args=[comment.id])
        data = {'content': 'test_content'}
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_comment_if_moderator_with_valid_data(self, client, user):
        community = CommunityFactory()
        post = PostFactory(community=community)
        MemberFactory(user=user, community=community, is_moderator=True)
        comment = CommentFactory(post=post)
        url = reverse('comment-detail', args=[comment.id])
        data = {'status': 'removed'}
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'removed'
    
    def test_update_comment_if_moderator_with_invalid_data(self, client, user):
        community = CommunityFactory()
        user2 = UserFactory()
        post = PostFactory(community=community)
        MemberFactory(user=user, community=community, is_moderator=True)
        comment = CommentFactory(post=post, user=user2)
        url = reverse('comment-detail', args=[comment.id])
        data = {'content': 'test_content'}
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestCommentInteractionListCreateView:

    def test_get_interactions(self, client, user):
        comment = CommentFactory()
        CommentInteractionFactory(comment=comment, user=user)
        url = reverse('comment-interaction-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_other_user_interactions(self, client):
        comment = CommentFactory()
        CommentInteractionFactory(comment=comment)
        url = reverse('comment-interaction-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_create_comment_interaction(self, client, user):
        comment = CommentFactory()
        url = reverse('comment-interaction-list')
        data = {'comment': comment.id, 'interaction_type': 'upvote'}
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['comment'] == comment.id
        assert response.data['interaction_type'] == 'upvote'
        assert response.data['user'] == user.id
        assert response.data['id'] is not None
        interaction_id = response.data['id']
        url = reverse('comment-detail', args=[comment.id])
        response = client.get(url)
        assert response.data['interaction_diff'] == 1
        assert response.data['interaction']['id'] == interaction_id
    
    def test_create_duplicate_comment_interaction(self, client, user):
        comment = CommentFactory()
        CommentInteractionFactory(comment=comment, user=user)
        url = reverse('comment-interaction-list')
        data = {'comment': comment.id, 'interaction_type': 'upvote'}
        response = client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_comment_interaction_with_invalid_type(self, client):
        comment = CommentFactory()
        url = reverse('comment-interaction-list')
        data = {'comment': comment.id, 'type': 'invalid_type'}
        response = client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_comment_interaction_with_blocked_user(self, client, user):
        user2 = UserFactory()
        post = PostFactory(user=user2)
        comment = CommentFactory(post=post, user=user2)
        BlockFactory(blocked_by=user, blocked_user=user2)
        url = reverse('comment-interaction-list')
        data = {'comment': comment.id, 'interaction_type': 'upvote'}
        response = client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_comment_interaction_with_banned_user(self, client, user):
        user2 = UserFactory()
        community = CommunityFactory()
        post = PostFactory(community=community)
        comment = CommentFactory(post=post, user=user2)
        BanFactory(user=user, community=community)
        url = reverse('comment-interaction-list')
        data = {'comment': comment.id, 'interaction_type': 'upvote'}
        response = client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestCommentInteractionDetailView:

    def test_get_interaction(self, client, user):
        comment = CommentFactory()
        interaction = CommentInteractionFactory(comment=comment, user=user)
        url = reverse('comment-interaction-detail', args=[interaction.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_get_other_user_interaction(self, client):
        comment = CommentFactory()
        interaction = CommentInteractionFactory(comment=comment)
        url = reverse('comment-interaction-detail', args=[interaction.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_interaction(self, client, user):
        comment = CommentFactory()
        interaction = CommentInteractionFactory(comment=comment, user=user)
        url = reverse('comment-interaction-detail', args=[interaction.id])
        data = {'interaction_type': 'downvote'}
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['interaction_type'] == 'downvote'

    def test_update_interaction_if_not_author(self, client, user):
        user2 = UserFactory()
        comment = CommentFactory()
        interaction = CommentInteractionFactory(comment=comment, user=user2)
        url = reverse('comment-interaction-detail', args=[interaction.id])
        data = {'interaction_type': 'downvote'}
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_interaction(self, client, user):
        comment = CommentFactory()
        interaction = CommentInteractionFactory(comment=comment, user=user)
        url = reverse('comment-interaction-detail', args=[interaction.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_interaction_if_not_author(self, client):
        user2 = UserFactory()
        comment = CommentFactory()
        interaction = CommentInteractionFactory(comment=comment, user=user2)
        url = reverse('comment-interaction-detail', args=[interaction.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
class TestCommentReportListCreateView:

    def test_get_reports(self, client, user):
        comment = CommentFactory()
        CommentReportFactory(comment=comment, user=user)
        url = reverse('comment-report-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0
    
    def test_get_reports_if_moderator(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=True)
        post = PostFactory(community=community)
        comment = CommentFactory(post=post)
        CommentReportFactory(comment=comment)
        url = reverse('comment-report-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
    
    def test_create_report(self, client, user):
        community = CommunityFactory()
        rule = RuleFactory(community=community)
        MemberFactory(user=user, community=community, is_moderator=True)
        post = PostFactory(community=community)
        comment = CommentFactory(post=post)
        CommentReportFactory(comment=comment)
        url = reverse('comment-report-list')
        data = {
            'comment': comment.id,
            'reason': 'test_reason',
            'violated_rule': rule.id
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['id'] is not None
        assert response.data['user']['id'] == user.id
        assert response.data['comment']['id'] == comment.id
        assert response.data['reason'] == 'test_reason'
        assert response.data['violated_rule']['id'] == rule.id
        assert response.data['status'] == 'pending'
        assert response.data['created_at'] is not None

    def test_create_report_with_invalid_rule(self, client, user):
        community = CommunityFactory()
        rule = RuleFactory()
        MemberFactory(user=user, community=community, is_moderator=True)
        post = PostFactory(community=community)
        comment = CommentFactory(post=post)
        url = reverse('comment-report-list')
        data = {
            'comment': comment.id,
            'reason': 'test_reason',
            'violated_rule': rule.id
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_report_with_pending_report(self, client, user):
        community = CommunityFactory()
        rule = RuleFactory(community=community)
        MemberFactory(user=user, community=community, is_moderator=True)
        post = PostFactory(community=community)
        comment = CommentFactory(post=post)
        CommentReportFactory(user=user, comment=comment, status='pending')
        url = reverse('comment-report-list')
        data = {
            'comment': comment.id,
            'reason': 'test_reason',
            'violated_rule': rule.id
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_report_for_own_comment(self, client, user):
        community = CommunityFactory()
        rule = RuleFactory(community=community)
        MemberFactory(user=user, community=community, is_moderator=True)
        post = PostFactory(community=community)
        comment = CommentFactory(post=post, user=user)
        url = reverse('comment-report-list')
        data = {
            'comment': comment.id,
            'reason': 'test_reason',
            'violated_rule': rule.id
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestCommentReportDetailView:

    def test_get_report_if_not_moderator(self, client):
        report = CommentReportFactory()
        url = reverse('comment-report-detail', args=[report.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_report_if_moderator(self, client, user):
        community = CommunityFactory()
        post = PostFactory(community=community)
        comment = CommentFactory(post=post)
        MemberFactory(user=user, community=community, is_moderator=True)
        report = CommentReportFactory(comment=comment)
        url = reverse('comment-report-detail', args=[report.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == report.id
        assert response.data['comment']['id'] == report.comment.id
        assert response.data['user']['id'] == report.user.id
        assert response.data['reason'] == report.reason
        assert response.data['violated_rule']['id'] == report.violated_rule.id
        assert response.data['status'] == report.status
        assert response.data['created_at'] is not None

    def test_update_report_if_not_moderator(self, client):
        report = CommentReportFactory()
        url = reverse('comment-report-detail', args=[report.id])
        data = {'status': 'dismissed'}
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_report(self, client, user):
        community = CommunityFactory()
        post = PostFactory(community=community)
        comment = CommentFactory(post=post)
        MemberFactory(user=user, community=community, is_moderator=True)
        report = CommentReportFactory(comment=comment)
        url = reverse('comment-report-detail', args=[report.id])
        data = {'status': 'dismissed'}
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'dismissed'

    def test_delete_report_if_not_moderator(self, client):
        report = CommentReportFactory()
        url = reverse('comment-report-detail', args=[report.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_report(self, client, user):
        community = CommunityFactory()
        post = PostFactory(community=community)
        comment = CommentFactory(post=post)
        MemberFactory(user=user, community=community, is_moderator=True)
        report = CommentReportFactory(comment=comment)
        url = reverse('comment-report-detail', args=[report.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

@pytest.mark.django_db
class TestUserUpvotedCommentsView:

    def test_get_upvoted_comments(self, client, user):
        comment = CommentFactory(user=user)
        CommentInteractionFactory(comment=comment, user=user, interaction_type='upvote')
        url = reverse('user-upvoted-comments')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_other_users_upvoted_comments(self, client, user):
        comment = CommentFactory(user=user)
        user2 = UserFactory()
        CommentInteractionFactory(comment=comment, user=user2, interaction_type='upvote')
        url = reverse('user-upvoted-comments')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

@pytest.mark.django_db
class TestUserDownvotedCommentsView:

    def test_get_downvoted_comments(self, client, user):
        comment = CommentFactory(user=user)
        CommentInteractionFactory(comment=comment, user=user, interaction_type='downvote')
        url = reverse('user-downvoted-comments')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_other_users_downvoted_comments(self, client, user):
        comment = CommentFactory(user=user)
        user2 = UserFactory()
        CommentInteractionFactory(comment=comment, user=user2, interaction_type='downvote')
        url = reverse('user-downvoted-comments')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0