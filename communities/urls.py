from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register('topics', views.TopicsViewset, basename='topics')

urlpatterns = [
    path('', include(router.urls)),
    path('members/', views.MemberListCreateView.as_view(), name='member-list-create'),
    path('members/<int:pk>/', views.MemberDetailView.as_view(), name='member-detail'),
    path('favorites/', views.FavoriteListCreateView.as_view(), name='favorite-list-create'),
    path('favorites/<int:pk>/', views.FavoriteDetailView.as_view(), name='favorite-detail'),
    path('rules/', views.RuleListCreateView.as_view(), name='rule-list-create'),
    path('rules/<int:pk>/', views.RuleDetailView.as_view(), name='rule-detail'),
    path('bans/', views.BanListCreateView.as_view(), name='ban-list-create'),
    path('bans/<int:pk>/', views.BanDetailView.as_view(), name='ban-detail'),
    path('communities/', views.CommunityListCreateView.as_view(), name='community-list-create'),
    path('communities/<int:pk>/', views.CommunityDetailView.as_view(), name='community-detail'),
    path('user/communities/', views.UserCommunitiesView.as_view(), name='user-communities'),
    path('user/moderated-communities/', views.UserModeratedCommunitiesView.as_view(), name='user-moderated-communities'),
]