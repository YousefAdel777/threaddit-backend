import pytest
from rest_framework.test import APIClient
from rest_framework import status
from .utils import create_temp_image_file
from django.urls import reverse
from django.utils import timezone
from .factories import (
    UserFactory,
    CommunityFactory, 
    RuleFactory, 
    TopicFactory, 
    MemberFactory, 
    FavoriteFactory, 
    BanFactory
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
class TestCommunityListCreateView:
    def test_create_community(self, client, user):
        url = reverse('community-list-create')
        banner = create_temp_image_file()
        icon = create_temp_image_file()
        topic = TopicFactory()
        data = {
            'name': 'test_name',
            'description': 'test_description',
            'icon': icon,
            'banner': banner,
            'topics': [topic.id],
        }
        response = client.post(url, data, format='multipart')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'test_name'
        assert response.data['user']['id'] == user.id
        assert icon.name in response.data['icon']
        assert banner.name in response.data['banner']
        assert response.data['description'] == 'test_description'
        assert response.data['created_at'] is not None
        assert response.data['member_id'] is not None
        assert response.data['members_count'] == 1
        assert len(response.data['moderators']) == 1
        assert response.data['is_creator']
        assert response.data['is_moderator']
        assert response.data['topics'][0]['id'] == topic.id
    
    def test_get_communities(self, client, user):
        CommunityFactory()
        url = reverse('community-list-create')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_filters_communities_if_user_is_banned(self, client, user):
        community = CommunityFactory()
        BanFactory(user=user, community=community)
        url = reverse('community-list-create')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

@pytest.mark.django_db
class TestCommunityDetailView:
    def test_get_community(self, client, user):
        community = CommunityFactory()
        url = reverse('community-detail', args=[community.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == community.name

    def test_get_community_if_user_is_banned(self, client, user):
        community = CommunityFactory()
        BanFactory(user=user, community=community)
        url = reverse('community-detail', args=[community.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_community(self, client, user):
        community = CommunityFactory(user=user)
        MemberFactory(user=user, community=community, is_moderator=True)
        url = reverse('community-detail', args=[community.id])
        data = {
            'name': 'new_name',
            'description': 'new_description',
        }
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'new_name'
        assert response.data['description'] == 'new_description'

    def test_cannot_update_community_if_not_moderator(self, client, user):
        community = CommunityFactory()
        url = reverse('community-detail', args=[community.id])
        data = {
            'name': 'new_name',
            'description': 'new_description',
        }
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_community(self, client, user):
        community = CommunityFactory(user=user)
        MemberFactory(user=user, community=community, is_moderator=True)
        url = reverse('community-detail', args=[community.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_community_if_not_moderator(self, client, user):
        community = CommunityFactory()
        url = reverse('community-detail', args=[community.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestUserCommunitiesView:
    def test_get_user_communities(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community)
        url = reverse('user-communities')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_user_communities_if_user_is_banned(self, client, user):
        community = CommunityFactory(user=user)
        MemberFactory(user=user, community=community)
        BanFactory(user=user, community=community)
        url = reverse('user-communities')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

@pytest.mark.django_db
class TestUserModeratedCommunitiesView:
    def test_get_user_moderated_communities(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=True)
        url = reverse('user-moderated-communities')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_user_moderated_communities_if_user_is_not_moderator(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=False)
        url = reverse('user-moderated-communities')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

@pytest.mark.django_db
class TestTopicViewset:

    def test_get_topics(self, client):
        TopicFactory()
        url = reverse('topics-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_get_topic(self, client):
        topic = TopicFactory()
        url = reverse('topics-detail', args=[topic.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_create_topic(self, client):
        user = UserFactory(is_staff=True)
        print(user.is_staff)
        client.force_authenticate(user=user)
        url = reverse('topics-list')
        data = {
            'name': 'test_name',
            'description': 'test_description',
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_create_topic_if_user_is_not_superuser(self, client):
        user = UserFactory(is_staff=False)
        client.force_authenticate(user=user)
        url = reverse('topics-list')
        data = {
            'name': 'test_name',
            'description': 'test_description',
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_topic(self, client):
        topic = TopicFactory()
        user = UserFactory(is_staff=True)
        client.force_authenticate(user=user)
        url = reverse('topics-detail', args=[topic.id])
        data = {
            'name': 'new_name',
            'description': 'new_description',
        }
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'new_name'
        assert response.data['description'] == 'new_description'

    def test_update_topic_if_user_is_not_superuser(self, client):
        topic = TopicFactory()
        url = reverse('topics-detail', args=[topic.id])
        data = {
            'name': 'new_name',
            'description': 'new_description',
        }
        user = UserFactory(is_staff=False)
        client.force_authenticate(user=user)
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_topic(self, client):
        topic = TopicFactory()
        user = UserFactory(is_staff=True)
        client.force_authenticate(user=user)
        url = reverse('topics-detail', args=[topic.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_topic_if_user_is_not_superuser(self, client):
        topic = TopicFactory()
        url = reverse('topics-detail', args=[topic.id])
        user = UserFactory(is_staff=False)
        client.force_authenticate(user=user)
        response = client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestMemberListCreateView:
    def test_create_member(self, client, user):
        community = CommunityFactory()
        url = reverse('member-list-create')
        response = client.post(url, {'user': user.id, 'community': community.id})
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_create_member_with_banned_user(self, client, user):
        community = CommunityFactory()
        BanFactory(user=user, community=community)
        url = reverse('member-list-create')
        response = client.post(url, {'user': user.id, 'community': community.id})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_member_with_existing_member(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community)
        url = reverse('member-list-create')
        response = client.post(url, {'user': user.id, 'community': community.id})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_members_if_user_is_moderator(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=True)
        MemberFactory(community=community)
        url = reverse('member-list-create')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
    
    def test_get_members_if_user_not_moderator(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=False)
        MemberFactory(community=community)
        url = reverse('member-list-create')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
    
    def test_get_members_if_user_not_member(self, client, user):
        url = reverse('member-list-create')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

@pytest.mark.django_db
class TestMemberDetailView:

    def test_get_member(self, client, user):
        community = CommunityFactory()
        member = MemberFactory(user=user, community=community)
        url = reverse('member-detail', args=[member.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_get_other_member_if_user_is_moderator(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=True)
        member = MemberFactory(community=community)
        url = reverse('member-detail', args=[member.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_get_other_member_if_user_is_not_moderator(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=False)
        member = MemberFactory(community=community)
        url = reverse('member-detail', args=[member.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_other_member_if_user_is_not_member(self, client, user):
        community = CommunityFactory()
        member = MemberFactory(community=community)
        url = reverse('member-detail', args=[member.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_member_if_user_is_moderator(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=True)
        member = MemberFactory(community=community, is_moderator=False)
        url = reverse('member-detail', args=[member.id])
        data = {
            'is_moderator': True,
        }
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
    
    def test_update_member_if_user_is_not_moderator(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=False)
        member = MemberFactory(community=community, is_moderator=False)
        url = reverse('member-detail', args=[member.id])
        data = {
            'is_moderator': True,
        }
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_member_if_user_is_moderator(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=True)
        member = MemberFactory(community=community, is_moderator=False)
        url = reverse('member-detail', args=[member.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_delete_member_if_user_is_not_moderator(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=False)
        member = MemberFactory(community=community, is_moderator=False)
        url = reverse('member-detail', args=[member.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
class TestFavoriteListCreateView:
    def test_create_favorite(self, client, user):
        community = CommunityFactory()
        url = reverse('favorite-list-create')
        response = client.post(url, {'user': user.id, 'community': community.id})
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_favorite_with_existing_favorite(self, client, user):
        community = CommunityFactory()
        FavoriteFactory(user=user, community=community)
        url = reverse('favorite-list-create')
        response = client.post(url, {'user': user.id, 'community': community.id})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_favorite_with_banned_user(self, client, user):
        community = CommunityFactory()
        BanFactory(user=user, community=community)
        url = reverse('favorite-list-create')
        response = client.post(url, {'user': user.id, 'community': community.id})
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_favorites(self, client, user):
        community = CommunityFactory()
        FavoriteFactory(user=user, community=community)
        url = reverse('favorite-list-create')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
    
    def test_get_favorites_if_user_is_banned(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community)
        FavoriteFactory(community=community)
        BanFactory(user=user, community=community)
        url = reverse('favorite-list-create')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

@pytest.mark.django_db
class TestFavoriteDetailView:
    def test_get_favorite(self, client, user):
        community = CommunityFactory()
        favorite = FavoriteFactory(user=user, community=community)
        url = reverse('favorite-detail', args=[favorite.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_get_other_user_favorite(self, client):
        community = CommunityFactory()
        favorite = FavoriteFactory(community=community)
        url = reverse('favorite-detail', args=[favorite.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_favorite_if_user_is_banned(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community)
        favorite = FavoriteFactory(community=community)
        BanFactory(user=user, community=community)
        url = reverse('favorite-detail', args=[favorite.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_favorite(self, client, user):
        community = CommunityFactory()
        favorite = FavoriteFactory(user=user, community=community)
        url = reverse('favorite-detail', args=[favorite.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_favorite_if_user_is_banned(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community)
        favorite = FavoriteFactory(community=community)
        BanFactory(user=user, community=community)
        url = reverse('favorite-detail', args=[favorite.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
class TestRuleListCreateView:
    def test_get_rules(self, client):
        community = CommunityFactory()
        RuleFactory(community=community)
        url = reverse('rule-list-create')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
    
    def test_get_rules_if_user_is_banned(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community)
        RuleFactory(community=community)
        BanFactory(user=user, community=community)
        url = reverse('rule-list-create')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0
    
    def test_create_rule(self, client, user):
        community = CommunityFactory(user=user)
        MemberFactory(user=user, community=community, is_moderator=True)
        url = reverse('rule-list-create')
        data = {
            'community': community.id,
            'title': 'test_title',
            'description': 'test_description',
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'test_title'
        assert response.data['community'] == community.id
        assert response.data['description'] == 'test_description'
    
    def test_create_rule_if_user_is_not_moderator(self, client, user):
        community = CommunityFactory(user=user)
        MemberFactory(user=user, community=community, is_moderator=False)
        url = reverse('rule-list-create')
        data = {
            'community': community.id,
            'name': 'test_name',
            'description': 'test_description',
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestRuleDetailView:
    def test_get_rule(self, client):
        community = CommunityFactory()
        rule = RuleFactory(community=community)
        url = reverse('rule-detail', args=[rule.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == rule.id
        assert response.data['community'] == community.id
        assert response.data['title'] == rule.title
        assert response.data['description'] == rule.description
        assert response.data['created_at'] is not None

    def test_get_rule_if_user_is_banned(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community)
        rule = RuleFactory(community=community)
        BanFactory(user=user, community=community)
        url = reverse('rule-detail', args=[rule.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_rule(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=True)
        rule = RuleFactory(community=community)
        url = reverse('rule-detail', args=[rule.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_rule_if_user_is_not_moderator(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=False)
        rule = RuleFactory(community=community)
        url = reverse('rule-detail', args=[rule.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_rule(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=True)
        rule = RuleFactory(community=community)
        url = reverse('rule-detail', args=[rule.id])
        data = {
            'name': 'new_name',
            'description': 'new_description',
        }
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK

    def test_update_rule_if_user_is_not_moderator(self, client, user):
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=False)
        rule = RuleFactory(community=community)
        url = reverse('rule-detail', args=[rule.id])
        data = {
            'name': 'new_name',
            'description': 'new_description',
        }
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestBanListCreateView:
    def test_get_bans(self, client, user):
        community = CommunityFactory(user=user)
        MemberFactory(user=user, community=community, is_moderator=True)
        BanFactory(community=community)
        url = reverse('ban-list-create')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_bans_if_user_is_not_moderator(self, client, user):
        community = CommunityFactory(user=user)
        MemberFactory(user=user, community=community, is_moderator=False)
        url = reverse('ban-list-create')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_get_bans_if_user_is_banned(self, client, user):
        community = CommunityFactory(user=user)
        MemberFactory(user=user, community=community, is_moderator=False)
        BanFactory(user=user, community=community)
        url = reverse('ban-list-create')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_ban(self, client, user):
        community = CommunityFactory(user=user)
        MemberFactory(user=user, community=community, is_moderator=True)
        user2 = UserFactory()
        BanFactory(community=community)
        url = reverse('ban-list-create')
        data = {
            'user': user2.id,
            'community': community.id,
            'is_permanent': True,
            'reason': 'test_reason',
        }
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['user'] == user2.id
        assert response.data['community'] == community.id
        assert response.data['is_permanent']
        assert response.data['reason'] == 'test_reason'
        assert response.data['banned_at'] is not None
        assert response.data['expires_at'] is None
        assert response.data['is_active']

    def test_create_ban_if_user_is_not_moderator(self, client, user):
        community = CommunityFactory(user=user)
        MemberFactory(user=user, community=community, is_moderator=False)
        user2 = UserFactory()
        url = reverse('ban-list-create')
        data = {
            'user': user2.id,
            'community': community.id,
            'is_permanent': True,
            'reason': 'test_reason',
        }
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_ban_for_moderator(self, client, user):
        community = CommunityFactory(user=user)
        MemberFactory(user=user, community=community, is_moderator=True)
        user2 = UserFactory()
        MemberFactory(user=user2, community=community, is_moderator=True)
        url = reverse('ban-list-create')
        data = {
            'user': user2.id,
            'community': community.id,
            'is_permanent': True,
            'reason': 'test_reason',
        }
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_ban_if_user_is_banned(self, client, user):
        community = CommunityFactory(user=user)
        MemberFactory(user=user, community=community, is_moderator=True)
        user2 = UserFactory()
        BanFactory(user=user2, community=community)
        url = reverse('ban-list-create')
        data = {
            'user': user2.id,
            'community': community.id,
            'is_permanent': True,
            'reason': 'test_reason',
        }
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_ban(self, client, user):
        community = CommunityFactory(user=user)
        MemberFactory(user=user, community=community, is_moderator=True)
        user2 = UserFactory()
        ban = BanFactory(user=user2, community=community)
        url = reverse('ban-detail', args=[ban.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_delete_ban_if_user_is_not_moderator(self, client, user):
        community = CommunityFactory(user=user)
        MemberFactory(user=user, community=community, is_moderator=False)
        user2 = UserFactory()
        ban = BanFactory(user=user2, community=community)
        url = reverse('ban-detail', args=[ban.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_ban(self, client, user):
        community = CommunityFactory(user=user)
        MemberFactory(user=user, community=community, is_moderator=True)
        user2 = UserFactory()
        ban = BanFactory(user=user2, community=community, is_permanent=True, expires_at=None)
        url = reverse('ban-detail', args=[ban.id])
        data = {
            'is_permanent': False,
            'expires_at': timezone.now() + timezone.timedelta(days=1),
        }
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_permanent'] is False
        assert response.data['expires_at'] is not None
    
    def test_update_ban_if_user_is_not_moderator(self, client, user):
        community = CommunityFactory(user=user)
        MemberFactory(user=user, community=community, is_moderator=False)
        user2 = UserFactory()
        ban = BanFactory(user=user2, community=community, is_permanent=True, expires_at=None)
        url = reverse('ban-detail', args=[ban.id])
        data = {
            'is_permanent': False,
            'expires_at': timezone.now() + timezone.timedelta(days=1),
        }
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_404_NOT_FOUND