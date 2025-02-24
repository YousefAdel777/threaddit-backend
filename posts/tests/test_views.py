import pytest
from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status
from .factories import (
    UserFactory,
    PostFactory,
    BlockFactory,
    BanFactory,
    MemberFactory,
    PostInteractionFactory,
    CommentFactory,
    CommunityFactory,
    SavedPostFactory
)

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
class TestPostListCreateView:
    def test_get_posts(self, client):
        PostFactory(type='text', content='test_content')
        url = reverse('post-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
    
    def test_get_posts_from_blocked_user(self, client, user):
        user2 = UserFactory()
        BlockFactory(blocked_by=user, blocked_user=user2)
        PostFactory(type='text', content='test_content', user=user2)
        url = reverse('post-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_get_posts_with_banned_user(self, client, user):
        community = CommunityFactory()
        BanFactory(user=user, community=community)
        PostFactory(type='text', content='test_content', community=community)
        url = reverse('post-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_create_post(self, client, user):
        url = reverse('post-list')
        data = {'type': 'text', 'title': 'test_title', 'content': 'test_content'}
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['id'] == 1
        assert response.data['type'] == 'text'
        assert response.data['content'] == 'test_content'
        assert response.data['user']['id'] == user.id
        assert response.data['title'] == 'test_title'
        assert response.data['community'] is None
        assert response.data['created_at'] is not None

    def test_create_post_with_banned_user(self, client, user):
        community = CommunityFactory()
        BanFactory(user=user, community=community)
        url = reverse('post-list')
        data = {'type': 'text', 'title': 'test_title', 'content': 'test_content', 'community': community.id}
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_crosspost(self, client, user):
        post = PostFactory(type='text', content='test_content', user=user)
        url = reverse('post-list')
        data = {
            'type': 'crosspost',
            'title': 'test_title',
            'original_post': post.id
        }
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['type'] == 'crosspost'
        assert response.data['user']['id'] == user.id
        assert response.data['title'] == 'test_title'
        assert response.data['original_post']['id'] == post.id

    def test_crosspost_with_nsfw_original_post(self, client, user):
        post = PostFactory(type='text', content='test_content', user=user, is_nsfw=True)
        url = reverse('post-list')
        data = {
            'type': 'crosspost',
            'title': 'test_title',
            'original_post': post.id
        }
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['is_nsfw']

    def test_crosspost_from_blocked_user(self, client, user):        
        user2 = UserFactory()
        BlockFactory(blocked_by=user, blocked_user=user2)
        post = PostFactory(type='text', content='test_content', user=user2)
        url = reverse('post-list')
        data = {
            'type': 'crosspost',
            'title': 'test_title',
            'content': 'test_content',
            'original_post': post.id
        }
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_crosspost_with_banned_user(self, client, user):
        community = CommunityFactory()
        BanFactory(user=user, community=community)
        post = PostFactory(type='text', content='test_content', user=user)
        url = reverse('post-list')
        data = {
            'type': 'crosspost',
            'title': 'test_title',
            'content': 'test_content',
            'original_post': post.id,
            'community': community.id
        }
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestPostDetailView:

    def test_get_post(self, client):
        post = PostFactory()
        PostInteractionFactory(post=post, interaction_type='upvote')
        CommentFactory(post=post)
        url = reverse('post-detail', args=[post.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == post.id
        assert response.data['user']['id'] == post.user.id
        assert response.data['type'] == post.type
        assert response.data['content'] == post.content
        assert response.data['title'] == post.title
        assert response.data['community']['id'] == post.community.id
        assert response.data['status'] == post.status
        assert response.data['is_nsfw'] == post.is_nsfw
        assert response.data['is_spoiler'] == post.is_spoiler
        assert response.data['created_at'] is not None
        assert response.data['interaction_diff'] == 1
        assert response.data['comments_count'] == 1

    def test_get_post_with_invalid_id(self, client):
        url = reverse('post-detail', args=[999])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_post_with_blocked_user(self, client, user):
        user2 = UserFactory()
        BlockFactory(blocked_by=user, blocked_user=user2)
        post = PostFactory(user=user2)
        url = reverse('post-detail', args=[post.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_post_with_banned_user(self, client, user):
        community = CommunityFactory()
        BanFactory(user=user, community=community)
        post = PostFactory(community=community)
        url = reverse('post-detail', args=[post.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_post_if_author(self, client, user):
        post = PostFactory(type='text', content='test_content', user=user)
        url = reverse('post-detail', args=[post.id])
        data = { 'content': 'test_content_updated'}
        response = client.patch(url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == 1
        assert response.data['type'] == 'text'
        assert response.data['content'] == 'test_content_updated'
        assert response.data['user']['id'] == user.id

    def test_update_post_if_not_author(self, client, user):
        post = PostFactory(type='text', content='test_content')
        url = reverse('post-detail', args=[post.id])
        data = { 'content': 'test_content_updated'}
        response = client.put(url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_post_if_moderator_with_invalid_data(self, client, user):
        community = CommunityFactory()
        user2 = UserFactory()
        MemberFactory(user=user, community=community, is_moderator=True)
        post = PostFactory(user=user2, type='text', content='test_content', community=community)
        url = reverse('post-detail', args=[post.id])
        data = { 'content': 'test_content_updated' }
        response = client.patch(url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_post_status_if_moderator(self, client, user):
        community = CommunityFactory()
        user2 = UserFactory()
        MemberFactory(user=user, community=community, is_moderator=True)
        post = PostFactory(user=user2, type='text', content='test_content', community=community, status='pending')
        url = reverse('post-detail', args=[post.id])
        data = { 'status': 'accepted' }
        response = client.patch(url, data=data)
        assert response.status_code == status.HTTP_200_OK

    def test_delete_post_if_author(self, client, user):
        post = PostFactory(type='text', content='test_content', user=user)
        url = reverse('post-detail', args=[post.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_post_if_not_author(self, client):
        post = PostFactory(type='text', content='test_content')
        url = reverse('post-detail', args=[post.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_post_if_moderator(self, client, user):
        community = CommunityFactory()
        user2 = UserFactory()
        MemberFactory(user=user, community=community, is_moderator=True)
        post = PostFactory(user=user2, type='text', content='test_content', community=community)
        url = reverse('post-detail', args=[post.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestSavedPostListCreateView:
    def test_create_saved_post(self, client):
        post = PostFactory(type='text', content='test_content')
        url = reverse('saved-post-list')
        data = {'post': post.id}
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_get_saved_posts(self, client, user):
        post = PostFactory(type='text', content='test_content', user=user)
        SavedPostFactory(user=user, post=post)
        url = reverse('saved-post-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_other_user_saved_posts(self, client, user):
        user2 = UserFactory()
        post = PostFactory(type='text', content='test_content')
        SavedPostFactory(post=post, user=user2)
        url = reverse('saved-post-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

@pytest.mark.django_db
class TestSavedPostDetailView:
    def test_get_saved_post(self, client, user):
        post = PostFactory(type='text', content='test_content')
        saved_post = SavedPostFactory(post=post, user=user)
        url = reverse('saved-post-detail', args=[saved_post.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_get_invalid_saved_post(self, client):
        url = reverse('saved-post-detail', args=[999])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_other_user_saved_post(self, client):
        user2 = UserFactory()
        post = PostFactory(type='text', content='test_content')
        saved_post = SavedPostFactory(post=post, user=user2)
        url = reverse('saved-post-detail', args=[saved_post.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_saved_post(self, client, user):
        post = PostFactory(type='text', content='test_content')
        SavedPostFactory(user=user, post=post)
        url = reverse('saved-post-detail', args=[post.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_invalid_saved_post(self, client):
        url = reverse('saved-post-detail', args=[999])
        response = client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_other_user_saved_post(self, client):
        user2 = UserFactory()
        post = PostFactory(type='text', content='test_content')
        SavedPostFactory(user=user2, post=post)
        url = reverse('saved-post-detail', args=[post.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
class TestUserSavedPostsView:
    def test_get_user_saved_posts(self, client, user):
        post = PostFactory(type='text', content='test_content')
        SavedPostFactory(user=user, post=post)
        url = reverse('user-saved-posts')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
    
    def test_get_other_user_saved_posts(self, client, user):
        user2 = UserFactory()
        post = PostFactory(type='text', content='test_content')
        SavedPostFactory(user=user2, post=post)
        url = reverse('user-saved-posts')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0
    
    def test_get_user_saved_posts_with_blocked_user(self, client, user):
        user2 = UserFactory()
        BlockFactory(blocked_by=user, blocked_user=user2)
        post = PostFactory(type='text', content='test_content', user=user2)
        SavedPostFactory(user=user2, post=post)
        url = reverse('user-saved-posts')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_get_user_saved_posts_with_banned_user(self, client, user):
        user2 = UserFactory()
        community = CommunityFactory()
        BanFactory(user=user, community=community)
        post = PostFactory(type='text', content='test_content', user=user2)
        SavedPostFactory(user=user2, post=post)
        url = reverse('user-saved-posts')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

@pytest.mark.django_db
class TestPostInteractionListCreateView:
    def test_get_post_interactions(self, client, user):
        post = PostFactory(type='text', content='test_content')
        PostInteractionFactory(post=post, user=user)
        url = reverse('post-interaction-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_other_user_post_interactions(self, client):
        user2 = UserFactory()
        post = PostFactory(type='text', content='test_content')
        PostInteractionFactory(user=user2, post=post)
        url = reverse('post-interaction-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_create_post_interaction(self, client):
        post = PostFactory(type='text', content='test_content')
        url = reverse('post-interaction-list')
        data = {'post': post.id, 'interaction_type': 'upvote'}
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['interaction_type'] == 'upvote'
        assert response.data['post'] == post.id

    def test_create_post_interaction_with_blocked_user(self, client, user):
        url = reverse('post-interaction-list')
        user2 = UserFactory()
        BlockFactory(blocked_by=user2, blocked_user=user)
        post = PostFactory(type='text', content='test_content', user=user2)
        data = {'post': post.id, 'interaction_type': 'upvote'}
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_post_interaction_with_banned_user(self, client, user):
        url = reverse('post-interaction-list')
        community = CommunityFactory()
        BanFactory(user=user, community=community)
        post = PostFactory(type='text', content='test_content', community=community)
        data = {'post': post.id, 'interaction_type': 'upvote'}
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestPostInteractionDetailView:
    def test_get_post_interaction(self, client, user):
        post = PostFactory(type='text', content='test_content')
        post_interaction = PostInteractionFactory(post=post, user=user)
        url = reverse('post-interaction-detail', args=[post_interaction.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
    
    def test_invalid_post_interaction(self, client):
        url = reverse('post-interaction-detail', args=[999])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_other_user_post_interaction(self, client):
        user2 = UserFactory()
        post = PostFactory(type='text', content='test_content')
        post_interaction = PostInteractionFactory(user=user2, post=post)
        url = reverse('post-interaction-detail', args=[post_interaction.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_post_interaction(self, client, user):
        post = PostFactory(type='text', content='test_content')
        post_interaction = PostInteractionFactory(post=post, user=user)
        url = reverse('post-interaction-detail', args=[post_interaction.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_other_user_post_interaction(self, client):
        user2 = UserFactory()
        post = PostFactory(type='text', content='test_content')
        post_interaction = PostInteractionFactory(user=user2, post=post)
        url = reverse('post-interaction-detail', args=[post_interaction.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_post_interaction(self, client, user):
        post = PostFactory(type='text', content='test_content')
        post_interaction = PostInteractionFactory(post=post, user=user, interaction_type='upvote')
        url = reverse('post-interaction-detail', args=[post_interaction.id])
        data = {'interaction_type': 'downvote'}
        response = client.patch(url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['interaction_type'] == 'downvote'

    def test_update_other_user_post_interaction(self, client):
        user2 = UserFactory()
        post = PostFactory(type='text', content='test_content')
        post_interaction = PostInteractionFactory(user=user2, post=post)
        url = reverse('post-interaction-detail', args=[post_interaction.id])
        data = {'interaction_type': 'downvote'}
        response = client.patch(url, data=data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_invalid_post_interaction(self, client):
        url = reverse('post-interaction-detail', args=[999])
        data = {'interaction_type': 'downvote'}
        response = client.patch(url, data=data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
class TestFeedView:
    pass

@pytest.mark.django_db
class TestPopularView:
    pass

@pytest.mark.django_db
class TestUserUpvotedPostsView:
    def test_get_current_user_upvoted_posts(self, client, user):
        post = PostFactory()
        PostInteractionFactory(post=post, user=user, interaction_type='upvote')
        url = reverse('user-upvoted-posts')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_other_user_upvoted_posts(self, client):
        user2 = UserFactory()
        post = PostFactory()
        PostInteractionFactory(post=post, user=user2, interaction_type='upvote')
        url = reverse('user-upvoted-posts')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

@pytest.mark.django_db
class TestUserDownvotedPostsView:
    def test_get_current_user_downvoted_posts(self, client, user):
        post = PostFactory()
        PostInteractionFactory(post=post, user=user, interaction_type='downvote')
        url = reverse('user-downvoted-posts')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_other_user_downvoted_posts(self, client):
        user2 = UserFactory()
        post = PostFactory()
        PostInteractionFactory(post=post, user=user2, interaction_type='downvote')
        url = reverse('user-downvoted-posts')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0