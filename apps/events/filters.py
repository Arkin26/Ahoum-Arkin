import django_filters
from django.db.models import Q

from .models import Event


class EventFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")
    language = django_filters.CharFilter(field_name="language", lookup_expr="iexact")
    location = django_filters.CharFilter(field_name="location", lookup_expr="icontains")
    starts_after = django_filters.DateTimeFilter(field_name="starts_at", lookup_expr="gte")
    starts_before = django_filters.DateTimeFilter(field_name="starts_at", lookup_expr="lte")

    class Meta:
        model = Event
        fields = ["q", "language", "location", "starts_after", "starts_before"]

    def filter_q(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(Q(title__icontains=value) | Q(description__icontains=value))
