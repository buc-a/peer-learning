from django.db import models
from django.contrib.auth.models import User


class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    bumped_at = models.DateTimeField(auto_now_add=True)
    last_message = models.ForeignKey(
        'Message', related_name='last_message_rooms',
        on_delete=models.SET_NULL, null=True, blank=True,
    )

    def __str__(self):
        return self.name


class RoomMember(models.Model):
    room = models.ForeignKey(Room, related_name='memberships', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='rooms', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('room', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.room.name}"


class Message(models.Model):
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    # message may have null user – we consider such messages "system"
    user = models.ForeignKey(
        User, related_name='messages', on_delete=models.CASCADE, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)