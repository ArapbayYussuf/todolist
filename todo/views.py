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
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination

class TaskPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = 'page_size'
    max_page_size = 100

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

    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        elif request.method == 'PATCH':
            serializer = self.get_serializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                # Обновление имени пользователя
                if 'username' in request.data:
                    new_username = request.data['username']
                    if User.objects.exclude(id=user.id).filter(username=new_username).exists():
                        return Response({"error": "Имя пользователя уже занято"}, status=status.HTTP_400_BAD_REQUEST)
                    user.username = new_username
                    user.save()

                # Обновление пароля
                if 'new_password' in request.data and 'old_password' in request.data:
                    old_password = request.data['old_password']
                    new_password = request.data['new_password']
                    if not user.check_password(old_password):
                        return Response({"error": "Неверный старый пароль"}, status=status.HTTP_400_BAD_REQUEST)
                    user.set_password(new_password)
                    user.save()
                    # После смены пароля обновляем токены
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        "message": "Пароль успешно изменён",
                        "refresh": str(refresh),
                        "access": str(refresh.access_token)
                    }, status=status.HTTP_200_OK)

                serializer = self.get_serializer(user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'priority', 'completed', 'tags']
    ordering_fields = ['priority']
    ordering = ['priority']
    search_fields = ['title', 'description', 'tags__name']
    pagination_class = TaskPagination

    def get_queryset(self):
        queryset = Task.objects.filter(user=self.request.user).prefetch_related('tags')
        # Получаем параметр ordering из запроса
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            # Убедимся, что сортировка по priority работает корректно
            if ordering == 'priority':
                # От низкого к высокому: low → medium → high
                queryset = queryset.order_by('priority')
            elif ordering == '-priority':
                # От высокого к низкому: high → medium → low
                queryset = queryset.order_by('-priority')
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

def profile_view(request):
    return render(request, 'profile.html')