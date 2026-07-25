from django.urls import path

from .report_views import (
    InstituteReportExportView,
    InstituteReportView,
    MyReportDrilldownView,
    MyReportExportView,
    MyReportView,
)

urlpatterns = [
    path("me/", MyReportView.as_view(), name="report-me"),
    path("me/drilldown/", MyReportDrilldownView.as_view(), name="report-me-drilldown"),
    path("me/export/", MyReportExportView.as_view(), name="report-me-export"),
    path("institute/", InstituteReportView.as_view(), name="report-institute"),
    path("institute/export/", InstituteReportExportView.as_view(), name="report-institute-export"),
]
