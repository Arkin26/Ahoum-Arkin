from django.utils import timezone
from rest_framework import serializers

from apps.events.models import Event

from .models import Enrollment


class EventBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ("id", "title", "language", "location", "starts_at", "ends_at")


class EnrollmentSerializer(serializers.ModelSerializer):
    event = EventBriefSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ("id", "event", "status", "created_at", "updated_at")
        read_only_fields = ("id", "status", "created_at", "updated_at", "event")


class EnrollmentCreateSerializer(serializers.Serializer):
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())

    def validate_event(self, event):
        if event.ends_at <= timezone.now():
            raise serializers.ValidationError("Cannot enroll in a past event.")
        return event

    def validate(self, attrs):
        request = self.context["request"]
        event = attrs["event"]
        seeker = request.user

        active = Enrollment.objects.filter(
            event=event, seeker=seeker, status=Enrollment.STATUS_ENROLLED
        ).exists()
        if active:
            raise serializers.ValidationError("You are already enrolled in this event.")

        if event.capacity is not None:
            enrolled = event.enrollments.filter(status=Enrollment.STATUS_ENROLLED).count()
            if enrolled >= event.capacity:
                raise serializers.ValidationError("This event is at full capacity.")

        return attrs

    def create(self, validated_data):
        return Enrollment.objects.create(
            event=validated_data["event"],
            seeker=self.context["request"].user,
            status=Enrollment.STATUS_ENROLLED,
        )


class FacilitatorEnrollmentSerializer(serializers.ModelSerializer):
    seeker_email = serializers.EmailField(source="seeker.email", read_only=True)

    class Meta:
        model = Enrollment
        fields = ("id", "seeker_email", "status", "created_at", "updated_at")
