from rest_framework import serializers, validators
from .models import CustomUser, Block, Follow
from dj_rest_auth.registration.serializers import RegisterSerializer
from allauth.account.adapter import get_adapter
from django.contrib.auth import authenticate

class CustomUserCreateSerializer(RegisterSerializer, serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True, validators=[validators.UniqueValidator(queryset=CustomUser.objects.all())])
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']

    def validate_username(self, username):
        return username
    
    def validate(self, data):
        return data
    
    def validate_password(self, password):
        return get_adapter().clean_password(password)
    
    def get_cleaned_data(self):
        return {
            "username": self.validated_data.get("username", ""),
            "password": self.validated_data.get("password", ""),
            "email": self.validated_data.get("email", "")
        }

class CustomLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    class Meta:
        model = CustomUser
        fields = ['email', 'password']
    
    def validate(self, attrs):
        user = authenticate(email=attrs.get('email'), password=attrs.get('password'))
        if not user:
            raise serializers.ValidationError("Unable to log in with provided credentials..")
        attrs['user'] = user
        return attrs


class CustomUserSerializer(serializers.ModelSerializer):
    block_id = serializers.SerializerMethodField(read_only=True)
    follow_id = serializers.SerializerMethodField(read_only=True)
    is_current_user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'image', 'post_karma', 'comment_karma', 'created_at', 'is_current_user', 'block_id', 'follow_id', 'followers_count', 'bio']

    def get_is_current_user(self, obj):
        request = self.context.get('request')
        if request:
            return request.user == obj
        return False
    
    def get_follow_id(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        return obj.get_follow_id(request.user)

    def get_block_id(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        return obj.get_block_id(request.user)

class FollowSerializer(serializers.ModelSerializer):
    follower = serializers.PrimaryKeyRelatedField(default=serializers.CurrentUserDefault(), queryset=CustomUser.objects.all())
    followed = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())

    def validate(self, attrs):
        if attrs.get('follower') == attrs.get('followed'):
            raise serializers.ValidationError('User cannot follow themselves')
        return attrs
    
    validators = [
        serializers.UniqueTogetherValidator(
            queryset=Follow.objects.all(),
            fields=['follower', 'followed'],
            message='User is already following this user'
        )
    ]

    class Meta:
        model = Follow
        fields = '__all__'

class BlockSerializer(serializers.ModelSerializer):
    blocked_by = serializers.PrimaryKeyRelatedField(default=serializers.CurrentUserDefault(), queryset=CustomUser.objects.all())
    blocked_user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())

    def validate(self, attrs):
        if attrs.get('blocked_by') == attrs.get('blocked_user'):
            raise serializers.ValidationError('User cannot block themselves')
        return attrs
    
    validators = [
        serializers.UniqueTogetherValidator(
            queryset=Block.objects.all(),
            fields=['blocked_by', 'blocked_user'],
            message='User has already blocked this user'
        )
    ]

    class Meta:
        model = Block
        fields = '__all__'

# class UserHighlightWriteSerializer(serializers.ModelSerializer):
#     user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), default=serializers.CurrentUserDefault())
#     post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())
#     class Meta:
#         model = UserHighlight
#         fields = ['post']

# class UserHighlightReadSerializer(serializers.ModelSerializer):
#     user = CustomUserSerializer()
#     post = PostReadSerializer()
#     class Meta: 
#         model = UserHighlight
#         fields = '__all__'