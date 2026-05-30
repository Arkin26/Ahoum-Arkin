from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    ROLE_SEEKER = "seeker"
    ROLE_FACILITATOR = "facilitator"
    ROLE_CHOICES = [
        (ROLE_SEEKER, "Seeker"),
        (ROLE_FACILITATOR, "Facilitator"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.user.email} ({self.role})"
