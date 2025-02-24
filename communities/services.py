from django.utils import timezone
from django.db.models import Q
from django.db.transaction import atomic
from .models import Ban, Member, Community, Topic, Favorite, Rule

class CommunityService:

    @atomic
    @staticmethod
    def create_community(**validated_data):
        print(validated_data)
        topics = validated_data.pop('topics', [])
        community = Community.objects.create(**validated_data)
        community.topics.set(topics)
        community.save()
        Member.objects.create(user=validated_data['user'], community=community, is_moderator=True)
        return community

    @classmethod
    def get_community(cls, community_id, user):
        communities = Community.objects.filter(id=community_id)
        communities = cls._exclude_banned(communities, user)
        communities = cls._optimize_communities_queryset(communities)
        return communities.first()
    
    @classmethod
    def get_communities(cls, user):        
        communities = cls.get_filtered_communities(user)
        communities = cls._optimize_communities_queryset(communities)
        return communities.order_by('name')
    
    @classmethod
    def get_filtered_communities(cls, user):
        communities = Community.objects.all()
        communities = cls._exclude_banned(communities, user)
        return communities

    @classmethod
    def get_user_communities(cls, user):
        communities = Community.objects.filter(members__user=user)
        communities = cls._exclude_banned(communities, user)
        communities = cls._optimize_communities_queryset(communities)
        return communities
    
    @classmethod
    def get_user_moderated_communities(cls, user):
        communities = Community.objects.filter(members__user=user, members__is_moderator=True)
        communities = cls._exclude_banned(communities, user)
        communities = cls._optimize_communities_queryset(communities)
        return communities
    
    @classmethod
    def _exclude_banned(cls, communities, user):
        if not user.is_authenticated:
            return communities
        ban_query = Q(community_bans__is_permanent=True) | Q(community_bans__expires_at__gte=timezone.now())
        return communities.exclude(ban_query, community_bans__user=user)

    @classmethod
    def _optimize_communities_queryset(cls, communities):
        return communities.prefetch_related('members', 'topics', 'favorites', 'rules', 'community_bans')

class TopicService:
    @staticmethod
    def get_topics():
        return Topic.objects.all()

class MemberService:
    @classmethod
    def get_members(cls, user):
        is_moderator_query = Q(community__members__user=user, community__members__is_moderator=True)
        members = Member.objects.filter(Q(user=user) | is_moderator_query).distinct()
        members = cls._optimize_members_queryset(members)
        return members
    
    @classmethod
    def _optimize_members_queryset(cls, members):
        return members.select_related('user', 'community').prefetch_related('user__bans')
    
    @staticmethod
    def is_member(user_id, community_id):
        return Member.objects.filter(user__id=user_id, community__id=community_id).exists()

    @staticmethod
    def is_moderator(user_id, community_id):
        return Member.objects.filter(user__id=user_id, community__id=community_id, is_moderator=True).exists()

class BanService:
    @staticmethod
    def is_banned(user, community_id):
        ban_query = Q(is_permanent=True) | Q(expires_at__gt=timezone.now())
        return Ban.objects.filter(ban_query, user=user, community__id=community_id).exists()
    
    @classmethod
    def get_bans(cls, user):
        is_moderator_query = Q(community__members__user=user, community__members__is_moderator=True)
        bans = Ban.objects.filter(Q(user=user) | is_moderator_query)
        return cls._optimize_bans_queryset(bans)

    @classmethod
    def _optimize_bans_queryset(cls, bans):
        return bans.select_related('user', 'community')


class FavoriteService:
    @classmethod
    def get_favorites(cls, user):
        favorites = Favorite.objects.filter(user=user)
        favorites = cls._exclude_banned(favorites, user)
        return favorites
    
    @classmethod
    def _exclude_banned(cls, favorites, user):
        if not user.is_authenticated:
            return favorites
        ban_query = Q(community__community_bans__is_permanent=True) | Q(community__community_bans__expires_at__gte=timezone.now())
        return favorites.exclude(ban_query, community__community_bans__user=user)

class RuleService:
    @classmethod
    def get_rules(cls, user):
        rules = Rule.objects.all()
        rules = cls._exclude_banned(rules, user)
        rules = cls._optimize_rules_queryset(rules)
        return rules

    @classmethod
    def _exclude_banned(cls, rules, user):
        if not user.is_authenticated:
            return rules
        ban_query = Q(community__community_bans__is_permanent=True) | Q(community__community_bans__expires_at__gte=timezone.now())
        return rules.exclude(ban_query, community__community_bans__user=user)
    
    @classmethod
    def _optimize_rules_queryset(cls, rules):
        return rules.select_related('community').prefetch_related('community__community_bans')