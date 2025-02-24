import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory
from .factories import (
    PostFactory, 
    UserFactory,
    PostInteractionFactory, 
    SavedPostFactory,
    AttachmentFactory,
    PostReportFactory,
    RuleFactory,
    MemberFactory,
    CommunityFactory
)
from posts.serializers import (
    AttachmentSerializer,
    PostWriteSerializer, 
    PostUpdateSerializer,
    PostReadSerializer, 
    PostInteractionSerializer,
    SavedPostSerializer,
    PostReportReadSerializer,
    PostReportWriteSerializer,
    LinkPreviewSerializer
)
from accounts.serializers import CustomUserSerializer
from communities.serializers import RuleSerializer

@pytest.fixture
def serializer_context():
    user = UserFactory()
    request = APIRequestFactory().get('/')
    request.user = user
    return {'request': request}

@pytest.mark.django_db
class TestAttachmentSerializer:
    def test_attachment_serializer_fields(self):
        user = UserFactory()
        post = PostFactory(type='text', user=user)
        attachment = AttachmentFactory(post=post, file='test_file.png', file_type='image')
        serializer = AttachmentSerializer(attachment)
        serializer_data = serializer.data
        assert 'test_file' in serializer_data['file']
        assert serializer_data['file_type'] == 'image'
        assert 'post' not in serializer_data

@pytest.mark.django_db
class TestPostWriteSerializer:
    def test_media_post_with_no_attachments(self):
        user = UserFactory()
        community = CommunityFactory()
        data = {
            'user': user.id,
            'community': community.id,
            'type': 'media',
            'title': 'Test Media Post',
            'content': '',
            'link': '',
            'attachments': []
        }
        serializer = PostWriteSerializer(data=data)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['Media posts must have at least 1 attachment']}

    def test_media_post_with_attachments(self):
        user = UserFactory()
        community = CommunityFactory()
        test_file = SimpleUploadedFile(
            name='test_file.png',
            content=b'file_content',
            content_type='image/png'
        )
        data = {
            'user': user.id,
            'community': community.id,
            'type': 'media',
            'title': 'Test Media Post',
            'content': '',
            'link': '',
            'attachments': [test_file]
        }
        serializer = PostWriteSerializer(data=data)
        assert serializer.is_valid() is True

    def test_media_post_with_invalid_attachments(self):
        user = UserFactory()
        community = CommunityFactory()
        test_file = SimpleUploadedFile(
            name='test_file.txt',
            content=b'file_content',
            content_type='text/plain'
        )
        data = {
            'user': user.id,
            'community': community.id,
            'type': 'media',
            'title': 'Test Media Post',
            'content': '',
            'link': '',
            'attachments': [test_file]
        }
        serializer = PostWriteSerializer(data=data)
        assert serializer.is_valid() is False
        print(serializer.errors)
        assert serializer.errors == {'attachments': [f'Unsupported file type: {test_file.name}']}

    def test_non_media_post_with_attachments(self):
        user = UserFactory()
        community = CommunityFactory()
        test_file = SimpleUploadedFile(
            name='test_file.png',
            content=b'file_content',
            content_type='image/png'
        )
        data = {
            'user': user.id,
            'community': community.id,
            'type': 'text',
            'title': 'Test Text Post',
            'content': 'Test content',
            'link': '',
            'attachments': [test_file]
        }
        serializer = PostWriteSerializer(data=data)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['Only media posts can have attachments']}

    def test_link_post_with_no_link(self):
        user = UserFactory()
        community = CommunityFactory()
        data = {
            'user': user.id,
            'community': community.id,
            'type': 'link',
            'title': 'Test Link Post',
            'content': '',
            'link': '',
            'attachments': []
        }
        serializer = PostWriteSerializer(data=data)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['Link posts must have a link']}

    def test_link_post_with_link(self):
        user = UserFactory()
        community = CommunityFactory()
        data = {
            'user': user.id,
            'community': community.id,
            'type': 'link',
            'title': 'Test Link Post',
            'content': '',
            'link': 'https://example.com',
            'attachments': []
        }
        serializer = PostWriteSerializer(data=data)
        assert serializer.is_valid() is True

    def test_non_link_post_with_link(self):
        user = UserFactory()
        community = CommunityFactory()
        data = {
            'user': user.id,
            'community': community.id,
            'type': 'text',
            'title': 'Test Text Post',
            'content': 'Test content',
            'link': 'https://example.com',
            'attachments': []
        }
        serializer = PostWriteSerializer(data=data)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['Only link posts can have a link']}

    def test_text_post_with_no_content(self):
        user = UserFactory()
        community = CommunityFactory()
        data = {
            'user': user.id,
            'community': community.id,
            'type': 'text',
            'title': 'Test Text Post',
            'content': '',
            'link': '',
            'attachments': []
        }
        serializer = PostWriteSerializer(data=data)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['Text posts must have content']}

    def test_text_post_with_content(self):
        user = UserFactory()
        community = CommunityFactory()
        data = {
            'user': user.id,
            'community': community.id,
            'type': 'text',
            'title': 'Test Text Post',
            'content': 'Test content',
            'link': '',
            'attachments': []
        }
        serializer = PostWriteSerializer(data=data)
        assert serializer.is_valid()

    def test_crosspost_post_with_no_original_post(self):
        user = UserFactory()
        community = CommunityFactory()
        data = {
            'user': user.id,
            'community': community.id,
            'type': 'crosspost',
            'title': 'Test Crosspost Post',
            'content': '',
            'link': '',
            'attachments': [],
        }
        serializer = PostWriteSerializer(data=data)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['Crosspost posts must have an original post']}

    def test_crosspost_post_with_original_post(self):
        user = UserFactory()
        community = CommunityFactory()
        original_post = PostFactory(type='text', user=user, title='Test Original Post', content='Test content')
        data = {
            'user': user.id,
            'community': community.id,
            'type': 'crosspost',
            'title': 'Test Crosspost Post',
            'content': '',
            'link': '',
            'attachments': [],
            'original_post': original_post.id
        }
        serializer = PostWriteSerializer(data=data)
        assert serializer.is_valid()

    def test_non_crosspost_post_with_original_post(self):
        user = UserFactory()
        community = CommunityFactory()
        original_post = PostFactory(type='text', user=user, title='Test Original Post', content='Test content')
        data = {
            'user': user.id,
            'community': community.id,
            'type': 'text',
            'title': 'Test Text Post',
            'content': 'Test content',
            'link': '',
            'attachments': [],
            'original_post': original_post.id
        }
        serializer = PostWriteSerializer(data=data)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['Only crosspost posts can have an original post']}

    def test_crosspost_with_nsfw_original_post(self):
        user = UserFactory()
        community = CommunityFactory()
        original_post = PostFactory(type='text', is_nsfw=True, user=user, title='Test Original Post', content='Test content')
        data = {
            'user': user.id,
            'community': community.id,
            'type': 'crosspost',
            'title': 'Test Crosspost Post',
            'content': '',
            'link': '',
            'attachments': [],
            'original_post': original_post.id
        }
        serializer = PostWriteSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['is_nsfw']

