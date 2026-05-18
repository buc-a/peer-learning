from django.contrib import admin
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'skill', 'author', 'created_at']
    list_filter = ['skill']
    search_fields = ['title', 'description', 'skill', 'author__username']
    ordering = ['-created_at']
