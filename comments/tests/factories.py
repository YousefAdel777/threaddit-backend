import factory
from faker import Faker
from django.contrib.auth import get_user_model
from accounts.models import Block
from posts.models import Post
from communities.models import Community, Rule, Member, Ban
from comments.models import Comment, CommentInteraction, CommentReport

User = get_user_model()
fake = Faker()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = fake.user_name()
    password = fake.password()
    email = factory.LazyAttribute(lambda _:  fake.unique.email())

class CommunityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Community

    name = factory.LazyAttribute(lambda _: fake.unique.name())
    user = factory.SubFactory(UserFactory)
    description = fake.sentence()

class MemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Member

    user = factory.SubFactory(UserFactory)
    community = factory.SubFactory(CommunityFactory)
    is_moderator = fake.boolean()

class BanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ban

    user = factory.SubFactory(UserFactory)
    community = factory.SubFactory(CommunityFactory)
    reason = fake.text()
    is_permanent = fake.boolean()
    expires_at = factory.Maybe(
        factory.LazyAttribute(lambda obj: fake.future_datetime() if not obj.is_permanent else None),
        yes_declaration=factory.LazyFunction(lambda: fake.future_datetime()),
        no_declaration=None
    )

class RuleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Rule
    
    community = factory.SubFactory(CommunityFactory)
    title = fake.sentence()

class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    user = factory.SubFactory(UserFactory)
    community = factory.SubFactory(CommunityFactory)
    title = fake.sentence()
    type = fake.random_element(['text', 'media', 'link', 'poll', 'crosspost'])
    content = factory.Maybe(
        factory.LazyAttribute(lambda obj: fake.text() if obj.type == 'text' else None),
        yes_declaration=factory.LazyFunction(lambda: fake.text()),
        no_declaration=''
    )
    link = factory.Maybe(
        factory.LazyAttribute(lambda obj: fake.url() if obj.type == 'link' else None),
        yes_declaration=factory.LazyFunction(lambda: fake.url()),
        no_declaration=''
    )
    original_post = factory.Maybe(
        factory.LazyAttribute(lambda obj: PostFactory(type="text") if obj.type == 'crosspost' else None),
        yes_declaration=factory.LazyFunction(lambda: PostFactory(type="text")),
        no_declaration=None
    )
    is_spoiler = fake.boolean()
    is_nsfw = fake.boolean()

class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    user = factory.SubFactory(UserFactory)
    post = factory.SubFactory(PostFactory)
    content = fake.sentence()
    status = fake.random_element(['accepted', 'removed'])
    parent = None

class CommentInteractionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CommentInteraction

    user = factory.SubFactory(UserFactory)
    comment = factory.SubFactory(CommentFactory)
    interaction_type = fake.random_element(['upvote', 'downvote'])

class CommentReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CommentReport

    user = factory.SubFactory(UserFactory)
    comment = factory.SubFactory(CommentFactory)
    reason = fake.sentence()
    status = fake.random_element(['pending', 'dismissed', 'reviewed'])
    violated_rule = factory.SubFactory(RuleFactory)

class BlockFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Block

    blocked_by = factory.SubFactory(UserFactory)
    blocked_user = factory.SubFactory(UserFactory)