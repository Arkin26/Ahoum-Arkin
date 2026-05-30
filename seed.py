#!/usr/bin/env python
"""Seed verified sample users and events for local testing."""
import os
import sys
from datetime import timedelta

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ahoum.settings.local")
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone

from apps.accounts.models import Profile
from apps.events.models import Event


def ensure_user(email, password, role):
    user, created = User.objects.get_or_create(
        email=email,
        defaults={"username": email, "is_active": True},
    )
    user.set_password(password)
    user.is_active = True
    user.save()
    Profile.objects.update_or_create(user=user, defaults={"role": role})
    action = "Created" if created else "Updated"
    print(f"{action} {role}: {email}")
    return user


def main():
    facilitator = ensure_user("facilitator@ahoum.com", "Test1234!", Profile.ROLE_FACILITATOR)
    ensure_user("seeker@ahoum.com", "Test1234!", Profile.ROLE_SEEKER)

    now = timezone.now()
    samples = [
        {
            "title": "Morning Meditation in Hindi",
            "description": "Guided meditation and breathwork session.",
            "language": "Hindi",
            "location": "Mumbai Studio",
            "starts_at": now + timedelta(days=7, hours=6),
            "ends_at": now + timedelta(days=7, hours=8),
            "capacity": 25,
        },
        {
            "title": "English Wellness Workshop",
            "description": "Introductory wellness and mindfulness workshop.",
            "language": "English",
            "location": "Delhi Community Hall",
            "starts_at": now + timedelta(days=14, hours=10),
            "ends_at": now + timedelta(days=14, hours=12),
            "capacity": 40,
        },
        {
            "title": "Mumbai Sunset Yoga",
            "description": "Outdoor yoga session by the beach.",
            "language": "English",
            "location": "Mumbai Beachfront",
            "starts_at": now + timedelta(days=21, hours=17),
            "ends_at": now + timedelta(days=21, hours=19),
            "capacity": 30,
        },
    ]

    for data in samples:
        event, created = Event.objects.get_or_create(
            title=data["title"],
            created_by=facilitator,
            defaults=data,
        )
        print(("Created" if created else "Exists") + f" event: {event.title}")

    print("\nSeed complete (users are email-verified / active).")
    print("Facilitator: facilitator@ahoum.com / Test1234!")
    print("Seeker: seeker@ahoum.com / Test1234!")


if __name__ == "__main__":
    main()
