from rest_framework import generics, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, IsAdminUser, AllowAny, SAFE_METHODS
from .serializers import (
    MemberReadSerializer, 
    MemberWriteSerializer, 
    FavoriteSerializer, 
    TopicSerializer, 
    CommunityReadSerializer, 
    CommunityWriteSerializer, 
    RuleSerializer, 
    BanSerializer
)
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from api.pagination import CustomPagination
from .services import (
    CommunityService, 
    TopicService, 
    MemberService, 
    FavoriteService,
    RuleService,
    BanService
)
from .permissions import IsNotBanned, IsOwner, CanModerate, CanBan

class CommunityListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ['name']
    filterset_fields = ['topics']

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(CommunityReadSerializer(serializer.instance, context={'request': request}).data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.instance = CommunityService.create_community(**serializer.validated_data)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CommunityReadSerializer
        return CommunityWriteSerializer

    def get_queryset(self):
        return CommunityService.get_communities(self.request.user)

class CommunityDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly & CanModerate]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CommunityReadSerializer
        return CommunityWriteSerializer
    
    def get_queryset(self):
        return CommunityService.get_communities(self.request.user)

class UserCommunitiesView(generics.ListAPIView):
    serializer_class = CommunityReadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CommunityService.get_user_communities(self.request.user)

class UserModeratedCommunitiesView(generics.ListAPIView):
    serializer_class = CommunityReadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CommunityService.get_user_moderated_communities(self.request.user)

class TopicsViewset(viewsets.ModelViewSet):
    queryset = TopicService.get_topics()
    serializer_class = TopicSerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

class MemberListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly & IsNotBanned]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['joined_at']
    filterset_fields = ['community', 'user', 'is_moderator']
    search_fields = ['user__username']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(MemberReadSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, is_moderator=False)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return MemberReadSerializer
        return MemberWriteSerializer
    
    def get_queryset(self):
        return MemberService.get_members(self.request.user)

class MemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly & (IsOwner | CanModerate)]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return MemberReadSerializer
        return MemberWriteSerializer
    
    def get_queryset(self):
        return MemberService.get_members(self.request.user)

class FavoriteListCreateView(generics.ListCreateAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated & IsNotBanned]
    
    def get_queryset(self):
        return FavoriteService.get_favorites(self.request.user)

class FavoriteDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FavoriteService.get_favorites(self.request.user)


class RuleListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly & CanModerate]
    serializer_class = RuleSerializer
    
    def get_queryset(self):
        return RuleService.get_rules(self.request.user)

class RuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RuleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly & CanModerate]
    
    def get_queryset(self):
        return RuleService.get_rules(self.request.user)

class BanListCreateView(generics.ListCreateAPIView):
    serializer_class = BanSerializer
    permission_classes = [IsAuthenticated & CanModerate & CanBan]
    def get_queryset(self):
        return BanService.get_bans(self.request.user)

class BanDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BanSerializer
    permission_classes = [IsAuthenticated & CanModerate & CanBan]
    def get_queryset(self):
        return BanService.get_bans(self.request.user)