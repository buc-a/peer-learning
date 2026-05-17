from django.contrib import admin
from .models import Room, RoomMember, Message


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'bumped_at', 'last_message']
    search_fields = ['name']


@admin.register(RoomMember)
class RoomMemberAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'user']
    list_filter = ['room']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'user', 'content', 'created_at']
    list_filter = ['room']
    search_fields = ['content']
