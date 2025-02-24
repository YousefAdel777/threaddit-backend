# from rest_framework import viewsets, generics
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework.filters import OrderingFilter, SearchFilter
# from .serializers import CommentReportReadSerializer, CommentReportWriteSerializer, TopicSerializer, CommentSerializer, CommentInteractionSerializer, CustomUserSerializer
# from .models import CommentReport, CommentInteraction, Comment
# from communities.models import Community, Ban, Member, Topic, Favorite
# from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
# from .permissions import IsAuthorOrReadOnly, IsModeratorOrReadOnly
# from rest_framework.views import APIView
# from rest_framework import status
# from .pagination import CustomPagination
# from rest_framework.response import Response
# from django.db.transaction import atomic
# from django.db.models import Count, Case, When, F, Exists, OuterRef, Value, Subquery, Prefetch, Q
# from django.db.models.functions import Coalesce
# from django.db.models.fields import BooleanField, IntegerField
# import requests
# from bs4 import BeautifulSoup
# import random
# from datetime import timedelta
# from django.utils import timezone
# from django.contrib.auth import get_user_model
# User = get_user_model()

# def annotate_comments(user=None):
#     if user.is_authenticated:
#         queryset = Comment.objects.select_related('post', 'user').prefetch_related('comment_interactions').annotate(
#             upvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='upvote', then=1))), 0),
#             downvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='downvote', then=1))), 0),
#             interaction_diff=F('upvotes') - F('downvotes'),
#             interaction_id=Subquery(
#                 CommentInteraction.objects.filter(comment=OuterRef('pk'), user=user).values('id')[:1],
#                 output_field=IntegerField()
#             ),
#             is_upvoted=Exists(
#                 CommentInteraction.objects.filter(comment=OuterRef('pk'), user=user, interaction_type='upvote')
#             ),
#             is_downvoted=Exists(
#                 CommentInteraction.objects.filter(comment=OuterRef('pk'), user=user, interaction_type='downvote')
#             )
#         ).prefetch_related(
#             Prefetch(
#                 'replies',  # Recursively fetch nested replies
#                 queryset=annotate_comments(user=user),  # Recursion happens here
#                 to_attr='annotated_replies'  # Store prefetched replies as 'annotated_replies'
#             )
#         )
#     else:
#         queryset = Comment.objects.select_related('post', 'user').prefetch_related('comment_interactions').annotate(
#             upvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='upvote', then=1))), 0),
                # upvotes = Coalesce(Count(comment_interactions__interaction_type='upvote'), 0),
                #downvotes = Coalesce(Count(comment_interactions__interaction_type='downvote'), 0),
#             downvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='downvote', then=1))), 0),
#             interaction_diff=F('upvotes') - F('downvotes'),
#             interaction_id=Value(None, IntegerField()),
#             is_upvoted=Value(False, BooleanField()),
#             is_downvoted=Value(False, BooleanField())
#         ).prefetch_related(
#             Prefetch(
#                 'replies',  # Recursively fetch nested replies
#                 queryset=annotate_comments(user=user),  # Recursion happens here
#                 to_attr='annotated_replies'  # Store prefetched replies as 'annotated_replies'
#             )
#         )
#     return queryset

# class PostListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     queryset = Post.objects.select_related('user', 'community').prefetch_related('attachments', 'interactions', 'comments')
#     pagination_class = CustomPagination
#     filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
#     filterset_fields = ['community', 'user', 'status']
#     ordering_fields = ['created_at', 'interaction_diff_ordered']
#     search_fields = ['title', 'content', 'community__name', 'user__username']

#     def get_serializer_class(self):
#         if self.request.method == 'GET':
#             return PostSerializer
#         return PostWriteSerializer

#     @atomic
#     def perform_create(self, serializer):
#         status = 'accepted' if serializer.validated_data.get('community') is None else 'pending'
#         files = serializer.validated_data.pop('attachments', [])
#         serializer.save(user=self.request.user, status=status)
#         attachments = [
#             Attachment(file=file['file'], file_type=file['file_type'], post=serializer.instance)
#             for file in files
#         ]
#         Attachment.objects.bulk_create(attachments)

#     # @atomic
#     # def create(self, request, *args, **kwargs):
#     #     serializer = self.get_serializer(data=request.data)
#     #     serializer.is_valid(raise_exception=True)
#     #     self.perform_create(serializer)
#     #     return Response(serializer.data, status=status.HTTP_201_CREATED)


