from rest_framework import serializers

from .models import Event


class FacilitatorBriefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()


class EventSerializer(serializers.ModelSerializer):
    created_by = FacilitatorBriefSerializer(read_only=True)
    enrolled_count = serializers.SerializerMethodField()
    available_seats = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            "id",
            "title",
            "description",
            "language",
            "location",
            "starts_at",
            "ends_at",
            "capacity",
            "created_by",
            "enrolled_count",
            "available_seats",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")

    def get_enrolled_count(self, obj):
        count = getattr(obj, "enrolled_count", None)
        if count is not None:
            return count
        return obj.enrollments.filter(status="enrolled").count()

    def get_available_seats(self, obj):
        if obj.capacity is None:
            return None
        return max(obj.capacity - self.get_enrolled_count(obj), 0)


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = (
            "title",
            "description",
            "language",
            "location",
            "starts_at",
            "ends_at",
            "capacity",
        )

    def validate(self, attrs):
        starts = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if starts and ends and ends <= starts:
            raise serializers.ValidationError("ends_at must be after starts_at.")
        return attrs


class MyEventSerializer(EventSerializer):
    total_enrollments = serializers.IntegerField(read_only=True)
    available_seats = serializers.IntegerField(read_only=True, allow_null=True)
