from rest_framework import serializers
from .models import Post, SavedPost, Attachment, PostInteraction, PostReport
from communities.models import Community, Rule
from communities.serializers import RuleSerializer
from accounts.serializers import CustomUserSerializer
from communities.serializers import CommunityReadSerializer
from django.contrib.auth import get_user_model
from .services import PostService, PostReportService
User = get_user_model()

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['file', 'file_type']

class PostWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(default=serializers.CurrentUserDefault(), queryset=User.objects.all())
    community = serializers.PrimaryKeyRelatedField(queryset=Community.objects.all(), required=False)
    attachments = serializers.ListField(child=serializers.FileField(), required=False, write_only=True)
    original_post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all(), required=False)

    class Meta:
        model = Post
        fields = ['id', 'user', 'status', 'community', 'title', 'type', 'is_nsfw', 'is_spoiler', 'content', 'link', 'attachments', 'original_post']

    def validate(self, attrs):
        post_type = attrs.get('type', getattr(self.instance, 'type', ''))
        attachments = attrs.get('attachments', list(self.instance.attachments.all()) if self.instance else [])
        link = attrs.get('link', getattr(self.instance, 'link', ''))
        content = attrs.get('content', getattr(self.instance, 'content', ''))
        original_post = attrs.get('original_post', getattr(self.instance, 'original_post', None))
        if attachments and post_type != 'media':
            raise serializers.ValidationError("Only media posts can have attachments")
        elif not attachments and post_type == 'media':
            raise serializers.ValidationError("Media posts must have at least 1 attachment")
        elif link != '' and post_type != 'link':
            raise serializers.ValidationError("Only link posts can have a link")
        elif link == '' and post_type == 'link':
            raise serializers.ValidationError("Link posts must have a link")
        elif content == '' and post_type == 'text':
            raise serializers.ValidationError("Text posts must have content")
        elif original_post and post_type != 'crosspost':
            raise serializers.ValidationError("Only crosspost posts can have an original post")
        elif not original_post and post_type == 'crosspost':
            raise serializers.ValidationError("Crosspost posts must have an original post")
        if original_post and original_post.is_nsfw:
            attrs['is_nsfw'] = True
        return attrs

    def validate_attachments(self, files):
        image_types = ['png', 'jpg', 'jpeg', 'jfif']
        video_types = ['mp4', 'webm', 'ogg']
        max_size = 100 * 1024 * 1024
        validated_files = []

        for file in files:
            if file.size > max_size:
                raise serializers.ValidationError(f"File {file.name} exceeds 100MB limit.")
            file_type = file.name.split(".")[-1].lower()
            if file_type in image_types:
                file_type = "image"
            elif file_type in video_types:
                file_type = "video"
            else:
                raise serializers.ValidationError(f"Unsupported file type: {file.name}")
            validated_files.append({'file': file, 'file_type': file_type})
        return validated_files
    
    # def get_fields(self):
        # request = self.context.get('request')
        # fields = super().get_fields()
        # if not request:
        #     return fields
        # if request.method == 'POST' or request.method == 'PUT':
        #     user = request.user
        #     fields['community'].queryset = CommunityService.get_filtered_communities(user)
        #     fields['original_post'].queryset = PostService.get_filtered_posts(user).filter(original_post__isnull=True)
        # else:
        #     fields.pop('community')
        #     fields.pop('original_post')
        #     fields.pop('type')
        # return fields

class PostUpdateSerializer(PostWriteSerializer):
    class Meta:
        model = Post
        fields = ['id', 'title', 'status', 'is_nsfw', 'is_spoiler', 'content', 'link', 'attachments']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = self.context.get('request').user
        community = self.instance.community
        if user != self.instance.user and community.members.filter(user=user, is_moderator=True).exists():
            if 'status' not in attrs or len(attrs) > 1:
                raise serializers.ValidationError("Moderators can only change the status of posts")
        return attrs

    def validate_status(self, value):
        user = self.context.get('request').user
        community = self.instance.community
        if community and not community.members.filter(user=user, is_moderator=True).exists():
            raise serializers.ValidationError("You are not a moderator of this community")
        return value

class PostReadSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    community = CommunityReadSerializer()
    attachments = AttachmentSerializer(many=True)
    comments_count = serializers.IntegerField()
    interaction_diff = serializers.IntegerField(required=False)
    interaction = serializers.SerializerMethodField()
    original_post = serializers.SerializerMethodField()
    saved_post_id = serializers.SerializerMethodField()
    is_author = serializers.SerializerMethodField()
    is_reported = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = '__all__'
        # fields = ['id', 'user', 'title', 'type', 'is_nsfw', 'is_spoiler', 'content', 'link', 'attachments']

    def get_is_author(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return obj.user == request.user
    
    def get_interaction(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        interaction = obj.get_user_interaction(request.user)
        if not interaction:
            return None
        return PostInteractionSerializer(interaction).data
    
    def get_saved_post_id(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        return obj.get_saved_post_id(request.user)
    
    def get_is_reported(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return obj.get_is_reported(request.user)
    
    def get_original_post(self, obj):
        request = self.context.get('request')
        if not obj.original_post or not request:
            return None
        original_post = PostService.get_post(obj.original_post.id, request.user)
        if not original_post:
            return None
        return PostReadSerializer(original_post, context=self.context).data

class SavedPostSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(default=serializers.CurrentUserDefault(), queryset=User.objects.all())
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())

    class Meta:
        model = SavedPost
        fields = '__all__'
    
    validators = [
        serializers.UniqueTogetherValidator(
            queryset=SavedPost.objects.all(),
            fields=['user', 'post'],
            message='User has already saved this post'
        )
    ]

class LinkPreviewSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, allow_blank=True)
    description = serializers.CharField(max_length=500, allow_blank=True)
    image = serializers.URLField(allow_blank=True)
    url = serializers.URLField()


class PostInteractionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(default=serializers.CurrentUserDefault(), queryset=User.objects.all())
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())
    class Meta:
        model = PostInteraction
        fields = '__all__'
    
    validators = [
        serializers.UniqueTogetherValidator(
            queryset=PostInteraction.objects.all(),
            fields=['user', 'post'],
            message='User has already interacted with this post'
        ),
    ]

class PostReportWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=serializers.CurrentUserDefault())
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())
    violated_rule = serializers.PrimaryKeyRelatedField(queryset=Rule.objects.all(), required=False)
    class Meta:
        model = PostReport
        fields = '__all__'

    def validate(self, attrs):
        violated_rule = attrs.get('violated_rule')
        post = attrs.get('post')
        if violated_rule and violated_rule.community != post.community:
            raise serializers.ValidationError('The selected rule does not belong to the specified community')
        return super().validate(attrs)

    def validate_post(self, value):
        user = self.context.get('request').user
        if not value.community:
            raise serializers.ValidationError("Post must belong to a community")
        if user == value.user:
            raise serializers.ValidationError("You cannot report your own post")
        if PostReportService.is_reported(user.id, value.id):
            raise serializers.ValidationError("You already have a pending report for this post")
        return value

class PostReportReadSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    post = PostReadSerializer()
    violated_rule = RuleSerializer()
    class Meta:
        model = PostReport
        fields = '__all__'