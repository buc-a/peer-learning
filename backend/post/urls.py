from django.urls import path
from .views import PostListCreateView, PostDetailView, MyPostsView

urlpatterns = [
    path('posts/', PostListCreateView.as_view(), name='post-list'),
    path('posts/my/', MyPostsView.as_view(), name='post-my'),
    path('posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
]
