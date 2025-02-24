from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.contrib.auth import get_user_model
from django.core.cache import cache
from .serializers import CustomUserSerializer, BlockSerializer, FollowSerializer
from api.pagination import CustomPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from .services import BlockService, UserService, FollowService
from .permissions import CanFollow
from django.conf import settings
User = get_user_model()

class UserListView(generics.ListAPIView):
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ['username', 'bio']

    @method_decorator(vary_on_headers('Authorization'))
    @method_decorator(cache_page(60 * 15, key_prefix="user_list"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return UserService.get_users(self.request.user)

class UserDetailView(generics.RetrieveAPIView):
    serializer_class = CustomUserSerializer

    def retrieve(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        cache_key = f"user_{pk}"
        cached_user = cache.get(cache_key)
        if cached_user:
            return Response(cached_user, status=status.HTTP_200_OK)
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=60 * 15)
        return response

    def get_queryset(self):
        return UserService.get_users(self.request.user)

class GithubLoginView(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    callback_url = settings.GITHUB_CALLBACK_URL
    client_class = OAuth2Client

class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.GOOGLE_CALLBACK_URL
    client_class = OAuth2Client

class FollowCreateView(generics.CreateAPIView):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated & CanFollow]

    def perform_create(self, serializer):
        serializer.save(follower=self.request.user)

    def get_queryset(self):        
        return FollowService.get_follows(self.request.user)

class FollowDeleteView(generics.DestroyAPIView):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return FollowService.get_follows(self.request.user)

class FollowedUsersListView(generics.ListAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    @method_decorator(cache_page(60 * 15, key_prefix="followed_user_list"))
    @method_decorator(vary_on_headers('Authorization'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return UserService.get_followed_users(self.request.user)

class BlockCreateView(generics.CreateAPIView):
    serializer_class = BlockSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        BlockService.block_user(self.request.user, serializer.validated_data['blocked_user'])

    def get_queryset(self):
        return BlockService.get_blocks(self.request.user)

class BlockDeleteView(generics.DestroyAPIView):
    serializer_class = BlockSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return BlockService.get_blocks(self.request.user)

class BlockedUsersListView(generics.ListAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    @method_decorator(cache_page(60 * 15, key_prefix="blocked_user_list"))
    @method_decorator(vary_on_headers('Authorization'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return UserService.get_blocked_users(self.request.user)