#     def get_queryset(self):
#         return Post.objects.select_related('user', 'community').prefetch_related('attachments', 'interactions', 'comments').annotate(
#             upvotes=Coalesce(Count(Case(When(interactions__interaction_type='upvote', then=1))), 0),
#             downvotes=Coalesce(Count(Case(When(interactions__interaction_type='downvote', then=1))), 0),
#             interaction_diff_ordered=F('upvotes') - F('downvotes'),
#         )

# class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = PostSerializer
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     queryset = Post.objects.select_related('user', 'community').prefetch_related('attachments', 'interactions', 'comments').all()
#     filter_backends = [DjangoFilterBackend, OrderingFilter]
#     filterset_fields = ['community', 'user']
#     ordering_fields = ['created_at']

#     # def get_queryset(self):
#     #     if self.request.user.is_authenticated:
#     #         posts = Post.objects.select_related('user', 'community').prefetch_related('attachments', 'interactions', 'comments').annotate(
#     #             upvotes=Coalesce(Count(Case(When(interactions__interaction_type='upvote', then=1)), distinct=True), 0),
#     #             downvotes=Coalesce(Count(Case(When(interactions__interaction_type='downvote', then=1)), distinct=True), 0),
#     #             interaction_diff=F('upvotes') - F('downvotes'),
#     #             saved_post_id=Subquery(SavedPost.objects.filter(user=self.request.user, post=OuterRef('pk')).values('id')[:1], IntegerField()),
#     #             comments_count=Count('comments'),
#     #             interaction_id=Subquery(Interaction.objects.filter(post=OuterRef('pk'), user=self.request.user).values('id')[:1], IntegerField()),
#     #             is_upvoted=Exists(Interaction.objects.filter(post=OuterRef('pk'), user=self.request.user, interaction_type='upvote')),
#     #             is_downvoted=Exists(Interaction.objects.filter(post=OuterRef('pk'), user=self.request.user, interaction_type='downvote'))
#     #         )
#     #     else:
#     #         posts = Post.objects.select_related('user', 'community').prefetch_related('attachments', 'interactions', 'comments').annotate(
#     #             upvotes=Coalesce(Count(Case(When(interactions__interaction_type='upvote', then=1)), distinct=True), 0),
#     #             downvotes=Coalesce(Count(Case(When(interactions__interaction_type='downvote', then=1)), distinct=True), 0),
#     #             interaction_diff=F('upvotes') - F('downvotes'),
#     #             saved_post_id=Value(None, IntegerField()),
#     #             comments_count=Count('comments'),
#     #             interaction_id=Value(None, IntegerField()),
#     #             is_upvoted=Value(False, BooleanField()),
#     #             is_downvoted=Value(False, BooleanField())
#     #         )
#     #     return posts

# class CommentListCreateView(generics.ListCreateAPIView):
#     serializer_class = CommentSerializer
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     pagination_class = CustomPagination
#     # queryset = Comment.objects.select_related('post', 'user').prefetch_related('comment_interactions')
#     filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
#     filterset_fields = ['post', 'user']
#     ordering_fields = ['created_at', 'interaction_diff_ordered']

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)
    
#     def get_queryset(self):
#         # return Comment.objects.select_related('post', 'user').prefetch_related('comment_interactions')
#         comments_queryset = (
#             Comment.objects.filter(parent__isnull=True)  # Get comments for the specific post
#             .select_related('post', 'user')
#             .prefetch_related('comment_interactions', 'replies')
#             .annotate(
#                 upvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='upvote', then=1))), 0),
#                 downvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='downvote', then=1))), 0),
#                 interaction_diff_ordered=F('upvotes') - F('downvotes'),
#             )
#             # .annotate(
#             #     upvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='upvote', then=1))), 0),
#             #     downvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='downvote', then=1))), 0),
#             #     interaction_diff=F('upvotes') - F('downvotes'),
#             #     interaction_id=Subquery(
#             #         CommentInteraction.objects.filter(comment=OuterRef('pk'), user=user).values('id')[:1],
#             #         output_field=IntegerField()
#             #     ),
#             #     is_upvoted=Exists(
#             #         CommentInteraction.objects.filter(comment=OuterRef('pk'), user=user, interaction_type='upvote')
#             #     ),
#             #     is_downvoted=Exists(
#             #         CommentInteraction.objects.filter(comment=OuterRef('pk'), user=user, interaction_type='downvote')
#             #     )
#             # )
#         )

