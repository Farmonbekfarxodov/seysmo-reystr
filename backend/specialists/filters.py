import django_filters
from django.db.models import Q

from .models import SpecialistProfile


class SpecialistFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method="filter_name")
    department = django_filters.CharFilter(field_name="department__slug", lookup_expr="exact")

    class Meta:
        model = SpecialistProfile
        fields = ["name", "department"]

    def filter_name(self, queryset, name, value):
        return queryset.filter(
            Q(user__last_name__icontains=value)
            | Q(user__first_name__icontains=value)
            | Q(user__patronymic__icontains=value)
        )
