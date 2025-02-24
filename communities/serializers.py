from rest_framework import serializers
from accounts.serializers import CustomUserSerializer
from .models import Community, Topic, Ban, Favorite, Member, Rule
from .services import BanService
from django.utils import timezone
from django.contrib.auth import get_user_model
User = get_user_model()

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = '__all__'

class CommunityWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(write_only=True, default=serializers.CurrentUserDefault(), queryset=User.objects.all())

    class Meta:
        model = Community
        fields = '__all__'

    def validate_topics(self, value):
        if len(value) > 3:
            raise serializers.ValidationError("Topics cannot exceed 3")
        return value

class BanSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    community = serializers.PrimaryKeyRelatedField(queryset=Community.objects.all())
    is_active = serializers.BooleanField(read_only=True)
    class Meta:
        model = Ban
        fields = ['id', 'user', 'community', 'banned_at', 'reason', 'is_permanent', 'expires_at', 'is_active']

    def validate(self, attrs):
        is_permanent = attrs.get('is_permanent', False)
        expires_at = attrs.get('expires_at')
        user = attrs.get('user')
        community = attrs.get('community')
        if is_permanent and expires_at:
            raise serializers.ValidationError('Permanent bans cannot have an expiration date')
        if not is_permanent and not expires_at:
            raise serializers.ValidationError('Temporary bans must have an expiration date')
        if expires_at and expires_at < timezone.now():
            raise serializers.ValidationError('Ban expiration date cannot be in the past')
        if community and user and BanService.is_banned(user, community.id):
            raise serializers.ValidationError('User is already banned in this community')
        return super().validate(attrs)

class MemberWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(default=serializers.CurrentUserDefault(), queryset=User.objects.all())
    community = serializers.PrimaryKeyRelatedField(queryset=Community.objects.all())

    class Meta:
        model = Member
        fields = '__all__'

    validators = [
        serializers.UniqueTogetherValidator(
            queryset=Member.objects.all(),
            fields=['user', 'community'],
            message='User is already a member of this community'
        )
    ]

class MemberReadSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    ban = BanSerializer()
    is_creator = serializers.BooleanField()

    class Meta:
        model = Member
        fields = ['id', 'community', 'user', 'ban', 'joined_at' , 'is_creator', 'is_moderator']

class RuleSerializer(serializers.ModelSerializer):
    community = serializers.PrimaryKeyRelatedField(queryset=Community.objects.all())
    class Meta:
        model = Rule
        fields = '__all__'

class CommunityReadSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    topics = TopicSerializer(many=True)
    moderators = MemberReadSerializer(many=True)
    rules = RuleSerializer(many=True)
    members_count = serializers.SerializerMethodField(read_only=True)
    member_id = serializers.SerializerMethodField(read_only=True)
    favorite_id = serializers.SerializerMethodField(read_only=True)
    is_moderator = serializers.SerializerMethodField(read_only=True)
    is_creator = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Community
        fields = '__all__'

    def get_is_creator(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return obj.user == request.user

    def get_moderators(self, obj):
        return MemberReadSerializer(obj.members.filter(is_moderator=True), many=True, context=self.context).data
    
    def get_rules(self, obj):
        return RuleSerializer(obj.rules, many=True).data

    def get_favorite_id(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        return obj.get_favorite_id(request.user)

    def get_is_moderator(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        return obj.get_is_moderator(request.user)
    
    def get_members_count(self, obj):
        return obj.members_count
    
    def get_member_id(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        return obj.get_member_id(request.user)

class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(default=serializers.CurrentUserDefault(), queryset=User.objects.all())
    community = serializers.PrimaryKeyRelatedField(queryset=Community.objects.all())

    class Meta:
        model = Favorite
        fields = '__all__'
    
    validators = [
        serializers.UniqueTogetherValidator(
            queryset=Favorite.objects.all(),
            fields=['user', 'community'],
            message='User has already favorited this community'
        )
    ]