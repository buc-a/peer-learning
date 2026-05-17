from rest_framework import serializers
from .models import Room, RoomMember, Message
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class LastMessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'content', 'user', 'created_at']


class RoomSerializer(serializers.ModelSerializer):
    last_message = LastMessageSerializer(read_only=True)
    # Include all members so the frontend can show the other participant's username.
    members = serializers.SerializerMethodField()

    def get_members(self, obj):
        memberships = obj.memberships.select_related('user').all()
        return [{'id': m.user.id, 'username': m.user.username} for m in memberships]

    class Meta:
        model = Room
        fields = ['id', 'name', 'bumped_at', 'last_message', 'members']


class MessageRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'bumped_at']


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    room = MessageRoomSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'content', 'user', 'room', 'created_at']


class RoomMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    room = RoomSerializer(read_only=True)

    class Meta:
        model = RoomMember
        fields = ['room', 'user']
