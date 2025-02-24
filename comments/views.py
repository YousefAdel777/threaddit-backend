from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.filters import OrderingFilter, SearchFilter
from api.pagination import CustomPagination
from .serializers import (
    CommentReadSerializer, 
    CommentWriteSerializer, 
    CommentReportReadSerializer, 
    CommentReportWriteSerializer, 
    CommentInteractionSerializer,
    CommentUpdateSerializer
)
from django_filters.rest_framework import DjangoFilterBackend
from .services import CommentService, CommentInteractionService, CommentReportService
from .permissions import CanComment, CanInteract, IsAuthor
from communities.permissions import CanModerate

class CommentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly & CanComment]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['post', 'user']
    ordering_fields = ['created_at', 'interaction_diff']

    @method_decorator(cache_page(60 * 15, key_prefix="comment_list"))
    @method_decorator(vary_on_headers('Authorization'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CommentReadSerializer
        return CommentWriteSerializer

    def get_queryset(self):
        return CommentService.get_parent_comments(self.request.user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        serializer.instance.interaction_diff = 0
        read_serializer = CommentReadSerializer(serializer.instance, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly & (IsAuthor | CanModerate)]

    # def get_object(self):
    #     comment = CommentService.get_comment(self.kwargs['pk'], self.request.user)
    #     if comment is None:
    #         raise Http404
    #     return comment

    @method_decorator(cache_page(60 * 15, key_prefix="comment_detail"))
    @method_decorator(vary_on_headers('Authorization'))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        return CommentService.get_annotated_comments(self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CommentReadSerializer
        if self.request.method == 'PATCH':
            return CommentUpdateSerializer
        return CommentWriteSerializer
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(CommentReadSerializer(serializer.instance, context={'request': request}).data)
    
    def partial_update(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(CommentReadSerializer(serializer.instance, context={'request': request}).data)


class CommentInteractionListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentInteractionSerializer
    permission_classes = [IsAuthenticated & CanInteract]

    @method_decorator(cache_page(60 * 15, key_prefix="comment_interaction_list"))
    @method_decorator(vary_on_headers('Authorization'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.validated_data['user'] = self.request.user
        serializer.instance = CommentInteractionService.create_comment_interaction(**serializer.validated_data)

    def get_queryset(self):
        return CommentInteractionService.get_comment_interactions(self.request.user)

    # @atomic
    # def create(self, request, *args, **kwargs):
    #     interaction_type = request.data.get('interaction_type')
    #     comment = request.data.get('comment')
    #     user = Comment.objects.get(pk=comment).user
    #     user.update_comment_karma(1 if interaction_type == 'upvote' else -1)
    #     return super().create(request, *args, **kwargs)


class CommentInteractionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentInteractionSerializer
    permission_classes = [IsAuthenticated & IsAuthor]

    @method_decorator(cache_page(60 * 15, key_prefix="comment_interaction_detail"))
    @method_decorator(vary_on_headers('Authorization'))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.validated_data['user'] = self.request.user
        serializer.instance = CommentInteractionService.update_comment_interaction(self.get_object(), **serializer.validated_data)

    def perform_destroy(self, instance):
        CommentInteractionService.delete_comment_interaction(instance)

    def get_queryset(self):
        return CommentInteractionService.get_comment_interactions(self.request.user)

    # @atomic
    # def destroy(self, request, *args, **kwargs):
    #     interaction = self.get_object()
    #     interaction_type = interaction.interaction_type
    #     interaction.comment.user.update_comment_karma(1 if interaction_type == 'upvote' else -1)
    #     return super().destroy(request, *args, **kwargs)

    # def partial_update(self, request, *args, **kwargs):
    #     interaction_type = request.data.get('interaction_type')
    #     interaction = self.get_object()
    #     if interaction_type == 'upvote' and interaction.interaction_type == 'downvote':
    #         interaction.comment.user.update_comment_karma(2)
    #     elif interaction_type == 'downvote' and interaction.interaction_type == 'upvote':
    #         interaction.comment.user.update_comment_karma(-2)
    #     return super().partial_update(request, *args, **kwargs)

class UserUpvotedCommentsView(generics.ListAPIView):
    serializer_class = CommentReadSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    @method_decorator(cache_page(60 * 15, key_prefix="user_upvoted_comment_list"))
    @method_decorator(vary_on_headers('Authorization'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):        
        return CommentService.get_interacted_comments(self.request.user, 'upvote')

class UserDownvotedCommentsView(generics.ListAPIView):
    serializer_class = CommentReadSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    @method_decorator(cache_page(60 * 15, key_prefix="user_downvoted_comment_list"))
    @method_decorator(vary_on_headers('Authorization'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return CommentService.get_interacted_comments(self.request.user, 'downvote')

class CommentReportListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated & CanInteract]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['comment__post__community', 'status']

    @method_decorator(cache_page(60 * 15, key_prefix="comment_report_list"))
    @method_decorator(vary_on_headers('Authorization'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        read_serializer = CommentReportReadSerializer(serializer.instance, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        return CommentReportService.get_comment_reports(self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CommentReportReadSerializer
        return CommentReportWriteSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CommentReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    @method_decorator(cache_page(60 * 15, key_prefix="comment_report_detail"))
    @method_decorator(vary_on_headers('Authorization'))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(CommentReportReadSerializer(serializer.instance, context={'request': request}).data)
    
    def partial_update(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(CommentReportReadSerializer(serializer.instance, context={'request': request}).data)

    def get_queryset(self):
        return CommentReportService.get_comment_reports(self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CommentReportReadSerializer
        return CommentReportWriteSerializer