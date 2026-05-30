import uuid

from django.contrib.auth.models import User
from django.db import models


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    language = models.CharField(max_length=50)
    location = models.CharField(max_length=255)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_events",
        limit_choices_to={"profile__role": "facilitator"},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at"]
        indexes = [
            models.Index(fields=["starts_at"]),
            models.Index(fields=["language"]),
            models.Index(fields=["location"]),
            models.Index(fields=["created_by"]),
        ]

    def __str__(self):
        return self.title
