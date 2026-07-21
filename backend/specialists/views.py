from django.db.models import Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as drf_filters
from rest_framework import generics, parsers, permissions

from .filters import ScientificWorkFilter, SpecialistFilter
from .models import Department, ScientificWork, SpecialistProfile
from .permissions import IsVerifiedSpecialist
from .serializers import (
    DepartmentSerializer,
    MySpecialistProfileSerializer,
    ScientificWorkSerializer,
    SpecialistCardSerializer,
    SpecialistDetailSerializer,
)

PUBLIC_QUERYSET = SpecialistProfile.objects.select_related("user", "department").filter(
    user__is_email_verified=True,
    user__is_active=True,
)


class DepartmentListView(generics.ListAPIView):
    """GET /api/departments/ — dropdown source. Unpaginated, public."""

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    throttle_scope = "public"


class SpecialistSearchView(generics.ListAPIView):
    """GET /api/specialists/?name=&department=&page= — public, paginated
    search. Every verified, active employee's profile is included -- there
    is no approval step and no visibility toggle."""

    queryset = PUBLIC_QUERYSET.annotate(works_count=Count("works")).order_by("-created_at")
    serializer_class = SpecialistCardSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SpecialistFilter
    throttle_scope = "public"


class SpecialistDetailView(generics.RetrieveAPIView):
    """GET /api/specialists/{id}/ — public profile, no email/username."""

    queryset = PUBLIC_QUERYSET
    serializer_class = SpecialistDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "user_id"
    lookup_url_kwarg = "id"
    throttle_scope = "public"


class MyProfileView(generics.RetrieveUpdateAPIView):
    """GET | PATCH /api/specialists/me/ — the logged-in employee's own
    profile: edit fields, replace/remove photo. No moderation or visibility
    fields here -- the profile is always public once the account is
    verified."""

    serializer_class = MySpecialistProfileSerializer
    permission_classes = [IsVerifiedSpecialist]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_object(self):
        return get_object_or_404(SpecialistProfile, user=self.request.user)


class SpecialistWorksPublicView(generics.ListAPIView):
    """GET /api/specialists/{id}/works/?category=&page=&ordering= — a
    specific (public, verified) employee's scientific works."""

    serializer_class = ScientificWorkSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, drf_filters.OrderingFilter]
    filterset_class = ScientificWorkFilter
    ordering_fields = ["year", "issued_date", "created_at"]
    ordering = ["-year", "-created_at"]
    throttle_scope = "public"

    def get_queryset(self):
        profile = get_object_or_404(PUBLIC_QUERYSET, user_id=self.kwargs["id"])
        return ScientificWork.objects.filter(specialist=profile)


class MyWorksListCreateView(generics.ListCreateAPIView):
    """GET | POST /api/specialists/me/works/?category=&page=&ordering= —
    list/create the logged-in employee's own scientific works. No count
    limit; every category requires a PDF file on create."""

    serializer_class = ScientificWorkSerializer
    permission_classes = [IsVerifiedSpecialist]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    filter_backends = [DjangoFilterBackend, drf_filters.OrderingFilter]
    filterset_class = ScientificWorkFilter
    ordering_fields = ["year", "issued_date", "created_at"]
    ordering = ["-year", "-created_at"]

    def get_profile(self):
        return get_object_or_404(SpecialistProfile, user=self.request.user)

    def get_queryset(self):
        return ScientificWork.objects.filter(specialist=self.get_profile())

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["specialist"] = self.get_profile()
        return context


class MyWorkDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET | PATCH | DELETE /api/specialists/me/works/{id}/ — a single own
    work: edit metadata and/or replace the PDF (removal is not allowed),
    or delete the whole record."""

    serializer_class = ScientificWorkSerializer
    permission_classes = [IsVerifiedSpecialist]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    lookup_url_kwarg = "id"

    def get_profile(self):
        return get_object_or_404(SpecialistProfile, user=self.request.user)

    def get_queryset(self):
        return ScientificWork.objects.filter(specialist=self.get_profile())

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["specialist"] = self.get_profile()
        return context

    def perform_destroy(self, instance):
        instance.file.delete(save=False)
        instance.delete()
