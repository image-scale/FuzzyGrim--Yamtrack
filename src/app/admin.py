"""Admin configuration for app models."""

from django.contrib import admin

from app.models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """Admin configuration for Item model."""

    list_display = ['title', 'media_type', 'source', 'media_id']
    list_filter = ['media_type', 'source']
    search_fields = ['title', 'media_id']
