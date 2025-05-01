from django.shortcuts import render
from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Task, Subtask, Category, Tag, TaskTag
from .serializers import (
    UserSerializer, RegisterSerializer, TaskSerializer,
    SubtaskSerializer, CategorySerializer, TagSerializer, TaskTagSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]

class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"message": "Вы успешно вышли из аккаунта"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        task = serializer.save(user=self.request.user)
        tag_ids = self.request.data.get('tags', [])
        for tag_id in tag_ids:
            try:
                tag = Tag.objects.get(id=tag_id)
                TaskTag.objects.create(task=task, tag=tag)
            except Tag.DoesNotExist:
                continue

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['post'], url_path='tags')
    def add_tag(self, request, pk=None):
        task = self.get_object()
        tag_id = request.data.get('tag_id')
        try:
            tag = Tag.objects.get(id=tag_id)
            TaskTag.objects.create(task=task, tag=tag)
            return Response({'status': 'Тег добавлен'}, status=status.HTTP_201_CREATED)
        except Tag.DoesNotExist:
            return Response({'error': 'Тег не найден'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['delete'], url_path='tags/(?P<tag_id>[^/.]+)')
    def remove_tag(self, request, pk=None, tag_id=None):
        task = self.get_object()
        try:
            task_tag = TaskTag.objects.get(task=task, tag__id=tag_id)
            task_tag.delete()
            return Response({'status': 'Тег удалён'}, status=status.HTTP_204_NO_CONTENT)
        except TaskTag.DoesNotExist:
            return Response({'error': 'Тег не найден для этой задачи'}, status=status.HTTP_404_NOT_FOUND)

class SubtaskViewSet(viewsets.ModelViewSet):
    serializer_class = SubtaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        task_id = self.kwargs.get('task_id')
        if task_id:
            return Subtask.objects.filter(task__id=task_id, task__user=self.request.user)
        return Subtask.objects.filter(task__user=self.request.user)

    def perform_create(self, serializer):
        task_id = self.kwargs.get('task_id')
        task = Task.objects.get(id=task_id, user=self.request.user)
        serializer.save(task=task)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]