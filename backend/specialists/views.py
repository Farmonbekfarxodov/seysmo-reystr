from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, parsers, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import SpecialistFilter
from .models import Department, SpecialistDocument, SpecialistProfile
from .permissions import IsVerifiedSpecialist
from .serializers import (
    DepartmentSerializer,
    DocumentSerializer,
    DocumentUploadSerializer,
    MySpecialistProfileSerializer,
    SpecialistCardSerializer,
    SpecialistDetailSerializer,
)

PUBLIC_QUERYSET = SpecialistProfile.objects.select_related("user", "department").prefetch_related(
    "documents"
).filter(
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

    queryset = PUBLIC_QUERYSET
    serializer_class = SpecialistCardSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SpecialistFilter
    throttle_scope = "public"


class SpecialistDetailView(generics.RetrieveAPIView):
    """GET /api/specialists/{id}/ — public profile, no email/username/docs."""

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


class MyDocumentsView(APIView):
    """POST /api/specialists/me/documents/ — upload a new article/document.
    No count limit -- researchers may have many publications over time."""

    permission_classes = [IsVerifiedSpecialist]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        profile = get_object_or_404(SpecialistProfile, user=request.user)

        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded = serializer.validated_data["file"]

        document = SpecialistDocument.objects.create(
            specialist=profile, file=uploaded, original_filename=uploaded.name, size=uploaded.size
        )
        return Response(
            DocumentSerializer(document, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class MyDocumentDeleteView(APIView):
    """DELETE /api/specialists/me/documents/{id}/ — remove one of the
    logged-in employee's own files."""

    permission_classes = [IsVerifiedSpecialist]

    def delete(self, request, id):
        profile = get_object_or_404(SpecialistProfile, user=request.user)
        document = get_object_or_404(SpecialistDocument, id=id, specialist=profile)
        document.file.delete(save=False)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
