from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, LogoutView, UserViewSet,
    TaskViewSet, SubtaskViewSet, CategoryViewSet, TagViewSet,
    profile_view
)
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('tasks/<int:task_id>/subtasks/', SubtaskViewSet.as_view({'get': 'list', 'post': 'create'}), name='task-subtasks'),
    path('subtasks/<int:pk>/', SubtaskViewSet.as_view({'put': 'update', 'delete': 'destroy'}), name='subtask-detail'),
    path('profile/', profile_view, name='profile'),
]