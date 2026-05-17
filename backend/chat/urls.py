from django.urls import path

from .views import (
    RoomListViewSet,
    RoomDetailViewSet,
    UserSearchViewSet,
    MessageListCreateAPIView,
    StartChatView,
)

urlpatterns = [
    path('rooms/', RoomListViewSet.as_view({'get': 'list'}), name='room-list'),
    path('rooms/<int:pk>/', RoomDetailViewSet.as_view({'get': 'retrieve'}), name='room-detail'),
    path('rooms/<int:room_id>/messages/', MessageListCreateAPIView.as_view(), name='room-messages'),
    path('users/', UserSearchViewSet.as_view({'get': 'list'}), name='user-search'),
    path('chats/start/', StartChatView.as_view(), name='start-chat'),
]
