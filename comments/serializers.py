from rest_framework import serializers
from posts.models import Post
from communities.models import Rule
from communities.services import MemberService
from communities.serializers import RuleSerializer
from .models import Comment, CommentInteraction, CommentReport
from .services import CommentService, CommentReportService
from accounts.serializers import CustomUserSerializer
from posts.serializers import PostReadSerializer
from django.contrib.auth import get_user_model
User = get_user_model()

class CommentWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(default=serializers.CurrentUserDefault(), queryset=User.objects.all())
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())

    class Meta:
        model = Comment
        fields = '__all__'

    def validate(self, attrs):
        parent = attrs.get('parent')
        post = attrs.get('post', getattr(self.instance, 'post', None))
        if parent and post:
            if parent.post != post:
                raise serializers.ValidationError("Parent comment must belong to the same post")
        return attrs

class CommentUpdateSerializer(CommentWriteSerializer):
    class Meta:
        model = Comment
        fields = ['content', 'status']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get('request')
        community = getattr(self.instance.post, 'community', None)
        if not request or not community:
            if 'status' in attrs:
                raise serializers.ValidationError("Only moderators can change comment status")
            return attrs
        is_moderator = MemberService.is_moderator(request.user.id, community.id)
        if is_moderator:
            if set(attrs.keys()) != {'status'}:
                raise serializers.ValidationError("Moderators can only change the status of comments")
        else:
            if 'status' in attrs:
                raise serializers.ValidationError("Only moderators can change comment status")
        return attrs

class CommentReadSerializer(serializers.ModelSerializer):
    post = PostReadSerializer()
    user = CustomUserSerializer()
    interaction_diff = serializers.IntegerField(read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)
    interaction = serializers.SerializerMethodField()
    is_author = serializers.SerializerMethodField()
    is_reported = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = '__all__'

    def get_is_author(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return obj.user == request.user

    def get_replies(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        replies = CommentService.get_annotated_replies(obj.id, request.user)
        if not replies:
            return []
        return CommentReadSerializer(replies, many=True, context=self.context).data

    def get_interaction(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        user = request.user
        interaction = obj.get_interaction(user)
        if not interaction: 
            return None
        return CommentInteractionSerializer(interaction).data
    
    def get_is_reported(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return obj.get_is_reported(request.user)

class CommentReportWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=serializers.CurrentUserDefault())
    comment = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all())
    violated_rule = serializers.PrimaryKeyRelatedField(queryset=Rule.objects.all(), required=False)

    class Meta:
        model = CommentReport
        fields = '__all__'

    def validate(self, attrs):
        violated_rule = attrs.get('violated_rule')
        comment = attrs.get('comment')
        if violated_rule and violated_rule.community != comment.post.community:
            raise serializers.ValidationError('Violated rule must belong to the same community as the comment')
        return super().validate(attrs)

    def validate_comment(self, value):
        user = self.context.get('request').user
        if not value.post.community:
            raise serializers.ValidationError("Comment must belong to a community")
        if value.user == user:
            raise serializers.ValidationError("You cannot report your own comment")
        if CommentReportService.is_reported(user, value):
            raise serializers.ValidationError("You already have a pending report for this comment")
        return value

class CommentReportReadSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    comment = CommentReadSerializer()
    violated_rule = RuleSerializer()

    class Meta:
        model = CommentReport
        fields = '__all__'

class CommentInteractionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(default=serializers.CurrentUserDefault(), queryset=User.objects.all())
    comment = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all())

    class Meta:
        model = CommentInteraction
        fields = '__all__'
    
    validators = [
        serializers.UniqueTogetherValidator(
            queryset=CommentInteraction.objects.all(),
            fields=['user', 'comment'],
            message='User has already interacted with this comment'
        )
    ]