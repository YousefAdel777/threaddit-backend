from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from api.pagination import CustomPagination
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from .serializers import (
    PostWriteSerializer, 
    PostReadSerializer,
    PostUpdateSerializer,
    PostInteractionSerializer, 
    SavedPostSerializer, 
    PostReportReadSerializer, 
    PostReportWriteSerializer, 
    LinkPreviewSerializer
)
from bs4 import BeautifulSoup
import requests
from .services import PostService, SavedPostService, PostInteractionService, PostReportService
from .permissions import IsAuthor, CanPost, CanInteract, CanCrossPost, CanModerate

class PostListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly & CanPost & CanCrossPost]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['community', 'user', 'status']
    ordering_fields = ['created_at', 'interaction_diff']
    search_fields = ['title', 'content', 'community__name', 'user__username']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(PostReadSerializer(serializer.instance, context={'request': request}).data, status=status.HTTP_201_CREATED)

    # # @method_decorator(vary_on_headers('Authorization'))
    # # @method_decorator(cache_page(60 * 15, key_prefix=lambda req: f"post_list_{req.user.id}"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PostReadSerializer
        return PostWriteSerializer

    def perform_create(self, serializer):
        serializer.instance = PostService.create_post(**serializer.validated_data)

    def get_queryset(self):
        return PostService.get_posts(self.request.user)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly & (IsAuthor | CanModerate)]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['community', 'user']
    ordering_fields = ['created_at']

    # # @method_decorator(vary_on_headers('Authorization'))
    # # @method_decorator(cache_page(60 * 15, key_prefix=lambda req: f"post_detail_{req.user.id}"))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(PostReadSerializer(serializer.instance, context={'request': request}).data)

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(PostReadSerializer(serializer.instance, context={'request': request}).data)

    def perform_update(self, serializer):
        serializer.instance = PostService.update_post(serializer.instance.id, **serializer.validated_data)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PostReadSerializer
        elif self.request.method == 'PATCH':
            return PostUpdateSerializer
        return PostWriteSerializer

    def get_queryset(self):
        return PostService.get_posts(self.request.user)

class SavedPostListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated & CanInteract]
    serializer_class = SavedPostSerializer
    pagination_class = CustomPagination

    # @method_decorator(vary_on_headers('Authorization'))
    # @method_decorator(cache_page(60 * 15, key_prefix=lambda req: f"saved_post_list_{req.user.id}"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_queryset(self):        
        return SavedPostService.get_saved_posts(self.request.user)

class SavedPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated & IsAuthor]
    serializer_class = SavedPostSerializer
    
    # @method_decorator(vary_on_headers('Authorization'))
    # @method_decorator(cache_page(60 * 15, key_prefix=lambda req: f"saved_post_detail_{req.user.id}"))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):                
        return SavedPostService.get_saved_posts(self.request.user)

class UserSavedPostsView(generics.ListAPIView):
    serializer_class = PostReadSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    # @method_decorator(vary_on_headers('Authorization'))
    # @method_decorator(cache_page(60 * 15, key_prefix=lambda req: f"user_saved_post_list_{req.user.id}"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return PostService.get_saved_posts(self.request.user)

class PostInteractionListCreateView(generics.ListCreateAPIView):
    serializer_class = PostInteractionSerializer
    permission_classes = [IsAuthenticated & CanInteract]

    # @method_decorator(vary_on_headers('Authorization'))
    # @method_decorator(cache_page(60 * 15, key_prefix=lambda req: f"post_interaction_list_{req.user.id}"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    # @atomic
    # def create(self, request, *args, **kwargs):
    #     interaction_type = request.data.get('interaction_type')
    #     post = request.data.get('post')
    #     user = Post.objects.get(pk=post).user
    #     user.update_post_karma(1 if interaction_type == 'upvote' else -1)
    #     return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        # serializer.save(user=self.request.user)
        # post_id = serializer.validated_data.get('post')
        # interaction_type = serializer.validated_data.get('interaction_type')
        serializer.instance = PostInteractionService.create_post_interaction(**serializer.validated_data)
    
    def get_queryset(self):
        return PostInteractionService.get_post_interactions(self.request.user)

class PostInteractionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostInteractionSerializer
    permission_classes = [IsAuthenticated & IsAuthor & CanInteract]

    # @method_decorator(vary_on_headers('Authorization'))
    # @method_decorator(cache_page(60 * 15, key_prefix=lambda req: f"post_interaction_detail_{req.user.id}"))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def perform_destroy(self, instance):
        PostInteractionService.delete_post_interaction(instance)

    # @atomic
    # def partial_update(self, request, *args, **kwargs):
    #     interaction_type = request.data.get('interaction_type')
    #     interaction = self.get_object()
    #     if interaction_type == 'upvote' and interaction.interaction_type == 'downvote':
    #         interaction.post.user.update_post_karma(2)
    #     elif interaction_type == 'downvote' and interaction.interaction_type == 'upvote':
    #         interaction.post.user.update_post_karma(-2)
    #     return super().partial_update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.instance = PostInteractionService.update_post_interaction(self.get_object(), **serializer.validated_data)

    def get_queryset(self):
        return PostInteractionService.get_post_interactions(self.request.user)

class FeedView(generics.ListAPIView):
    serializer_class = PostReadSerializer
    pagination_class = CustomPagination

    # @method_decorator(vary_on_headers('Authorization'))
    # @method_decorator(cache_page(60 * 15, key_prefix=lambda req: f"feed_list_{req.user.id}"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return PostService.get_feed(self.request.user)

class PopularView(generics.ListAPIView):
    serializer_class = PostReadSerializer
    pagination_class = CustomPagination

    # @method_decorator(vary_on_headers('Authorization'))
    # @method_decorator(cache_page(60 * 15, key_prefix=lambda req: f"popular_list_{req.user.id}"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return PostService.get_feed(self.request.user)
        # return Post.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=1)).annotate(
        #     upvotes=Coalesce(Count('post_interactions', filter=Q(post_interactions__interaction_type='upvote')), 0),
        #     downvotes=Coalesce(Count('post_interactions', filter=Q(post_interactions__interaction_type='downvote')), 0),
        #     interaction_diff=F('upvotes') - F('downvotes')
        # ).order_by('-interaction_diff', '-created_at')

class PostReportListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated & CanInteract]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['post__community', 'status']

    # @method_decorator(vary_on_headers('Authorization'))
    # @method_decorator(cache_page(60 * 15, key_prefix=lambda req: f"post_report_list_{req.user.id}"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        read_serializer = PostReportReadSerializer(serializer.instance)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PostReportReadSerializer
        return PostReportWriteSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return PostReportService.get_post_reports(self.request.user)

class PostReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated & CanModerate]

    # @method_decorator(vary_on_headers('Authorization'))
    # @method_decorator(cache_page(60 * 15, key_prefix=lambda req: f"post_report_detail_{req.user.id}"))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        read_serializer = PostReadSerializer(serializer.instance)
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        read_serializer = PostReadSerializer(serializer.instance)
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        return PostReportService.get_post_reports(self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PostReportReadSerializer
        return PostReportWriteSerializer

class UserUpvotedPostsView(generics.ListAPIView):
    serializer_class = PostReadSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    # @method_decorator(vary_on_headers('Authorization'))
    # @method_decorator(cache_page(60 * 15, key_prefix=lambda req: f"user_upvoted_post_list_{req.user.id}"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return PostService.get_interacted_posts(self.request.user, 'upvote')

class UserDownvotedPostsView(generics.ListAPIView):
    serializer_class = PostReadSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    # @method_decorator(vary_on_headers('Authorization'))
    # @method_decorator(cache_page(60 * 15, key_prefix=lambda req: f"user_downvoted_post_list_{req.user.id}"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return PostService.get_interacted_posts(self.request.user, 'downvote')


class LinkPreviewView(APIView):

    # @method_decorator(vary_on_headers('Authorization'))
    # @method_decorator(cache_page(60 * 60, key_prefix="link_preview"))
    def get(self, request, *args, **kwargs):
        url = request.query_params.get('url')
        if not url:
            return Response({"error": "URL is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            return Response({"error": "Failed to fetch URL"}, status=status.HTTP_400_BAD_REQUEST)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        og_title = soup.find("meta", property="og:title")
        og_description = soup.find("meta", property="og:description")
        og_image = soup.find("meta", property="og:image")
        
        title = og_title["content"] if og_title else soup.title.string if soup.title else "No title available"
        description = og_description["content"] if og_description else ""
        image = og_image["content"] if og_image else ""
        
        preview_data = {
            "title": title,
            "description": description,
            "image": image,
            "url": url,
        }
        serializer = LinkPreviewSerializer(data=preview_data)
        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)