from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Post


class PostAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class PostSerializer(serializers.ModelSerializer):
    author = PostAuthorSerializer(read_only=True)
    is_owner = serializers.SerializerMethodField()

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author_id == request.user.pk
        return False

    class Meta:
        model = Post
        fields = ['id', 'author', 'title', 'description', 'skill', 'created_at', 'updated_at', 'is_owner']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'is_owner']


class PostWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['title', 'description', 'skill']
