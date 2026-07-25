from django.urls import path

from .report_line_views import (
    InstituteReportLineView,
    InstituteReportLineZipView,
    MyReportLineView,
    MyReportLineZipView,
)
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
    path("me/line/", MyReportLineView.as_view(), name="report-me-line"),
    path("me/line/zip/", MyReportLineZipView.as_view(), name="report-me-line-zip"),
    path("me/export/", MyReportExportView.as_view(), name="report-me-export"),
    path("institute/", InstituteReportView.as_view(), name="report-institute"),
    path("institute/line/", InstituteReportLineView.as_view(), name="report-institute-line"),
    path("institute/line/zip/", InstituteReportLineZipView.as_view(), name="report-institute-line-zip"),
    path("institute/export/", InstituteReportExportView.as_view(), name="report-institute-export"),
]