#         return comments_queryset
        # if self.request.user.is_authenticated:
            
        #     replies = Comment.objects.select_related('post', 'user').prefetch_related('comment_interactions').annotate(
        #         upvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='upvote', then=1))), 0),
        #         downvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='downvote', then=1))), 0),
        #         interaction_diff=F('upvotes') - F('downvotes'),
        #         interaction_id=Subquery(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user).values('id')[:1], IntegerField()),
        #         is_upvoted=Exists(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user, interaction_type='upvote')),
        #         is_downvoted=Exists(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user, interaction_type='downvote'))
        #     )

        #     comments = Comment.objects.select_related('post', 'user').prefetch_related(Prefetch('replies', queryset=replies, to_attr='annotated_replies')).annotate(
        #         upvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='upvote', then=1))), 0),
        #         downvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='downvote', then=1))), 0),
        #         interaction_diff=F('upvotes') - F('downvotes'),
        #         interaction_id=Subquery(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user).values('id')[:1], IntegerField()),
        #         is_upvoted=Exists(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user, interaction_type='upvote')),
        #         is_downvoted=Exists(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user, interaction_type='downvote'))
        #     ).filter(parent__isnull=True)

        #     # comments = Comment.objects.select_related('post', 'user').prefetch_related('comment_interactions', 'replies').annotate(
        #     #     upvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='upvote', then=1))), 0),
        #     #     downvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='downvote', then=1))), 0),
        #     #     interaction_diff=F('upvotes') - F('downvotes'),
        #     #     interaction_id=Subquery(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user).values('id')[:1], IntegerField()),
        #     #     is_upvoted=Exists(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user, interaction_type='upvote')),
        #     #     is_downvoted=Exists(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user, interaction_type='downvote'))
        #     # ).filter(parent__isnull=True)
        # else:
        #     comments = Comment.objects.select_related('post', 'user').prefetch_related('comment_interactions', 'replies').annotate(
        #         upvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='upvote', then=1))), 0),
        #         downvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='downvote', then=1))), 0),
        #         interaction_diff=F('upvotes') - F('downvotes'),
        #         interaction_id=Value(None, IntegerField()),
        #         is_upvoted=Value(False, BooleanField()),
        #         is_downvoted=Value(False, BooleanField())
        #     ).filter(parent__isnull=True)
        # return comments

    # def list(self, request, *args, **kwargs):
    #     comments = Comment.objects.select_related('post', 'user').prefetch_related('comment_interactions')
    #     annotate_comments(comments, self.request.user)
    #     serializer = self.get_serializer(comments, many=True)
    #     return Response(serializer.data)

# class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = CommentSerializer
#     permission_classes = [IsAuthenticatedOrReadOnly]

