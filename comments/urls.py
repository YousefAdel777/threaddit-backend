from django.urls import path
from . import views

urlpatterns = [
    path('comment-reports/', views.CommentReportListCreateView.as_view(), name='comment-report-list'),
    path('comment-reports/<int:pk>/', views.CommentReportDetailView.as_view(), name='comment-report-detail'),
    path('user/upvoted-comments/', views.UserUpvotedCommentsView.as_view(), name='user-upvoted-comments'),
    path('user/downvoted-comments/', views.UserDownvotedCommentsView.as_view(), name='user-downvoted-comments'),
    path('comments-interactions/', views.CommentInteractionListCreateView.as_view(), name='comment-interaction-list'),
    path('comments-interactions/<int:pk>/', views.CommentInteractionDetailView.as_view(), name='comment-interaction-detail'),
    path('comments/', views.CommentListCreateView.as_view(), name='comment-list'),
    path('comments/<int:pk>/', views.CommentDetailView.as_view(), name='comment-detail'),
]