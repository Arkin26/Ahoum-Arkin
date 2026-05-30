from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "language", "location", "starts_at", "created_by")
    list_filter = ("language",)
    search_fields = ("title", "description", "location")