#     def get_queryset(self):
#         # if self.request.user.is_authenticated:
#         return Comment.objects.select_related('post', 'user').prefetch_related('comment_interactions', 'replies')
            # Prefetch replies recursively
            # replies_prefetch = Prefetch(
            #     'replies',  # assuming 'replies' is the related_name for the parent-child relation
            #     queryset=Comment.objects.annotate(
            #         upvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='upvote', then=1))), 0),
            #         downvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='downvote', then=1))), 0),
            #         interaction_diff=F('upvotes') - F('downvotes'),
            #         interaction_id=Subquery(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user).values('id')[:1], IntegerField()),
            #         is_upvoted=Exists(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user, interaction_type='upvote')),
            #         is_downvoted=Exists(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user, interaction_type='downvote'))
            #     ),
            #     to_attr='annotated_replies'  # custom attribute for prefetched replies
            # )

            # Main query for top-level comments with prefetching of replies
            # comments = Comment.objects.filter(parent__isnull=True).annotate(
            #     upvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='upvote', then=1))), 0),
            #     downvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='downvote', then=1))), 0),
            #     interaction_diff=F('upvotes') - F('downvotes'),
            #     interaction_id=Subquery(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user).values('id')[:1], IntegerField()),
            #     is_upvoted=Exists(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user, interaction_type='upvote')),
            #     is_downvoted=Exists(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user, interaction_type='downvote'))
            # ).prefetch_related(replies_prefetch)
            # replies = Comment.objects.select_related('post', 'user').prefetch_related('comment_interactions').annotate(
            #     upvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='upvote', then=1))), 0),
            #     downvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='downvote', then=1))), 0),
            #     interaction_diff=F('upvotes') - F('downvotes'),
            #     interaction_id=Subquery(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user).values('id')[:1], IntegerField()),
            #     is_upvoted=Exists(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user, interaction_type='upvote')),
            #     is_downvoted=Exists(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user, interaction_type='downvote'))
            # )

            # comments = Comment.objects.select_related('post', 'user').prefetch_related(Prefetch('replies', queryset=replies, to_attr='annotated_replies')).annotate(
            #     upvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='upvote', then=1))), 0),
            #     downvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='downvote', then=1))), 0),
            #     interaction_diff=F('upvotes') - F('downvotes'),
            #     interaction_id=Subquery(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user).values('id')[:1], IntegerField()),
            #     is_upvoted=Exists(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user, interaction_type='upvote')),
            #     is_downvoted=Exists(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user, interaction_type='downvote'))
            # )
            # comments = Comment.objects.select_related('post', 'user').prefetch_related('comment_interactions', 'replies').annotate(
            #     upvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='upvote', then=1))), 0),
            #     downvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='downvote', then=1))), 0),
            #     interaction_diff=F('upvotes') - F('downvotes'),
            #     interaction_id=Subquery(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user).values('id')[:1], IntegerField()),
            #     is_upvoted=Exists(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user, interaction_type='upvote')),
            #     is_downvoted=Exists(CommentInteraction.objects.filter(comment=OuterRef('pk'), user=self.request.user, interaction_type='downvote'))
            # ).filter(parent__isnull=True)
        # else:
        #     comments = Comment.objects.select_related('post', 'user').prefetch_related('comment_interactions', 'replies').annotate(
        #         upvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='upvote', then=1))), 0),
        #         downvotes=Coalesce(Count(Case(When(comment_interactions__interaction_type='downvote', then=1))), 0),
        #         interaction_diff=F('upvotes') - F('downvotes'),
        #         interaction_id=Value(None, IntegerField()),
        #         is_upvoted=Value(False, BooleanField()),
        #         is_downvoted=Value(False, BooleanField())
        #     ).filter(parent__isnull=True)
        # return comments

# class CommunityListCreateView(generics.ListCreateAPIView):
#     serializer_class = CommunitySerializer
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     pagination_class = CustomPagination
#     filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
#     search_fields = ['name']

#     @atomic
#     def create(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         Member.objects.create(user=request.user, community=serializer.instance, is_moderator=True)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
    
#     def get_queryset(self):
#         if self.request.user.is_authenticated:
#             communities = Community.objects.prefetch_related('members', 'topics', 'favorites', 'rules').annotate(
#                 members_count=Count('members'),
#                 is_member=Exists(Member.objects.filter(user=self.request.user, community=OuterRef('pk'))),
#                 member_id=Subquery(Member.objects.filter(user=self.request.user, community=OuterRef('pk')).values('id')[:1], IntegerField()),
#                 is_favorite=Exists(Favorite.objects.filter(user=self.request.user, community=OuterRef('pk')))
#             ).order_by('name')
#         else:
#             communities = Community.objects.prefetch_related('members', 'topics', 'favorites', 'rules').annotate(
#                 members_count=Count('members'),
#                 is_member=Value(False, BooleanField()),
#                 member_id=Value(None, IntegerField()),
#                 is_favorite=Value(False, BooleanField())
#             )
#         return communities

# class CommunityDetailView(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = CommunitySerializer
#     # permission_classes = [IsAuthorOrReadOnly]
#     def get_queryset(self):
#         if self.request.user.is_authenticated:
#             communities = Community.objects.prefetch_related('members', 'topics', 'favorites', 'rules').annotate(
#                 members_count=Count('members'),
#                 is_member=Exists(Member.objects.filter(user=self.request.user, community=OuterRef('pk'))),
#                 member_id=Subquery(Member.objects.filter(user=self.request.user, community=OuterRef('pk')).values('id')[:1], IntegerField()),
#                 is_favorite=Exists(Favorite.objects.filter(user=self.request.user, community=OuterRef('pk')))
#             ).order_by('name')
#         else:
#             communities = Community.objects.prefetch_related('members', 'topics', 'favorites', 'rules').annotate(
#                 members_count=Count('members'),
#                 is_member=Value(False, BooleanField()),
#                 member_id=Value(None, IntegerField()),
#                 is_favorite=Value(False, BooleanField())
#             )
#         return communities

