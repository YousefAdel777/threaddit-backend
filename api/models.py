# from django.db import models
# from django.utils import timezone
# from django.contrib.auth import get_user_model
# User = get_user_model()
# from posts.models import Post
# class Topic(models.Model):
#     name = models.CharField(max_length=255, unique=True)
#     description = models.TextField()

#     def __str__(self):
#         return self.name

# class Community(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
#     name = models.CharField(max_length=255, unique=True)
#     description = models.TextField()
#     banner = models.ImageField(upload_to='banners', blank=True, null=True)
#     icon = models.ImageField(upload_to='icons', blank=True, null=True)
#     topics = models.ManyToManyField(Topic)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.name
    
#     def get_favorite_id(self, user):
#         try:
#             return self.favorites.get(user=user).id
#         except:
#             return None

#     def get_is_moderator(self, user):
#         if not user.is_authenticated:
#             return False
#         return self.members.filter(is_moderator=True, user=user).exists()

# class Member(models.Model):
#     is_moderator = models.BooleanField(default=False)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='members')
#     joined_at = models.DateTimeField(auto_now_add=True)

#     # @property
#     # def ban_id(self):
#     #     return self.bans.id

# class Post(models.Model):
#     POST_STATUS = [
#         ('pending', 'Pending'), 
#         ('accepted', 'Accepted'), 
#         ('removed', 'Removed')
#     ]

#     POST_TYPES = [
#         ('text', 'Text'), 
#         ('media', 'Media'), 
#         ('link', 'Link'), 
#         ('poll', 'Poll')
#     ]

#     title = models.CharField(max_length=255)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     status = models.CharField(max_length=255, choices=POST_STATUS, default='pending')
#     content = models.TextField(null=True, blank=True, default=None)
#     type = models.CharField(max_length=255, choices=POST_TYPES)
#     link = models.URLField(max_length=255, null=True, blank=True, default=None)
#     community = models.ForeignKey(Community, on_delete=models.CASCADE, null=True, blank=True, default=None)
#     created_at = models.DateTimeField(auto_now_add=True)
#     is_spoiler = models.BooleanField(default=False)
#     is_nsfw = models.BooleanField(default=False)

#     def __str__(self):
#         return self.title

#     @property
#     def interaction_diff(self):
#         return self.interactions.filter(interaction_type='upvote').count() - self.interactions.filter(interaction_type='downvote').count()
    
#     @property
#     def comments_count(self):
#         return self.comments.count()
    
#     def get_interaction_id(self, user):
#         try:
#             return self.interactions.get(user=user).id
#         except:
#             return None
    
#     def get_is_upvoted(self, user):
#         if not user.is_authenticated:
#             return False
#         return self.interactions.filter(user=user, interaction_type='upvote').exists()
    
#     def get_is_downvoted(self, user):
#         if not user.is_authenticated:
#             return False
#         return self.interactions.filter(user=user, interaction_type='downvote').exists()
    
#     def get_saved_post_id(self, user):
#         try:
#             return SavedPost.objects.get(user=user, post=self).id
#         except:
#             return None

# class PostReport(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_post_reports')
#     post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_reports')
#     reason = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.post
    

# class Attachment(models.Model):
#     FILE_TYPES = [
#         ('image', 'Image'), 
#         ('video', 'Video')
#     ]

#     file = models.FileField(upload_to='attachments')
#     file_type = models.CharField(max_length=255, choices=FILE_TYPES)
#     post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='attachments')

# class PostInteraction(models.Model):
#     INTERACTION_TYPES = [
#         ('upvote', 'Upvote'), 
#         ('downvote', 'Downvote')
#     ]

#     interaction_type = models.CharField(max_length=255, choices=INTERACTION_TYPES, db_index=True)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_interactions')

# class CommentInteraction(models.Model):
#     INTERACTION_TYPES = [
#         ('upvote', 'Upvote'), 
#         ('downvote', 'Downvote')
#     ]

#     interaction_type = models.CharField(max_length=255, choices=INTERACTION_TYPES, db_index=True)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_interactions')

# class Favorite(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='favorites')

# class SavedPost(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     post = models.ForeignKey(Post, on_delete=models.CASCADE)

# class Follow(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
#     followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followed')

# class Block(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     blocked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_users')

# class Rule(models.Model):
#     title = models.CharField(max_length=255)
#     description = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='rules')

#     def __str__(self):        
#         return self.title

# class Ban(models.Model):
#     member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='bans')
#     reason = models.TextField()
#     banned_at = models.DateTimeField(auto_now_add=True)
#     expires_at = models.DateTimeField(null=True, blank=True)
#     is_permanent = models.BooleanField(default=False)

#     def __str__(self):        
#         return self.reason
    
#     @property
#     def is_active(self):
#         return self.is_permanent or self.expires_at > timezone.now()