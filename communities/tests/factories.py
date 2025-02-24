import factory
from faker import Faker
from django.contrib.auth import get_user_model
from posts.models import Post, PostInteraction, SavedPost, Attachment, PostReport
from communities.models import Community, Rule, Topic, Ban, Favorite, Member
from comments.models import Comment

User = get_user_model()
fake = Faker()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = fake.user_name()
    password = fake.password()
    email = factory.LazyAttribute(lambda _:  fake.unique.email())

class TopicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Topic
        
    name = factory.LazyAttribute(lambda _: fake.unique.word())
    description = fake.text()

class CommunityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Community
        skip_postgeneration_save = True

    user = factory.SubFactory(UserFactory)
    name = factory.LazyAttribute(lambda _: fake.unique.word())
    icon = factory.django.ImageField(filename='test_icon.png')
    banner = factory.django.ImageField(filename='test_banner.png')
    description = fake.text()
    
    @factory.post_generation
    def topics(self, create, extracted, **kwargs):
        if not create:  
            return  
        if extracted:
            for topic in extracted:
                self.topics.add(topic)
        else:
            self.topics.add(TopicFactory())
        self.save()

class RuleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Rule

    community = factory.SubFactory(CommunityFactory)
    title = fake.sentence()
    description = fake.text()

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

class FavoriteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Favorite

    user = factory.SubFactory(UserFactory)
    community = factory.SubFactory(CommunityFactory)