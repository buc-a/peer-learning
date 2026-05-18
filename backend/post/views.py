from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from django.shortcuts import get_object_or_404

from .models import Post
from .serializers import PostSerializer, PostWriteSerializer


class PostListCreateView(ListCreateAPIView):
    """
    GET  /api/posts/        — list all posts (public, paginated)
    POST /api/posts/        — create a new post (authenticated)
    Optional query params:
      ?skill=<str>          — filter by skill (case-insensitive)
      ?author=<user_id>     — filter by author
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostWriteSerializer
        return PostSerializer

    def get_queryset(self):
        qs = Post.objects.select_related('author').all()
        skill = self.request.query_params.get('skill', '').strip()
        author = self.request.query_params.get('author', '').strip()
        if skill:
            qs = qs.filter(skill__icontains=skill)
        if author:
            qs = qs.filter(author_id=author)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(author=request.user)
        # Return full representation with author info.
        output = PostSerializer(post, context={'request': request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class PostDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET    /api/posts/<id>/  — retrieve a post (public)
    PUT    /api/posts/<id>/  — update a post (owner only)
    PATCH  /api/posts/<id>/  — partial update (owner only)
    DELETE /api/posts/<id>/  — delete a post (owner only)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Post.objects.select_related('author').all()

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return PostWriteSerializer
        return PostSerializer

    def _check_owner(self, post):
        if post.author != self.request.user:
            return Response({'detail': 'you are not the author of this post'}, status=status.HTTP_403_FORBIDDEN)
        return None

    def update(self, request, *args, **kwargs):
        post = self.get_object()
        err = self._check_owner(post)
        if err:
            return err
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(post, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        output = PostSerializer(updated, context={'request': request})
        return Response(output.data)

    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        err = self._check_owner(post)
        if err:
            return err
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyPostsView(ListCreateAPIView):
    """
    GET /api/posts/my/  — list posts created by the current user
    """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user).select_related('author')
