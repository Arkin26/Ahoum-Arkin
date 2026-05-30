import uuid

from django.contrib.auth.models import User
from django.db import models

from apps.events.models import Event


class Enrollment(models.Model):
    STATUS_ENROLLED = "enrolled"
    STATUS_CANCELED = "canceled"
    STATUS_CHOICES = [
        (STATUS_ENROLLED, "Enrolled"),
        (STATUS_CANCELED, "Canceled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="enrollments")
    seeker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ENROLLED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["seeker"]),
            models.Index(fields=["event"]),
        ]

    def __str__(self):
        return f"{self.seeker.email} -> {self.event.title} ({self.status})"
