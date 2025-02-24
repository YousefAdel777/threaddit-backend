from django.urls import path
from . import views

urlpatterns = [
    path('posts/', views.PostListCreateView.as_view(), name='post-list'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post-detail'),
    path('post-reports/', views.PostReportListCreateView.as_view(), name='post-report-list'),
    path('post-reports/<int:pk>/', views.PostReportDetailView.as_view(), name='post-report-detail'),
    path('user/upvoted-posts/', views.UserUpvotedPostsView.as_view(), name='user-upvoted-posts'),
    path('user/downvoted-posts/', views.UserDownvotedPostsView.as_view(), name='user-downvoted-posts'),
    path('feed/', views.FeedView.as_view(), name='feed'),
    path('popular/', views.PopularView.as_view(), name='popular-list'),
    path('link-preview/', views.LinkPreviewView.as_view(), name='link-preview'),
    path('saved-posts/', views.SavedPostListCreateView.as_view(), name='saved-post-list'),
    path('saved-posts/<int:pk>/', views.SavedPostDetailView.as_view(), name='saved-post-detail'),
    path('user/saved-posts/', views.UserSavedPostsView.as_view(), name='user-saved-posts'),
    path('interactions/', views.PostInteractionListCreateView.as_view(), name='post-interaction-list'),
    path('interactions/<int:pk>/', views.PostInteractionDetailView.as_view(), name='post-interaction-detail'),
]