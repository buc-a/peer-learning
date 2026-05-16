from django.urls import path

from .views import RoomListViewSet, \
    MessageListCreateAPIView, JoinRoomView


urlpatterns = [
    path('rooms/', RoomListViewSet.as_view({'get': 'list'}), name='room-list'),
    path('rooms/<int:room_id>/messages/', MessageListCreateAPIView.as_view(), name='room-messages'),
    path('rooms/<int:room_id>/join/', JoinRoomView.as_view(), name='join-room'),
]