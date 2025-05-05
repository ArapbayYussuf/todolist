from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, Subtask, Category, Tag, TaskTag

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class TaskTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskTag
        fields = ['id', 'task', 'tag']

class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = ['id', 'title', 'task']

class TaskSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'category', 'tags', 'priority', 'completed', 'user']
        read_only_fields = ['user']

    def get_tags(self, obj):
        task_tags = TaskTag.objects.filter(task=obj)
        return [task_tag.tag.id for task_tag in task_tags]

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        task = Task.objects.create(**validated_data)
        for tag_id in tags_data:
            TaskTag.objects.create(task=task, tag_id=tag_id)
        return task