@pytest.mark.django_db
class TestPostUpdateSerializer:
    def test_valid_post_update_serializer(self, serializer_context):
        user = serializer_context['request'].user
        post = PostFactory(user=user, title='test_title', content='test_content', type='text')
        data = {
            'title': 'test_title_updated',
            'content': 'test_content_updated',
            'is_nsfw': True,
            'is_spoiler': True
        }
        serializer = PostUpdateSerializer(post, data=data, context=serializer_context, partial=True)
        assert serializer.is_valid()
        post = serializer.save()
        assert post.title == 'test_title_updated'
        assert post.content == 'test_content_updated'
        assert post.is_nsfw
        assert post.is_spoiler

    def test_update_post_with_invalid_data(self, serializer_context):
        user = user = serializer_context['request'].user
        post = PostFactory(user=user, title='test_title', content='test_content', type='text')
        data = {
            'title': 'test_title_updated',
            'content': '',
        }
        serializer = PostUpdateSerializer(instance=post, data=data, context=serializer_context, partial=True)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['Text posts must have content']}

    def test_update_post_status_as_user(self, serializer_context):
        user = serializer_context['request'].user
        community = CommunityFactory(user=user)
        post = PostFactory(community=community, user=user, title='test_title', content='test_content', type='text', status='pending')
        data = {
            'status': 'accepted',
        }
        serializer = PostUpdateSerializer(post, data=data, context=serializer_context, partial=True)
        assert serializer.is_valid() is False
        print(serializer.errors)
        assert serializer.errors == { 'status': ['You are not a moderator of this community'] }

    def test_update_post_status_as_moderator(self, serializer_context):
        user = serializer_context['request'].user
        community = CommunityFactory(user=user)
        MemberFactory(community=community, user=user, is_moderator=True)
        post = PostFactory(community=community, user=user, title='test_title', content='test_content', type='text', status='pending')
        data = {
            'status': 'accepted',
        }
        serializer = PostUpdateSerializer(post, data=data, context=serializer_context, partial=True)
        assert serializer.is_valid()
        post = serializer.save()
        assert post.status == 'accepted'
    
    def test_update_post_as_moderator_with_invalid_data(self, serializer_context):
        user = serializer_context['request'].user
        user2 = UserFactory()
        community = CommunityFactory(user=user)
        MemberFactory(community=community, user=user, is_moderator=True)
        post = PostFactory(community=community, user=user2, title='test_title', content='test_content', type='text', status='pending')
        data = {
            'title': 'invalid_title',
        }
        serializer = PostUpdateSerializer(post, data=data, context=serializer_context, partial=True)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['Moderators can only change the status of posts']}

    def test_update_post_type_not_allowed(self, serializer_context):
        user = serializer_context['request'].user
        post = PostFactory(user=user, title='test_title', content='test_content', type='text', status='pending')
        data = {
            'type': 'link',
        }
        serializer = PostUpdateSerializer(post, data=data, context=serializer_context, partial=True)
        assert serializer.is_valid()
        post = serializer.save()
        assert post.type == 'text'

    def test_update_post_community_not_allowed(self, serializer_context):
        user = serializer_context['request'].user
        community = CommunityFactory(user=user)
        post = PostFactory(community=None, user=user, title='test_title', content='test_content', type='text', status='pending')
        data = {
            'community': community.id,
        }
        serializer = PostUpdateSerializer(post, data=data, context=serializer_context, partial=True)
        assert serializer.is_valid()
        post = serializer.save()
        assert post.community is None

