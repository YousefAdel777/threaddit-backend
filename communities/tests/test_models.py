import pytest
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
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

@pytest.mark.django_db
class TestCommunityModel:
    def test_community_creation(self):
        user = UserFactory()
        topic = TopicFactory()
        community = CommunityFactory(
            user=user,
            name='test_name',
            topics=[topic.id],
            icon='test_icon.png',
            banner='test_banner.png'
        )
        assert community.user == user
        assert community.name == 'test_name'
        assert community.topics.first() == topic
        assert community.icon == 'test_icon.png'
        assert community.banner == 'test_banner.png'
        assert community.created_at is not None
    
    def test_string_representation(self):
        community = CommunityFactory()
        assert str(community) == community.name

    def test_get_favorite_id(self):
        user = UserFactory()
        community = CommunityFactory()
        favorite = FavoriteFactory(user=user, community=community)
        assert community.get_favorite_id(user) == favorite.id
    
    def test_get_members_id(self):
        user = UserFactory()
        community = CommunityFactory()
        member = MemberFactory(user=user, community=community)
        assert community.get_member_id(user) == member.id
    
    def test_get_is_moderator(self):
        user = UserFactory()
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=True)
        assert community.get_is_moderator(user)
    
    def test_moderators(self):
        user = UserFactory()
        user2 = UserFactory()
        community = CommunityFactory()
        MemberFactory(user=user, community=community, is_moderator=True)
        MemberFactory(user=user2, community=community, is_moderator=False)
        assert len(community.moderators.all()) == 1
    
    def test_members_count_property(self):
        user = UserFactory()
        community = CommunityFactory()
        MemberFactory(user=user, community=community)
        assert community.members_count == 1

@pytest.mark.django_db
class TestTopicModel:
    def test_topic_creation(self):
        topic = TopicFactory(name='test_name', description='test_description')
        assert topic.name == 'test_name'
        assert topic.description == 'test_description'

    def test_string_representation(self):
        topic = TopicFactory()
        assert str(topic) == topic.name

    def test_unique_name(self):
        TopicFactory(name='test_name')
        with pytest.raises(IntegrityError):
            TopicFactory(name='test_name')

@pytest.mark.django_db
class TestRuleModel:
    def test_rule_creation(self):
        community = CommunityFactory()
        rule = RuleFactory(title='test_title', description='test_description', community=community)
        assert rule.title == 'test_title'
        assert rule.description == 'test_description'
        assert rule.community == community
        assert rule.created_at is not None

    def test_string_representation(self):
        community = CommunityFactory()
        rule = RuleFactory(community=community)
        assert str(rule) == f"{rule.title} for {community.name}"

@pytest.mark.django_db
class TestMemberModel:
    def test_member_creation(self):
        user = UserFactory()
        community = CommunityFactory()
        member = MemberFactory(user=user, community=community)
        assert member.user == user
        assert member.community == community

    def test_string_representation(self):
        member = MemberFactory()
        assert str(member) == f"{member.user.username} in {member.community.name}"
    
    def test_unique_member(self):
        user = UserFactory()
        community = CommunityFactory()
        MemberFactory(user=user, community=community)
        with pytest.raises(IntegrityError):
            MemberFactory(user=user, community=community)

    def test_ban_property(self):
        user = UserFactory()
        community = CommunityFactory()
        member = MemberFactory(user=user, community=community)
        ban = BanFactory(user=user, community=community)
        assert member.ban == ban

    def test_is_creator_property(self):
        user = UserFactory()
        community = CommunityFactory(user=user)
        member = MemberFactory(user=user, community=community)
        assert member.is_creator

@pytest.mark.django_db
class TestBanModel:
    def test_ban_creation(self):
        user = UserFactory()
        community = CommunityFactory()
        ban = BanFactory(user=user, community=community, is_permanent=True)
        assert ban.user == user
        assert ban.banned_at is not None
        assert ban.community == community
        assert ban.is_permanent

    def test_string_representation(self):
        user = UserFactory()
        community = CommunityFactory()
        ban = BanFactory(user=user, community=community)
        assert str(ban) == f"Ban on {ban.user.username} - {'Permanent' if ban.is_permanent else f'Until {ban.expires_at}'}"

    def test_is_active_property(self):
        user = UserFactory()
        community = CommunityFactory()
        ban = BanFactory(user=user, community=community, is_permanent=True)
        assert ban.is_active

    def test_ban_creation_with_is_permanent_and_expires_at(self):
        user = UserFactory()
        community = CommunityFactory()
        with pytest.raises(ValidationError):
            BanFactory(user=user, community=community, is_permanent=True, expires_at=timezone.now() + timezone.timedelta(days=1))

    def test_ban_creation_with_is_not_permanent_and_no_expires_at(self):        
        user = UserFactory()
        community = CommunityFactory()
        with pytest.raises(ValidationError):
            BanFactory(user=user, community=community, is_permanent=False, expires_at=None)

    def test_ban_creation_with_invalid_dates(self):
        user = UserFactory()
        community = CommunityFactory()
        with pytest.raises(ValidationError):
            BanFactory(user=user, community=community, is_permanent=False, expires_at=timezone.now() - timezone.timedelta(days=1))
    
    def test_ban_creation_for_user_with_active_ban(self):
        user = UserFactory()
        community = CommunityFactory()
        BanFactory(user=user, community=community, is_permanent=True)
        with pytest.raises(ValidationError):
            BanFactory(user=user, community=community)


@pytest.mark.django_db
class TestFavoriteModel:
    def test_favorite_creation(self):
        user = UserFactory()
        community = CommunityFactory()
        favorite = FavoriteFactory(user=user, community=community)
        assert favorite.user == user
        assert favorite.community == community
    
    def test_string_representation(self):
        user = UserFactory()
        community = CommunityFactory()
        favorite = FavoriteFactory(user=user, community=community)
        assert str(favorite) == f"{user.username} favorited {community.name}"
    
    def test_unique_favorite(self):
        user = UserFactory()
        community = CommunityFactory()
        FavoriteFactory(user=user, community=community)
        with pytest.raises(IntegrityError):
            FavoriteFactory(user=user, community=community)