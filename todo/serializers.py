from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, Subtask, Category, Tag, TaskTag

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'created_at']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'created_at']

class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = ['id', 'title', 'completed', 'task', 'created_at']
        read_only_fields = ['task', 'created_at']

class TaskTagSerializer(serializers.ModelSerializer):
    tag = TagSerializer()

    class Meta:
        model = TaskTag
        fields = ['id', 'tag']

class TaskSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False
    )
    subtasks = SubtaskSerializer(many=True, read_only=True)
    tags = TaskTagSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'completed', 'created_at',
                  'updated_at', 'user', 'category',
                  'category_id', 'priority', 'subtasks', 'tags']