@pytest.mark.django_db
class TestPostReadSerializer:
    def test_valid_post_read_serializer_fields(self, serializer_context):
        user = serializer_context['request'].user
        post = PostFactory(user=user, is_nsfw=False, is_spoiler=True, title='test_title', content='test_content', type='text')
        serializer = PostReadSerializer(post, context=serializer_context)
        serializer_data = serializer.data
        assert serializer_data['id'] == post.id
        assert serializer_data['user']['id'] == user.id
        assert serializer_data['type'] == 'text'
        assert serializer_data['title'] == 'test_title'
        assert serializer_data['content'] == 'test_content'
        assert serializer_data['is_nsfw'] is False
        assert serializer_data['is_spoiler'] is True
        assert serializer_data['created_at'] is not None
        assert serializer_data['is_author'] is True


@pytest.mark.django_db
class TestPostInteractionSerializer:
    def test_valid_post_interaction_serializer_read_fields(self):
        user = UserFactory()
        post = PostFactory(user=user, title='test_title', content='test_content', type='text')
        post_interaction = PostInteractionFactory(post=post, user=user)
        serializer = PostInteractionSerializer(post_interaction)
        serializer_data = serializer.data
        assert serializer_data['id'] == post_interaction.id
        assert serializer_data['post'] == post.id
        assert serializer_data['user'] == user.id

    def test_valid_post_interaction_serializer_write_fields(self):
        user = UserFactory()
        post = PostFactory(user=user, title='test_title', content='test_content', type='text')
        data = {'interaction_type': 'upvote', 'post': post.id, 'user': user.id}
        serializer = PostInteractionSerializer(data=data)
        assert serializer.is_valid()
        post_interaction = serializer.save()
        assert post_interaction.interaction_type == 'upvote'
        assert post_interaction.post == post
        assert post_interaction.user == user

    def test_unique_together_post_interaction_serializer(self):
        user = UserFactory()
        post = PostFactory(user=user, title='test_title', content='test_content', type='text')
        PostInteractionFactory(post=post, user=user)
        data = {'interaction_type': 'upvote', 'post': post.id, 'user': user.id}
        serializer = PostInteractionSerializer(data=data)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['User has already interacted with this post']}

@pytest.mark.django_db
class TestSavedPostSerializer:
    def test_valid_saved_post_serializer_fields(self):
        user = UserFactory()
        post = PostFactory(user=user, title='test_title', content='test_content', type='text')
        saved_post = SavedPostFactory(user=user, post=post)
        serializer = SavedPostSerializer(saved_post)
        serializer_data = serializer.data
        assert serializer_data['id'] == saved_post.id
        assert serializer_data['user'] == user.id
        assert serializer_data['post'] == post.id

    def test_valid_saved_post_serializer_write_fields(self):
        user = UserFactory()
        post = PostFactory(user=user, title='test_title', content='test_content', type='text')
        data = {'user': user.id, 'post': post.id}
        serializer = SavedPostSerializer(data=data)
        assert serializer.is_valid()
        saved_post = serializer.save()
        assert saved_post.user == user
        assert saved_post.post == post

    def test_unique_together_saved_post_serializer(self):
        user = UserFactory()
        post = PostFactory(user=user, title='test_title', content='test_content', type='text')
        SavedPostFactory(user=user, post=post)
        data = {'user': user.id, 'post': post.id}
        serializer = SavedPostSerializer(data=data)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['User has already saved this post']}

