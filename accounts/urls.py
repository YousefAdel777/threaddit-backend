from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.UserListView.as_view(), name='users-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('follows/', views.FollowCreateView.as_view(), name='follows-create'),
    path('follows/<int:pk>/', views.FollowDeleteView.as_view(), name='follows-delete'),
    path('followed-users/', views.FollowedUsersListView.as_view(), name='followed-users-list'),
    path('blocks/', views.BlockCreateView.as_view(), name='blocks-create'),
    path('blocks/<int:pk>/', views.BlockDeleteView.as_view(), name='blocks-delete'),
    path('blocked-users/', views.BlockedUsersListView.as_view(), name='blocked-users-list'),
    path('auth/github/', views.GithubLoginView.as_view(), name='github-login'),
    path('auth/google/', views.GoogleLoginView.as_view(), name='google-login'),
]