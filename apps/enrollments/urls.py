from django.urls import path

from .views import CancelEnrollmentView, EnrollmentViewSet, EventEnrollmentsView

enrollment_list = EnrollmentViewSet.as_view({"get": "list", "post": "create"})

urlpatterns = [
    path("", enrollment_list, name="enrollment-list"),
    path("<uuid:pk>/cancel/", CancelEnrollmentView.as_view(), name="enrollment-cancel"),
    path("event/<uuid:event_uuid>/", EventEnrollmentsView.as_view(), name="enrollment-event-list"),
]
