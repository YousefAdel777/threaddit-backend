import pytest
from rest_framework.test import APIRequestFactory
from communities.serializers import (
    CommunityReadSerializer,
    CommunityWriteSerializer,
    RuleSerializer,
    BanSerializer,
    FavoriteSerializer,
    TopicSerializer,
    MemberReadSerializer,
    MemberWriteSerializer,
)
from django.utils import timezone
from .utils import create_temp_image_file
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
def serializer_context():
    user = UserFactory()
    request = APIRequestFactory().get('/')
    request.user = user
    return {'request': request}

@pytest.mark.django_db
class TestCommunityWriteSerializer:

    def test_valid_community_serializer(self):
        user = UserFactory()
        topic = TopicFactory()
        icon = create_temp_image_file()
        banner = create_temp_image_file()
        data = {
            'name': 'test_name',
            'description': 'test_description',
            'icon': icon,
            'banner': banner,
            'user': user.id,
            'topics': [topic.id]
        }
        serializer = CommunityWriteSerializer(data=data)
        assert serializer.is_valid()
        community = serializer.save()
        assert community.name == 'test_name'
        assert community.description == 'test_description'
        assert icon.name in community.icon.name
        assert banner.name in community.banner.name
        assert community.user == user
        assert list(community.topics.all()) == [topic]

    def test_unique_community_name(self):
        user = UserFactory()
        CommunityFactory(name='test_name')
        data = {
            'name': 'test_name',
            'description': 'test_description',
            'icon': 'test_icon.png',
            'banner': 'test_banner.png',
            'user': user.id
        }
        serializer = CommunityWriteSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'name' in serializer.errors

    def test_max_topics_count(self):
        user = UserFactory()
        topics = [TopicFactory().id for _ in range(4)]
        data = {
            'name': 'test_name',
            'description': 'test_description',
            'user': user.id,
            'topics': topics
        }
        serializer = CommunityWriteSerializer(data=data)
        assert serializer.is_valid() is False
        assert serializer.errors == {'topics': ['Topics cannot exceed 3']}

@pytest.mark.django_db
class TestCommunityReadSerializer:
    def test_community_read_serializer_fields(self, serializer_context):
        user = serializer_context['request'].user
        community = CommunityFactory(user=user)
        rule = RuleFactory(community=community)
        favorite = FavoriteFactory(user=user, community=community)
        member = MemberFactory(user=user, community=community, is_moderator=True)
        serializer = CommunityReadSerializer(community, context=serializer_context)
        assert serializer.data['id'] == community.id
        assert serializer.data['user']['id'] == user.id
        assert serializer.data['name'] == community.name
        assert serializer.data['favorite_id'] == favorite.id
        assert serializer.data['moderators'][0]['id'] == member.id
        assert serializer.data['member_id'] == member.id
        assert serializer.data['is_creator']
        assert serializer.data['is_moderator']
        assert serializer.data['members_count'] == 1
        assert serializer.data['rules'][0]['id'] == rule.id
        assert serializer.data['description'] == community.description
        assert serializer.data['topics'][0]['id'] == community.topics.first().id
        assert community.icon.url in serializer.data['icon']
        assert community.banner.url in serializer.data['banner']

@pytest.mark.django_db
class TestTopicSerializer:
    def test_valid_rule_serializer(self):
        user = UserFactory()
        data = {
            'name': 'test_name',
            'description': 'test_description',
        }
        serializer = TopicSerializer(data=data)
        assert serializer.is_valid()
        topic = serializer.save()
        assert topic.name == 'test_name'
        assert topic.description == 'test_description'
    
    def test_rule_serializer_fields(self):
        topic = TopicFactory(name='test_name', description='test_description')
        serializer = TopicSerializer(topic)
        assert serializer.data['id'] == topic.id
        assert serializer.data['name'] == topic.name
        assert serializer.data['description'] == topic.description

@pytest.mark.django_db
class TestRuleSerializer:
    def test_valid_rule_serializer(self):
        community = CommunityFactory()        
        data = {
            'title': 'test_title',
            'description': 'test_description',
            'community': community.id
        }
        serializer = RuleSerializer(data=data)
        assert serializer.is_valid()
        rule = serializer.save()
        assert rule.title == 'test_title'
        assert rule.description == 'test_description'
        assert rule.community == community

    def test_rule_serializer_fields(self):
        rule = RuleFactory(title='test_title', description='test_description')
        serializer = RuleSerializer(rule)
        assert serializer.data['id'] == rule.id
        assert serializer.data['title'] == rule.title
        assert serializer.data['description'] == rule.description