# class UserCommunitiesView(generics.ListAPIView):
#     serializer_class = CommunitySerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         communities = Community.objects.prefetch_related('members', 'topics').annotate(
#             members_count=Count('members'),
#             is_member=Exists(Member.objects.filter(user=self.request.user, community=OuterRef('pk'))),
#             member_id=Subquery(Member.objects.filter(user=self.request.user, community=OuterRef('pk')).values('id')[:1], IntegerField()),
#             is_favorite=Exists(Favorite.objects.filter(user=self.request.user, community=OuterRef('pk')))
#         ).order_by('name')
#         return communities.filter(members__user=self.request.user.id)

# class UserModeratedCommunitiesView(generics.ListAPIView):
#     serializer_class = CommunitySerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         communities = Community.objects.prefetch_related('members', 'topics').annotate(
#             members_count=Count('members'),
#             is_member=Exists(Member.objects.filter(user=self.request.user, community=OuterRef('pk'))),
#             member_id=Subquery(Member.objects.filter(user=self.request.user, community=OuterRef('pk')).values('id')[:1], IntegerField()),
#             is_favorite=Exists(Favorite.objects.filter(user=self.request.user, community=OuterRef('pk')))
#         ).order_by('name')
#         return communities.filter(members__user=self.request.user.id, members__is_moderator=True)

# class TopicsViewset(viewsets.ModelViewSet):
#     queryset = Topic.objects.all()
#     serializer_class = TopicSerializer

# class LinkPreviewView(APIView):
#     def get(self, request, *args, **kwargs):
#         url = request.query_params.get('url')
        
#         if not url:
#             return Response({"error": "URL is required"}, status=status.HTTP_400_BAD_REQUEST)
#         try:
#             response = requests.get(url)
#             response.raise_for_status()
#         except requests.RequestException as e:
#             return Response({"error": "Failed to fetch URL"}, status=status.HTTP_400_BAD_REQUEST)
#         soup = BeautifulSoup(response.text, 'html.parser')
        
#         og_title = soup.find("meta", property="og:title")
#         og_description = soup.find("meta", property="og:description")
#         og_image = soup.find("meta", property="og:image")
        
#         title = og_title["content"] if og_title else soup.title.string if soup.title else "No title available"
#         description = og_description["content"] if og_description else ""
#         image = og_image["content"] if og_image else ""
        
#         preview_data = {
#             "title": title,
#             "description": description,
#             "image": image,
#             "url": url,
#         }
#         serializer = LinkPreviewSerializer(data=preview_data)
#         if serializer.is_valid():
#             return Response(serializer.data)
        
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class MemberListCreateView(generics.ListCreateAPIView):
#     serializer_class = MemberSerializer
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
#     queryset = Member.objects.select_related('user').prefetch_related('bans')
#     ordering_fields = ['joined_at', 'is_member']
#     filterset_fields = ['community', 'user']
#     search_fields = ['user__username']

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user, is_moderator=False)

#     def get_queryset(self):
#         # return Member.objects.filter(community__members__user=self.request.user, community__members__is_moderator=True).select_related('user')
#         return Member.objects.select_related('user').prefetch_related('bans')

# class MemberDetailView(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = MemberSerializer
#     permission_classes = [IsModeratorOrReadOnly | IsAuthorOrReadOnly]

#     def get_queryset(self):
#         return Member.objects.select_related('user').prefetch_related('bans')
#         # return Member.objects.filter(community__members__user=self.request.user, community__members__is_moderator=True)
    
#     def get_permissions(self):
#         if self.request.method in ['PUT', 'PATCH']:
#             self.permission_classes = [IsModeratorOrReadOnly]
#         return super().get_permissions()

# class FavoriteListCreateView(generics.ListCreateAPIView):
#     serializer_class = FavoriteSerializer
#     permission_classes = [IsAuthenticated]
#     queryset = Favorite.objects.all()

# class FavoriteDetailView(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = FavoriteSerializer
#     permission_classes = [IsAuthenticated]
#     queryset = Favorite.objects.all()

