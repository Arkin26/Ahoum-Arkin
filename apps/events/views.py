from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.permissions import IsFacilitator, IsOwnerOrReadOnly

from .filters import EventFilterSet
from .models import Event
from .serializers import EventCreateUpdateSerializer, EventSerializer, MyEventSerializer


def get_event_queryset():
    return Event.objects.select_related("created_by", "created_by__profile").annotate(
        enrolled_count=Count("enrollments", filter=Q(enrollments__status="enrolled"))
    )


@extend_schema_view(
    list=extend_schema(tags=["Events"], summary="Search and list events"),
    retrieve=extend_schema(tags=["Events"], summary="Get event detail"),
    create=extend_schema(tags=["Events"], summary="Create event (facilitator)"),
    update=extend_schema(tags=["Events"], summary="Update event (owner)"),
    partial_update=extend_schema(tags=["Events"], summary="Partially update event (owner)"),
    destroy=extend_schema(tags=["Events"], summary="Delete event (owner)"),
)
class EventViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = EventFilterSet
    ordering_fields = ["starts_at", "created_at"]
    ordering = ["starts_at"]
    lookup_field = "pk"
    lookup_value_regex = r"[0-9a-f-]+"
    queryset = Event.objects.none()

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        if self.action in ("create", "my_events"):
            return [IsFacilitator()]
        return [IsFacilitator(), IsOwnerOrReadOnly()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Event.objects.none()
        return get_event_queryset()

    def get_serializer_class(self):
        if self.action == "my_events":
            return MyEventSerializer
        if self.action in ("create", "update", "partial_update"):
            return EventCreateUpdateSerializer
        return EventSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Events"],
        summary="List my events with enrollment counts",
        responses={200: MyEventSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="my")
    def my_events(self, request):
        queryset = (
            get_event_queryset()
            .filter(created_by=request.user)
            .annotate(total_enrollments=Count("enrollments", filter=Q(enrollments__status="enrolled")))
        )
        page = self.paginate_queryset(queryset)
        data = []
        for event in page:
            item = MyEventSerializer(event).data
            item["total_enrollments"] = event.total_enrollments
            item["available_seats"] = (
                max(event.capacity - event.total_enrollments, 0) if event.capacity is not None else None
            )
            data.append(item)
        return self.get_paginated_response(data)
