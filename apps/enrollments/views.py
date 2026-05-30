from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

import django_filters

from ahoum.exceptions import api_error
from apps.accounts.permissions import IsFacilitator, IsSeeker
from apps.events.models import Event

from .models import Enrollment
from .serializers import (
    EnrollmentCreateSerializer,
    EnrollmentSerializer,
    FacilitatorEnrollmentSerializer,
)
from .tasks import schedule_enrollment_emails


class EnrollmentFilterSet(django_filters.FilterSet):
    type = django_filters.CharFilter(method="filter_type")

    class Meta:
        model = Enrollment
        fields = ["type"]

    def filter_type(self, queryset, name, value):
        now = timezone.now()
        if value == "upcoming":
            return queryset.filter(
                status=Enrollment.STATUS_ENROLLED,
                event__starts_at__gte=now,
            )
        if value == "past":
            return queryset.filter(event__ends_at__lt=now)
        return queryset


class EnrollmentViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    lookup_field = "pk"
    lookup_value_regex = r"[0-9a-f-]+"
    queryset = Enrollment.objects.none()
    serializer_class = EnrollmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = EnrollmentFilterSet

    def get_permissions(self):
        if self.action in ("create", "list"):
            return [IsSeeker()]
        return []

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Enrollment.objects.none()
        return (
            Enrollment.objects.filter(seeker=self.request.user)
            .select_related("event", "event__created_by")
            .order_by("event__starts_at")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return EnrollmentCreateSerializer
        return EnrollmentSerializer

    @extend_schema(tags=["Enrollments"], summary="Enroll in an event", request=EnrollmentCreateSerializer)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enrollment = serializer.save()
        enrollment = Enrollment.objects.select_related("event", "seeker").get(pk=enrollment.pk)
        schedule_enrollment_emails(enrollment)
        return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Enrollments"],
        summary="List my enrollments (?type=upcoming or ?type=past)",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class CancelEnrollmentView(APIView):
    permission_classes = [IsSeeker]
    serializer_class = EnrollmentSerializer

    @extend_schema(tags=["Enrollments"], summary="Cancel enrollment")
    def patch(self, request, pk):
        enrollment = get_object_or_404(
            Enrollment.objects.select_related("event"),
            pk=pk,
            seeker=request.user,
        )
        if enrollment.status == Enrollment.STATUS_CANCELED:
            return api_error("Enrollment is already canceled.", "already_canceled", status.HTTP_400_BAD_REQUEST)

        enrollment.status = Enrollment.STATUS_CANCELED
        enrollment.save(update_fields=["status", "updated_at"])
        return Response(EnrollmentSerializer(enrollment).data)


class EventEnrollmentsView(APIView):
    permission_classes = [IsFacilitator]
    serializer_class = FacilitatorEnrollmentSerializer

    @extend_schema(tags=["Enrollments"], summary="List enrollments for facilitator's event")
    def get(self, request, event_uuid):
        event = get_object_or_404(Event, pk=event_uuid, created_by=request.user)
        enrollments = (
            Enrollment.objects.filter(event=event, status=Enrollment.STATUS_ENROLLED)
            .select_related("seeker")
            .order_by("-created_at")
        )
        from rest_framework.pagination import PageNumberPagination

        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(enrollments, request)
        serializer = FacilitatorEnrollmentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
