import json
import logging
import requests
from requests.adapters import HTTPAdapter, Retry

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from .models import Message, Room, RoomMember
from .serializers import (
    MessageSerializer, RoomSerializer, RoomMemberSerializer, UserSerializer
)


class CentrifugoMixin:
    """Helper mixin to broadcast real-time events via Centrifugo HTTP API."""

    def get_room_member_channels(self, room_id):
        """Return personal channels for all current members of a room."""
        members = RoomMember.objects.filter(room_id=room_id).values_list('user', flat=True)
        return [f'personal:{user_id}' for user_id in members]

    # разослать сообщение всем участникам чата
    def broadcast_room(self, room, broadcast_payload):
        """Broadcast a payload to all room member channels via Centrifugo HTTP API."""
        def broadcast():
            session = requests.Session()
            retries = Retry(total=1, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
            session.mount('http://', HTTPAdapter(max_retries=retries))
            try:
                session.post(
                    settings.CENTRIFUGO_HTTP_API_ENDPOINT + '/api/broadcast',
                    data=json.dumps(broadcast_payload),
                    headers={
                        'Content-type': 'application/json',
                        'X-API-Key': settings.CENTRIFUGO_HTTP_API_KEY,
                        'X-Centrifugo-Error-Mode': 'transport'
                    }
                )
            except requests.exceptions.RequestException as e:
                logging.error(e)

        # Use on_commit so we don't notify Centrifugo before the DB transaction commits.
        transaction.on_commit(broadcast)


class RoomListViewSet(ListModelMixin, GenericViewSet):
    """List all rooms the current user is a member of."""
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Room.objects.filter(
            memberships__user_id=self.request.user.pk
        ).select_related('last_message', 'last_message__user').prefetch_related('memberships__user').order_by('-bumped_at')


class RoomDetailViewSet(RetrieveModelMixin, GenericViewSet):
    """Retrieve a single room the current user is a member of."""
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Room.objects.filter(
            memberships__user_id=self.request.user.pk
        ).prefetch_related('memberships__user')


class UserSearchViewSet(ListModelMixin, GenericViewSet):
    """
    Search for users to start a 1-on-1 chat with.
    Returns all users except the current user.
    Optional query param: ?q=<username fragment>
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        q = self.request.query_params.get('q', '').strip()
        qs = User.objects.exclude(pk=self.request.user.pk).order_by('username')
        if q:
            qs = qs.filter(username__icontains=q)
        return qs


class MessageListCreateAPIView(ListCreateAPIView, CentrifugoMixin):
    """List messages in a room or post a new message."""
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        room_id = self.kwargs['room_id']
        get_object_or_404(RoomMember, user=self.request.user, room_id=room_id)
        return Message.objects.filter(
            room_id=room_id
        ).select_related('user', 'room').order_by('-created_at')

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        room_id = self.kwargs['room_id']
        room = Room.objects.select_for_update().get(id=room_id)
        # Verify the requesting user is a member.
        get_object_or_404(RoomMember, user=request.user, room=room)

        channels = self.get_room_member_channels(room_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(room=room, user=request.user)
        room.last_message = obj
        room.bumped_at = timezone.now()
        room.save()

        broadcast_payload = {
            'channels': channels,
            'data': {
                'type': 'message_added',
                'body': serializer.data
            },
            'idempotency_key': f'message_{serializer.data["id"]}'
        }
        self.broadcast_room(room, broadcast_payload)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class StartChatView(APIView, CentrifugoMixin):
    """
    Start (or retrieve) a 1-on-1 chat room between the current user and another user.
    A room is considered a direct chat if it has exactly 2 members and both users are members.
    POST body: { "user_id": <int> }
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        other_user_id = request.data.get('user_id')
        if not other_user_id:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        other_user = get_object_or_404(User, pk=other_user_id)
        if other_user == request.user:
            return Response(
                {'detail': 'cannot start chat with yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Look for an existing direct room shared by both users (exactly 2 members).
        existing_room = Room.objects.filter(
            memberships__user=request.user
        ).filter(
            memberships__user=other_user
        ).annotate(
            member_count_ann=Count('memberships')
        ).filter(member_count_ann=2).first()

        if existing_room:
            serializer = RoomSerializer(existing_room)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Create a new room named after both participants (sorted alphabetically).
        names = sorted([request.user.username, other_user.username])
        room_name = f'{names[0]}&{names[1]}'
        # Ensure uniqueness by appending a suffix if needed.
        base_name = room_name
        suffix = 1
        while Room.objects.filter(name=room_name).exists():
            room_name = f'{base_name}_{suffix}'
            suffix += 1

        room = Room.objects.create(name=room_name)
        RoomMember.objects.create(room=room, user=request.user)
        RoomMember.objects.create(room=room, user=other_user)

        channels = self.get_room_member_channels(room.pk)
        serializer = RoomSerializer(room)

        broadcast_payload = {
            'channels': channels,
            'data': {
                'type': 'room_created',
                'body': serializer.data
            },
            'idempotency_key': f'room_created_{room.pk}'
        }
        self.broadcast_room(room, broadcast_payload)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