# class SavedPostListCreateView(generics.ListCreateAPIView):
#     serializer_class = SavedPostSerializer
#     permission_classes = [IsAuthenticated]
#     pagination_class = CustomPagination

#     def get_queryset(self):
#         return SavedPost.objects.filter(user=self.request.user)

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

# class SavedPostDetailView(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = SavedPostSerializer
#     permission_classes = [IsAuthenticated]
    
#     def get_queryset(self):
#         return SavedPost.objects.filter(user=self.request.user)

# class PostInteractionListCreateView(generics.ListCreateAPIView):
#     serializer_class = PostInteractionSerializer
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     queryset = PostInteraction.objects.select_related('user', 'post').all()

#     @atomic
#     def create(self, request, *args, **kwargs):
#         interaction_type = request.data.get('interaction_type')
#         post = request.data.get('post')
#         user = Post.objects.get(pk=post).user
#         user.update_post_karma(1 if interaction_type == 'upvote' else -1)
#         return super().create(request, *args, **kwargs)

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

# class InteractionDetailView(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = PostInteractionSerializer
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     queryset = PostInteraction.objects.select_related('user', 'post').all()

#     @atomic
#     def destroy(self, request, *args, **kwargs):
#         interaction = self.get_object()
#         interaction_type = interaction.interaction_type
#         interaction.post.user.update_post_karma(-1 if interaction_type == 'upvote' else 1)
#         return super().destroy(request, *args, **kwargs)

#     @atomic
#     def partial_update(self, request, *args, **kwargs):
#         interaction_type = request.data.get('interaction_type')
#         interaction = self.get_object()
#         if interaction_type == 'upvote' and interaction.interaction_type == 'downvote':
#             interaction.post.user.update_post_karma(2)
#         elif interaction_type == 'downvote' and interaction.interaction_type == 'upvote':
#             interaction.post.user.update_post_karma(-2)
#         return super().partial_update(request, *args, **kwargs)

# class CommentInteractionListCreateView(generics.ListCreateAPIView):
#     serializer_class = CommentInteractionSerializer
#     permission_classes = [IsAuthenticated]
#     queryset = CommentInteraction.objects.all()

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

#     @atomic
#     def create(self, request, *args, **kwargs):
#         interaction_type = request.data.get('interaction_type')
#         comment = request.data.get('comment')
#         user = Comment.objects.get(pk=comment).user
#         user.update_comment_karma(1 if interaction_type == 'upvote' else -1)
#         return super().create(request, *args, **kwargs)


# class CommentInteractionDetailView(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = CommentInteractionSerializer
#     permission_classes = [IsAuthenticated]
#     queryset = CommentInteraction.objects.all()

#     @atomic
#     def destroy(self, request, *args, **kwargs):
#         interaction = self.get_object()
#         interaction_type = interaction.interaction_type
#         interaction.comment.user.update_comment_karma(1 if interaction_type == 'upvote' else -1)
#         return super().destroy(request, *args, **kwargs)

#     def partial_update(self, request, *args, **kwargs):
#         interaction_type = request.data.get('interaction_type')
#         interaction = self.get_object()
#         if interaction_type == 'upvote' and interaction.interaction_type == 'downvote':
#             interaction.comment.user.update_comment_karma(2)
#         elif interaction_type == 'downvote' and interaction.interaction_type == 'upvote':
#             interaction.comment.user.update_comment_karma(-2)
#         return super().partial_update(request, *args, **kwargs)

# class FollowCreateView(generics.ListCreateAPIView):
#     serializer_class = FollowSerializer
#     # permission_classes = [IsAuthenticated]
#     queryset = Follow.objects.all()

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

# class FollowDeletelView(generics.DestroyAPIView):
#     serializer_class = FollowSerializer
#     permission_classes = [IsAuthenticated]
#     queryset = Follow.objects.all()

# class BlockCreateView(generics.CreateAPIView):
#     serializer_class = BlockSerializer
#     permission_classes = [IsAuthenticated]
#     queryset = Block.objects.all()

#     def perform_create(self, serializer):
#         blocked_user = serializer.validated_data['blocked_user']
#         follow_id = blocked_user.get_follow_id(self.request.user)
#         if follow_id:
#             Follow.objects.get(id=follow_id).delete()
#         serializer.save(user=self.request.user)