@pytest.mark.django_db
class TestPostReportWriteSerializer:

    def test_valid_post_report_serailizer(self, serializer_context):
        user = serializer_context['request'].user
        community = CommunityFactory()
        post = PostFactory(title="test_post", type="text", content="test_content", community=community)
        rule = RuleFactory(community=community)
        data = {"post": post.id, "user": user.id, "violated_rule": rule.id, 'reason': 'test_reason'}
        serializer = PostReportWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid()
        report = serializer.save()
        assert report.post == post
        assert report.user == user
        assert report.violated_rule == rule
        assert report.reason == 'test_reason'

    def test_violated_rule_not_in_community(self, serializer_context):
        user = serializer_context['request'].user
        community = CommunityFactory()
        community2 = CommunityFactory()
        post = PostFactory(title="test_post", type="text", content="test_content", community=community)
        rule = RuleFactory(community=community2)
        data = {"post": post.id, "user": user.id, "violated_rule": rule.id, 'reason': 'test_reason'}
        serializer = PostReportWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid() is False
        assert serializer.errors == {'non_field_errors': ['The selected rule does not belong to the specified community']}

    def test_report_own_post(self, serializer_context):
        user = serializer_context['request'].user
        community = CommunityFactory()
        post = PostFactory(user=user, title="test_post", type="text", content="test_content", community=community)
        data = {"post": post.id, "user": user.id, 'reason': 'test_reason'}
        serializer = PostReportWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid() is False
        assert serializer.errors == {'post': ['You cannot report your own post']}

    def test_report_on_post_without_community(self, serializer_context):
        user = serializer_context['request'].user
        post = PostFactory(type="text", content="test_content", title="test_post", community=None)
        data = {"post": post.id, "user": user.id, 'reason': 'test_reason'}
        serializer = PostReportWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid() is False
        assert serializer.errors == {'post': ['Post must belong to a community']}

    def test_duplicate_pending_report(self, serializer_context):
        user = serializer_context['request'].user
        community = CommunityFactory()
        post = PostFactory(type="text", content="test_content", title="test_post", community=community)
        PostReportFactory(user=user, post=post, status="pending")
        data = {"post": post.id, "user": user.id, 'reason': 'test_reason'}
        serializer = PostReportWriteSerializer(data=data, context=serializer_context)
        assert serializer.is_valid() is False
        assert serializer.errors == {'post': ['You already have a pending report for this post']}

@pytest.mark.django_db
class TestPostReportReadSerializer:
    def test_post_report_read_serializer_fields(self, serializer_context):
        user = serializer_context['request'].user
        community = CommunityFactory()
        post = PostFactory(title="test_post", type="text", content="test_content", community=community)
        violated_rule = RuleFactory(community=community, title="test_rule")
        report = PostReportFactory(user=user, post=post, status="pending", violated_rule=violated_rule)
        serializer = PostReportReadSerializer(report, context=serializer_context)
        serializer_data = serializer.data
        assert serializer_data['id'] == report.id
        assert serializer_data['post'] == PostReadSerializer(post, context=serializer_context).data
        assert serializer_data['user'] == CustomUserSerializer(user, context=serializer_context).data
        assert serializer_data['violated_rule'] == RuleSerializer(violated_rule).data
        assert serializer_data['reason'] == report.reason
        assert serializer_data['status'] == report.status
        assert serializer_data['created_at'] is not None

class TestLinkPreviewSerializer:
    @pytest.mark.parametrize(
        "invalid_data, error_field",
        [
            ({"title": "test_title", "description": "test_description", "image": "not_a_url", "url": "https://example.com"}, "image"),
            ({"title": "test_title", "description": "test_description", "image": "https://example.com/image.jpg", "url": "not_a_url"}, "url"),
        ],
    )
    def test_invalid_link_preview_serialization(self, invalid_data, error_field):
        serializer = LinkPreviewSerializer(data=invalid_data)
        assert serializer.is_valid() is False
        assert error_field in serializer.errors

    @pytest.mark.parametrize(
        "valid_data",
        [
            {
                "title": "test_title",
                "description": "test_description",
                "image": "https://example.com/image.jpg",
                "url": "https://example.com",
            },
            {
                "title": "",
                "description": "",
                "image": "",
                "url": "https://validurl.com",
            },
        ],
    )
    def test_valid_link_preview_serialization(self, valid_data):
        serializer = LinkPreviewSerializer(data=valid_data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == valid_data