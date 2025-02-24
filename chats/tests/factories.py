import factory
from faker import Faker
from django.contrib.auth import get_user_model
from chats.models import Message, Chat
from accounts.models import Block

User = get_user_model()
fake = Faker()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = fake.user_name()
    password = fake.password()
    email = factory.LazyAttribute(lambda _:  fake.unique.email())

class ChatFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Chat
        skip_postgeneration_save = True

    @factory.post_generation
    def participants(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.participants.add(user)
        else:
            user1 = UserFactory()
            user2 = UserFactory()
            self.participants.add(user1, user2)


class MessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Message
    
    chat = factory.SubFactory(ChatFactory)
    user = factory.SubFactory(UserFactory)
    content = fake.sentence()

class BlockFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Block

    blocked_by = factory.SubFactory(UserFactory)
    blocked_user = factory.SubFactory(UserFactory)