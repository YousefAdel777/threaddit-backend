from .models import Comment, CommentInteraction
from django.db.models import Count, F, Q
from django.db.models.functions import Coalesce
from .models import CommentReport
from django.utils import timezone
from django.db.transaction import atomic

class CommentService:

    @classmethod
    def get_comment(cls, comment_id, user):
        comments = Comment.objects.filter(id=comment_id)
        comments = cls._exclude_blocked(comments, user)
        comments = cls._exclude_banned(comments, user)
        comments = cls._optimize_comments_queryset(comments)
        comments = cls._annotate_comments(comments)
        return comments.first()

    @classmethod
    def get_annotated_comments(cls, user):
        comments = Comment.objects.all()
        comments = cls._exclude_blocked(comments, user)
        comments = cls._exclude_banned(comments, user)
        comments = cls._optimize_comments_queryset(comments)
        comments = cls._annotate_comments(comments)
        return comments
    
    @classmethod
    def get_annotated_replies(cls, comment_id, user):
        comments = Comment.objects.filter(parent__id=comment_id)
        comments = cls._exclude_blocked(comments, user)
        comments = cls._exclude_banned(comments, user)
        comments = cls._optimize_comments_queryset(comments)
        comments = cls._annotate_comments(comments)
        return comments

    @classmethod
    def get_interacted_comments(cls, user, interaction_type):
        comments = Comment.objects.filter(
            comment_interactions__user=user,
            comment_interactions__interaction_type=interaction_type
        )
        comments = cls._exclude_blocked(comments, user)
        comments = cls._exclude_banned(comments, user)
        comments = cls._annotate_comments(cls._optimize_comments_queryset(comments))
        return comments
    
    @classmethod
    def get_parent_comments(cls, user):
        comments = Comment.objects.filter(parent__isnull=True)
        comments = cls._exclude_blocked(comments, user)
        comments = cls._exclude_banned(comments, user)
        comments = cls._optimize_comments_queryset(comments)
        comments = cls._annotate_comments(comments)
        return comments
    
    @classmethod
    def _exclude_blocked(cls, comments, user):
        if not user.is_authenticated:
            return comments
        return comments.exclude(user__blocked_by__blocked_by=user).exclude(user__blocks__blocked_user=user)
    
    @classmethod
    def _exclude_banned(cls, comments, user):
        if not user.is_authenticated:
            return comments
        ban_query = Q(post__community__community_bans__is_permanent=True) | Q(post__community__community_bans__expires_at__gte=timezone.now())
        return comments.exclude(
            ban_query &
            ~Q(user=user) &
            Q(post__community__community_bans__user=user)
        )

    @classmethod
    def _optimize_comments_queryset(cls, comments):
        return comments.select_related('post', 'user').prefetch_related('comment_interactions', 'comment_reports', 'replies')

    @classmethod
    def _annotate_comments(cls, comments):
        return comments.annotate(
            upvotes=Coalesce(Count('comment_interactions', filter=Q(comment_interactions__interaction_type='upvote'), distinct=True), 0),
            downvotes=Coalesce(Count('comment_interactions', filter=Q(comment_interactions__interaction_type='downvote'), distinct=True), 0),
            interaction_diff=F('upvotes') - F('downvotes'),
        )


class CommentInteractionService:

    @staticmethod
    def get_comment_interactions(user):
        return CommentInteraction.objects.filter(user=user)

    @staticmethod
    @atomic
    def create_comment_interaction(**validated_data):
        comment = validated_data.get('comment')
        interaction_type = validated_data.get('interaction_type')
        karma_diff = 1 if interaction_type == 'upvote' else -1
        comment_interaction = CommentInteraction.objects.create(**validated_data)
        comment.user.update_comment_karma(karma_diff)
        return comment_interaction

    @staticmethod
    @atomic
    def update_comment_interaction(interaction, **validated_data):
        interaction_type = validated_data.get('interaction_type')
        if not interaction_type or interaction_type == interaction.interaction_type:
            return interaction
        comment = interaction.comment
        if interaction_type == 'upvote':
            comment.user.update_comment_karma(2)
        elif interaction_type == 'downvote':
            comment.user.update_comment_karma(-2)
        interaction.interaction_type = interaction_type
        interaction.save(update_fields=['interaction_type'])
        return interaction

    @staticmethod
    @atomic
    def delete_comment_interaction(interaction):
        interaction_type = interaction.interaction_type
        karma_diff = 1 if interaction_type == 'upvote' else -1
        comment = interaction.comment
        comment.user.update_comment_karma(karma_diff)
        interaction.delete()

class CommentReportService:
    @classmethod
    def get_comment_reports(cls, user):
        comment_reports = CommentReport.objects.filter(
            Q(comment__post__community__members__user=user) &
            Q(comment__post__community__members__is_moderator=True)
        )
        comment_reports = cls._optimize_comment_reports_queryset(comment_reports)
        return comment_reports

    @staticmethod
    def is_reported(user, comment):
        return CommentReport.objects.filter(user=user, status='pending', comment=comment).exists()
    
    def _optimize_comment_reports_queryset(comment_reports):
        return comment_reports.select_related('user', 'comment')