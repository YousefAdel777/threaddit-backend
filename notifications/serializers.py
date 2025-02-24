from rest_framework import serializers
from .models import Notification
from accounts.serializers import CustomUserSerializer
from django.contrib.auth import get_user_model
from comments.serializers import CommentReadSerializer
from posts.serializers import PostReadSerializer
from accounts.serializers import FollowSerializer

User = get_user_model()

SERIALIZERS_MAPPING = {
    'post': PostReadSerializer,
    'follow': FollowSerializer,
    'comment': CommentReadSerializer
}

class NotificationSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    content_object = serializers.SerializerMethodField(read_only=True)
    content_type = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Notification
        fields = '__all__'

    def get_content_object(self, obj):
        serializer_class = SERIALIZERS_MAPPING.get(obj.content_type.model)
        return serializer_class(obj.content_object, context=self.context).data
    
    def get_content_type(self, obj):
        return obj.content_type.model