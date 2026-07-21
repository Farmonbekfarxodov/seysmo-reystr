import django_filters
from django.db.models import Q

from .models import ScientificWork, SpecialistProfile


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


class ScientificWorkFilter(django_filters.FilterSet):
    category = django_filters.ChoiceFilter(choices=ScientificWork.Category.choices)
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = ScientificWork
        fields = ["category", "search"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(title__icontains=value)