@pytest.mark.django_db
class TestBanSerializer:
    def test_valid_ban_serializer(self):
        user = UserFactory()
        community = CommunityFactory()
        data = {
            'user': user.id,
            'community': community.id,
            'reason': 'test_reason',
            'is_permanent': True
        }
        serializer = BanSerializer(data=data)
        assert serializer.is_valid()
        ban = serializer.save()
        assert ban.user == user
        assert ban.community == community
        assert ban.reason == 'test_reason'
        assert ban.is_permanent
        assert ban.expires_at is None

    def test_ban_serializer_fields(self):
        user = UserFactory()
        community = CommunityFactory()
        ban = BanFactory(user=user, community=community, reason='test_reason', is_permanent=True)
        serializer = BanSerializer(ban)
        assert serializer.data['id'] == ban.id
        assert serializer.data['user'] == ban.user.id
        assert serializer.data['community'] == ban.community.id
        assert serializer.data['reason'] == ban.reason
        assert serializer.data['is_permanent'] == ban.is_permanent
        assert serializer.data['expires_at'] is None
        assert serializer.data['banned_at'] is not None
        assert serializer.data['is_active']
    
    def test_ban_serializer_with_expires_at_and_is_permanent(self):
        user = UserFactory()
        community = CommunityFactory()
        expires_at = timezone.now() + timezone.timedelta(days=1)
        data = {
            'user': user.id,
            'community': community.id,
            'reason': 'test_reason',
            'is_permanent': True,
            'expires_at': expires_at
        }
        serializer = BanSerializer(data=data)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['Permanent bans cannot have an expiration date']}
    
    def test_ban_serializer_with_expires_at_none_and_not_permanent(self):
        user = UserFactory()
        community = CommunityFactory()
        data = {
            'user': user.id,
            'community': community.id,
            'reason': 'test_reason',
            'is_permanent': False,
            'expires_at': None
        }
        serializer = BanSerializer(data=data)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['Temporary bans must have an expiration date']}
    
    def test_ban_serializer_with_invalid_expires_at(self):
        user = UserFactory()
        community = CommunityFactory()
        expires_at = timezone.now() - timezone.timedelta(days=1)
        data = {
            'user': user.id,
            'community': community.id,
            'reason': 'test_reason',
            'is_permanent': False,
            'expires_at': expires_at
        }
        serializer = BanSerializer(data=data)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['Ban expiration date cannot be in the past']}

    def test_ban_serializer_unique_user_with_active_ban(self):
        user = UserFactory()
        community = CommunityFactory()
        BanFactory(user=user, community=community, is_permanent=True)
        data = {
            'user': user.id,
            'community': community.id,
            'reason': 'test_reason',
            'is_permanent': True
        }
        serializer = BanSerializer(data=data)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['User is already banned in this community']}

@pytest.mark.django_db
class TestFavoriteSerializer:
    def test_valid_favorite_serializer(self):
        user = UserFactory()
        community = CommunityFactory()
        data = {
            'user': user.id,
            'community': community.id
        }
        serializer = FavoriteSerializer(data=data)
        assert serializer.is_valid()
        favorite = serializer.save()
        assert favorite.user == user
        assert favorite.community == community
    
    def test_favorite_serializer_unique_user_community_constraint(self):
        user = UserFactory()
        community = CommunityFactory()
        FavoriteFactory(user=user, community=community)
        data = {
            'user': user.id,
            'community': community.id
        }
        serializer = FavoriteSerializer(data=data)
        assert serializer.is_valid() is False

    def test_favorite_serializer_fields(self):
        user = UserFactory()
        community = CommunityFactory()
        favorite = FavoriteFactory(user=user, community=community)
        serializer = FavoriteSerializer(favorite)
        assert serializer.data['id'] == favorite.id
        assert serializer.data['user'] == favorite.user.id
        assert serializer.data['community'] == favorite.community.id

@pytest.mark.django_db
class TestMemberWriteSerializer:
    def test_valid_member_serializer(self):
        user = UserFactory()
        community = CommunityFactory()
        data = {
            'user': user.id,
            'community': community.id,
            'is_moderator': True
        }
        serializer = MemberWriteSerializer(data=data)
        assert serializer.is_valid()
        member = serializer.save()
        assert member.user == user
        assert member.community == community
        assert member.is_moderator
        assert member.joined_at is not None

    def test_unique_user_community_constraint(self):
        user = UserFactory()
        community = CommunityFactory()
        MemberFactory(user=user, community=community)
        data = {
            'user': user.id,
            'community': community.id,
        }
        serializer = MemberWriteSerializer(data=data)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['User is already a member of this community']}

@pytest.mark.django_db
class TestMemberReadSerializer:
    def test_member_read_serializer_fields(self, serializer_context):
        user = UserFactory()
        community = CommunityFactory(user=user)
        member = MemberFactory(user=user, community=community, is_moderator=True)
        ban = BanFactory(user=user, community=community)
        serializer = MemberReadSerializer(member, context=serializer_context)
        assert serializer.data['id'] == member.id
        assert serializer.data['user']['id'] == member.user.id
        assert serializer.data['community'] == member.community.id
        assert serializer.data['joined_at'] is not None
        assert serializer.data['ban']['id'] == ban.id
        assert serializer.data['is_moderator']
        assert serializer.data['is_creator']