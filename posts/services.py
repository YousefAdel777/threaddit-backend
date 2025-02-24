from .models import Post, Attachment, PostReport, PostInteraction, SavedPost
from django.db.transaction import atomic
from django.db.models import Count, F, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
import random

class PostService:

    @classmethod
    def get_post(cls, post_id, user):
        posts = Post.objects.filter(pk=post_id)
        posts = cls._exclude_blocked(posts, user)
        posts = cls._exclude_banned(posts, user)
        posts = cls._prefetch_posts(posts)
        posts = cls._annotate_posts(posts)
        return posts.first()

    @classmethod
    def get_posts(cls, user):
        posts = cls.get_filtered_posts(user)
        posts = cls._prefetch_posts(posts)
        return cls._annotate_posts(posts)
    
    @classmethod
    def get_filtered_posts(cls, user):
        posts = Post.objects.all()
        if user.is_authenticated:
            posts = cls._exclude_blocked(posts, user)
            posts = cls._exclude_banned(posts, user)
        return posts
    
    @staticmethod
    @atomic
    def update_post(post_id, **validated_data):
        attachments = validated_data.pop('attachments', None)
        posts = Post.objects.filter(id=post_id)
        posts.update(**validated_data)
        post = posts.first()
        if attachments:
            Attachment.objects.filter(post__id=post_id).delete()
            attachments = [
                Attachment(file_type=attachment['file_type'], file=attachment['file'], post=post) 
                for attachment in attachments
            ]
            Attachment.objects.bulk_create(attachments)
        return post
    
    @staticmethod
    def create_post(**validated_data):
        status = 'accepted' if validated_data.get('community') is None else 'pending'
        files = validated_data.pop('attachments', [])
        post = Post.objects.create(**validated_data, status=status)
        attachments = [
            Attachment(file=file['file'], file_type=file['file_type'], post=post)
            for file in files
        ]
        Attachment.objects.bulk_create(attachments)
        return post

    @classmethod
    def _prefetch_posts(cls, posts):
        return posts.select_related('user', 'community').prefetch_related('attachments', 'post_interactions', 'comments', 'post_reports', 'community__community_bans')

    @classmethod
    def _annotate_posts(cls, posts):        
        return posts.annotate(
            upvotes=Coalesce(Count('post_interactions', filter=Q(post_interactions__interaction_type='upvote'), distinct=True), 0),
            downvotes=Coalesce(Count('post_interactions', filter=Q(post_interactions__interaction_type='downvote'), distinct=True), 0),
            interaction_diff=F('upvotes') - F('downvotes'),
        )
    
    @classmethod
    def _exclude_blocked(cls, posts, user):
        if not user.is_authenticated:
            return posts
        return posts.exclude(user__blocked_by__blocked_by=user).exclude(user__blocks__blocked_user=user)

    @classmethod
    def _exclude_banned(cls, posts, user):
        if not user.is_authenticated:
            return posts
        ban_query = Q(community__community_bans__is_permanent=True) | Q(community__community_bans__expires_at__gte=timezone.now())
        return posts.exclude(
            ban_query &
            ~Q(user=user) &
            Q(community__community_bans__user=user)
        )

    @classmethod
    def get_feed(cls, user):
        if user.is_authenticated:
            communities_posts = Post.objects.filter(community__members__user=user, created_at__gte=timezone.now() - timezone.timedelta(days=3))
            communities_posts = communities_posts.exclude(user=user)
            communities_posts = cls._exclude_blocked(communities_posts, user)
            communities_posts = cls._exclude_banned(communities_posts, user)
            communities_posts = cls._prefetch_posts(communities_posts)
            communities_posts = list(cls._annotate_posts(communities_posts).order_by('?', '-created_at'))
            recommended_posts = Post.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=3)).exclude(community__members__user=user)
            recommended_posts = recommended_posts.exclude(user=user)
            recommended_posts = cls._exclude_blocked(recommended_posts, user)
            recommended_posts = cls._exclude_banned(recommended_posts, user)
            recommended_posts = cls._prefetch_posts(recommended_posts)
            recommended_posts = list(cls._annotate_posts(recommended_posts).order_by('?', '-created_at'))
            posts = recommended_posts + communities_posts
            random.shuffle(posts)
            return posts
        else:
            return cls._annotate_posts((cls._prefetch_posts(Post.objects)).filter(created_at__gte=timezone.now() - timezone.timedelta(days=3)).order_by('?', '-created_at'))

    @classmethod
    def get_interacted_posts(cls, user, interaction_type):
        posts = Post.objects.filter(post_interactions__user=user, post_interactions__interaction_type=interaction_type)
        posts = cls._exclude_blocked(posts, user)
        posts = cls._exclude_banned(posts, user)
        posts = cls._prefetch_posts(posts)
        posts = cls._annotate_posts(posts)
        return posts
    
    @classmethod
    def get_saved_posts(cls, user):
        posts = Post.objects.filter(id__in=SavedPostService.get_saved_posts(user).values_list('post'))
        posts = cls._exclude_blocked(posts, user)
        posts = cls._exclude_banned(posts, user)
        posts = cls._prefetch_posts(posts)
        posts = cls._annotate_posts(posts)
        return posts

class SavedPostService:
    @staticmethod
    def get_saved_posts(user):
        return SavedPost.objects.filter(user=user)

class PostReportService:
    @classmethod
    def get_post_reports(cls, user):
        post_reports = PostReport.objects.filter(
            Q(post__community__members__user=user) &
            Q(post__community__members__is_moderator=True)
        )
        return cls._optimize_post_reports_queryset(post_reports)
    
    @classmethod
    def _optimize_post_reports_queryset(cls, post_reports):        
        return post_reports.select_related('user', 'post')

    @staticmethod
    def is_reported(user_id, post_id):
        return PostReport.objects.filter(user__id=user_id, status='pending', post__id=post_id).exists()

class PostInteractionService:

    @classmethod
    def get_post_interactions(cls, user):
        posts = PostInteraction.objects.filter(user=user)
        return cls._optimize_post_interactions_queryset(posts)
    
    @classmethod
    def _optimize_post_interactions_queryset(cls, posts):
        return posts.select_related('user', 'post')

    @atomic
    @staticmethod
    def create_post_interaction(**validated_data):
        user = validated_data.get('post').user
        interaction_type = validated_data.get('interaction_type')
        post_interaction = PostInteraction.objects.create(**validated_data)
        user.update_post_karma(1 if interaction_type == 'upvote' else -1)
        return post_interaction
    
    @atomic
    @staticmethod
    def update_post_interaction(interaction, **validated_data):
        interaction_type = validated_data.get('interaction_type')
        print(validated_data)
        if not interaction_type or interaction_type == interaction.interaction_type:
            return interaction
        if interaction_type == 'upvote':
            interaction.post.user.update_post_karma(2)
        elif interaction_type == 'downvote':
            interaction.post.user.update_post_karma(-2)
        interaction.interaction_type = interaction_type
        interaction.save(update_fields=['interaction_type'])
        return interaction
    
    @atomic
    @staticmethod
    def delete_post_interaction(interaction):
        interaction_type = interaction.interaction_type
        interaction.post.user.update_post_karma(1 if interaction_type == 'upvote' else -1)
        interaction.delete()