# class BlockDeleteView(generics.DestroyAPIView):
#     serializer_class = BlockSerializer
#     permission_classes = [IsAuthenticated]
#     queryset = Block.objects.all()

# class UserUpvotedPostsView(generics.ListAPIView):
#     serializer_class = PostSerializer
#     permission_classes = [IsAuthenticated]
#     pagination_class = CustomPagination

#     def get_queryset(self):
#         return Post.objects.filter(
#             interactions__user=self.request.user,
#             interactions__interaction_type='upvote'
#         )

# class UserDownvotedPostsView(generics.ListAPIView):
#     serializer_class = PostSerializer
#     permission_classes = [IsAuthenticated]
#     pagination_class = CustomPagination

#     def get_queryset(self):
#         return Post.objects.filter(
#             interactions__user=self.request.user,
#             interactions__interaction_type='downvote'
#         )

# class RuleListCreateView(generics.ListCreateAPIView):
#     serializer_class = RuleSerializer
#     permission_classes = [IsModeratorOrReadOnly]
#     queryset = Rule.objects.all()

# class RuleDetailView(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = RuleSerializer
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     queryset = Rule.objects.all()

# class BanListCreateView(generics.ListCreateAPIView):
#     serializer_class = BanSerializer
#     permission_classes = [IsModeratorOrReadOnly]
#     queryset = Ban.objects.select_related('member').all()

# class BanDetailView(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = BanSerializer
#     permission_classes = [IsModeratorOrReadOnly]
#     queryset = Ban.objects.select_related('member').all()

# class FeedView(generics.ListAPIView):
#     serializer_class = PostSerializer
#     pagination_class = CustomPagination
#     def get_queryset(self):
#         if self.request.user.is_authenticated:
#             communities_posts = list(Post.objects.exclude(user=self.request.user).filter(community__members__user=self.request.user, created_at__gte=timezone.now() - timedelta(days=3)).order_by('?', '-created_at'))
#             recommended_posts = list(Post.objects.exclude(user=self.request.user).exclude(community__members__user=self.request.user, created_at__gte=timezone.now() - timedelta(days=3)).order_by('?', '-created_at'))
#             posts = recommended_posts + communities_posts
#             random.shuffle(posts)
#             return posts
#         else:
#             return Post.objects.filter(created_at__gte=timezone.now() - timedelta(days=3)).order_by('?', '-created_at')

# class PopularView(generics.ListAPIView):
#     serializer_class = PostSerializer
#     pagination_class = CustomPagination
#     def get_queryset(self):
#         return Post.objects.filter(created_at__gte=timezone.now() - timedelta(days=1)).annotate(
#             upvotes=Coalesce(Count(Case(When(interactions__interaction_type='upvote', then=1))), 0),
#             downvotes=Coalesce(Count(Case(When(interactions__interaction_type='downvote', then=1))), 0),
#             interaction_diff=F('upvotes') - F('downvotes')
#         ).order_by('-interaction_diff', '-created_at')

# class PostReportListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#     def get_serializer_class(self):
#         if self.request.method == 'GET':
#             return PostReportReadSerializer
#         return PostReportWriteSerializer
    
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

#     def get_queryset(self):
#         return PostReport.objects.select_related('user', 'post').filter(
#             post__community__members__user=self.request.user, 
#             post__community__members__is_admin=True
#         )

# class PostReportDetailView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return PostReport.objects.select_related('user', 'post').filter(
#             post__community__members__user=self.request.user, 
#             post__community__members__is_admin=True
#         )

#     def get_serializer_class(self):
#         if self.request.method == 'GET':
#             return PostReportReadSerializer
#         return PostReportWriteSerializer

# class CommentReportListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return CommentReport.objects.select_related('user', 'comment').filter(
#             comment__post__community__members=self.request.user,
#             comment__post__community__members__is_admin=True
#         )
    
#     def get_serializer_class(self):
#         if self.request.method == 'GET':
#             return CommentReportReadSerializer
#         return CommentReportWriteSerializer
    
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

# class CommentReportDetailView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return CommentReport.objects.select_related('user', 'comment').filter(
#             comment__post__community__members=self.request.user,
#             comment__post__community__members__is_admin=True
#         )
    
#     def get_serializer_class(self):
#         if self.request.method == 'GET':
#             return CommentReportReadSerializer
#         return CommentReportWriteSerializer