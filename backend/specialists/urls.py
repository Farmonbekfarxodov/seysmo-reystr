from django.urls import path

from .views import (
    DepartmentListView,
    MyDocumentDeleteView,
    MyDocumentsView,
    MyProfileView,
    SpecialistDetailView,
    SpecialistSearchView,
)

urlpatterns = [
    path("departments/", DepartmentListView.as_view(), name="department-list"),
    path("specialists/", SpecialistSearchView.as_view(), name="specialist-search"),
    path("specialists/me/", MyProfileView.as_view(), name="specialist-me"),
    path("specialists/me/documents/", MyDocumentsView.as_view(), name="specialist-me-documents"),
    path(
        "specialists/me/documents/<int:id>/",
        MyDocumentDeleteView.as_view(),
        name="specialist-me-document-delete",
    ),
    path("specialists/<int:id>/", SpecialistDetailView.as_view(), name="specialist-detail"),
]
