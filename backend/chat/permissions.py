"""
DRF-разрешения для приложения chat.
"""

from rest_framework.permissions import BasePermission

from .models import RoomMember


class IsRoomMember(BasePermission):
    """
    Разрешает доступ к ресурсам комнаты только её участникам.

    View должна передавать `room_id` через `kwargs` (URL-параметр).
    """

    message = 'You are not a member of this room.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        room_id = view.kwargs.get('room_id')
        if room_id is None:
            # Если room_id не задан в URL — разрешение не применимо; доступ запрещён.
            return False
        return RoomMember.objects.filter(
            room_id=room_id, user=request.user
        ).exists()
