from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import ChatReadSerializer, MessageWriteSerializer, MessageReadSerializer, ChatWriteSerializer, MarkAsReadSerializer
from django_filters.rest_framework import DjangoFilterBackend
from api.pagination import CustomPagination
from .services import ChatService, MessageService
from .permissions import CanSendMessage, CanStartChat, IsSender

class ChatListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, CanStartChat]

    def get_queryset(self):
        return ChatService.get_chats(self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ChatReadSerializer
        return ChatWriteSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(ChatReadSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

class ChatDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatService.get_chats(self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ChatReadSerializer
        return ChatWriteSerializer

class MessageListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, CanSendMessage]
    filter_backends = [DjangoFilterBackend]
    pagination_class = CustomPagination
    filterset_fields = ['chat']

    def get_queryset(self):
        return MessageService.get_messages(self.request.user).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(MessageReadSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return MessageReadSerializer
        return MessageWriteSerializer

class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsSender]

    def get_queryset(self):
        return MessageService.get_messages(self.request.user).order_by('-created_at')
    
    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(MessageReadSerializer(serializer.instance).data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(MessageReadSerializer(serializer.instance).data, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return MessageReadSerializer
        return MessageWriteSerializer

class MarkAsReadView(APIView):
    permission_classes = [IsAuthenticated, CanSendMessage]
    def post(self, request):
        serializer = MarkAsReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        chat = serializer.validated_data.get('chat')
        MessageService.notify_read_messages(chat.id, request.user)
        MessageService.mark_as_read(chat.id, request.user)
        return Response({"message": "Messages marked as read"}, status=status.HTTP_200_OK)