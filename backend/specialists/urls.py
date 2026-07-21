from django.urls import path

from .views import (
    DepartmentListView,
    MyProfileView,
    MyWorkDetailView,
    MyWorksListCreateView,
    SpecialistDetailView,
    SpecialistSearchView,
    SpecialistWorksPublicView,
)

urlpatterns = [
    path("departments/", DepartmentListView.as_view(), name="department-list"),
    path("specialists/", SpecialistSearchView.as_view(), name="specialist-search"),
    path("specialists/me/", MyProfileView.as_view(), name="specialist-me"),
    path("specialists/me/works/", MyWorksListCreateView.as_view(), name="my-works-list-create"),
    path("specialists/me/works/<int:id>/", MyWorkDetailView.as_view(), name="my-work-detail"),
    path("specialists/<int:id>/", SpecialistDetailView.as_view(), name="specialist-detail"),
    path(
        "specialists/<int:id>/works/",
        SpecialistWorksPublicView.as_view(),
        name="specialist-works-public",
    ),
]
