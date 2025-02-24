from django.db import models
from django.contrib.auth import get_user_model
from accounts.services import UserService
User = get_user_model()

class Chat(models.Model):
    participants = models.ManyToManyField(User, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def last_message(self):        
        return self.messages.order_by('-created_at').first()
    
    def get_unread_messages_count(self, user):
        return self.messages.exclude(user=user).filter(is_read=False).count()
    
    def get_other_participant(self, user):
        return self.participants.exclude(id=user.id).exclude(blocked_by__blocked_by=user).exclude(blocks__blocked_user=user).first()

    def __str__(self):
        return f'Chat {self.id}'

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.content