from datetime import date

from django.db.models import Q
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Department, ScientificWork, SpecialistProfile
from .permissions import IsVerifiedSpecialist
from .report_codes import build_report, deduplicate_works
from .serializers import ScientificWorkSerializer


def period_filter(year=None, date_from=None, date_to=None):
    """Q object selecting works whose report-relevant date (year for
    articles/theses/other-publications, issued_date for patents,
    event_date for conference participation) falls in the requested
    period. Year mode is the primary, well-tested path; date-range mode
    is a best-effort convenience on top of the same per-category sources."""
    patent_q = Q(category=ScientificWork.Category.PATENT)
    conf_q = Q(category=ScientificWork.Category.CONFERENCE_PARTICIPATION)
    other_q = ~(patent_q | conf_q)

    if year:
        return (
            (patent_q & Q(issued_date__year=year))
            | (conf_q & Q(event_date__year=year))
            | (other_q & Q(year=year))
        )

    if date_from or date_to:
        def range_q(field):
            q = Q()
            if date_from:
                q &= Q(**{f"{field}__gte": date_from})
            if date_to:
                q &= Q(**{f"{field}__lte": date_to})
            return q

        year_from = date_from.year if date_from else None
        year_to = date_to.year if date_to else None
        year_q = Q()
        if year_from:
            year_q &= Q(year__gte=year_from)
        if year_to:
            year_q &= Q(year__lte=year_to)

        return (
            (patent_q & range_q("issued_date"))
            | (conf_q & range_q("event_date"))
            | (other_q & year_q)
        )

    return Q()


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def serialize_report(report_dict, request):
    """Turns build_report()'s dict (with model instances in `unclassified`)
    into a JSON-safe structure, including drill-down record summaries."""
    def summarize(work):
        return ScientificWorkSerializer(work, context={"request": request}).data

    return {
        "sections": report_dict["sections"],
        "quartile_matrix": report_dict["quartile_matrix"],
        "unclassified": [summarize(w) for w in report_dict["unclassified"]],
        "without_certificate": report_dict["without_certificate"],
        "total_records": report_dict["total_records"],
    }


class MyReportView(APIView):
    """GET /api/reports/me/?year=&date_from=&date_to= -- the logged-in
    employee's own report. Not deduplicated (an employee sees everything
    they registered, regardless of co-authors)."""

    permission_classes = [IsVerifiedSpecialist]

    def get(self, request):
        profile = SpecialistProfile.objects.get(user=request.user)
        year = request.query_params.get("year")
        date_from = _parse_date(request.query_params.get("date_from"))
        date_to = _parse_date(request.query_params.get("date_to"))

        qs = ScientificWork.objects.filter(specialist=profile).filter(
            period_filter(year=year, date_from=date_from, date_to=date_to)
        )
        report = build_report(qs)
        return Response(serialize_report(report, request))


class MyReportDrilldownView(APIView):
    """GET /api/reports/me/drilldown/?code=2.1&year= -- the records behind
    a single report line, for the employee's own report."""

    permission_classes = [IsVerifiedSpecialist]

    def get(self, request):
        profile = SpecialistProfile.objects.get(user=request.user)
        code = request.query_params.get("code")
        year = request.query_params.get("year")

        qs = ScientificWork.objects.filter(specialist=profile).filter(
            period_filter(year=year)
        )
        if code == "3.4":
            qs = qs.filter(report_code__in=["3.4.1", "3.4.2"])
        elif code == "5.2":
            qs = qs.filter(report_code="5.1", published_abroad=True)
        elif code == "5.4":
            qs = qs.filter(report_code="5.3", published_abroad=True)
        else:
            qs = qs.filter(report_code=code)

        data = ScientificWorkSerializer(qs, many=True, context={"request": request}).data
        return Response({"results": data})


class IsStaffUser(permissions.BasePermission):
    message = "Faqat administrator uchun."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class InstituteReportView(APIView):
    """GET /api/reports/institute/?year=&department=&employee= -- staff
    only. Institute-wide totals are deduplicated (see report_codes.py);
    per-employee rows show each employee's own non-deduplicated counts."""

    permission_classes = [IsStaffUser]

    def get(self, request):
        year = request.query_params.get("year")
        department_slug = request.query_params.get("department")
        employee_id = request.query_params.get("employee")

        qs = ScientificWork.objects.filter(
            specialist__user__is_email_verified=True, specialist__user__is_active=True
        ).select_related("specialist__user", "specialist__department")
        qs = qs.filter(period_filter(year=year))
        if department_slug:
            qs = qs.filter(specialist__department__slug=department_slug)
        if employee_id:
            qs = qs.filter(specialist__user_id=employee_id)

        all_works = list(qs)
        deduped, merged_groups = deduplicate_works(all_works)
        institute_report = build_report(deduped)

        # Per-laboratory breakdown: attribute each deduplicated group to
        # its representative record's department, so department numbers
        # sum exactly to the institute total.
        by_department = {}
        for work in deduped:
            dept_name = work.specialist.department.name
            by_department.setdefault(dept_name, []).append(work)
        department_breakdown = [
            {"department": name, "report": _summary_counts(build_report(works))}
            for name, works in sorted(by_department.items())
        ]

        # Per-employee breakdown: each employee's OWN full counts (not
        # deduplicated -- this is "who did what", not institute totals).
        by_employee = {}
        for work in all_works:
            key = work.specialist_id
            by_employee.setdefault(key, {"specialist": work.specialist, "works": []})
            by_employee[key]["works"].append(work)
        employee_breakdown = [
            {
                "employee_id": entry["specialist"].user_id,
                "full_name": entry["specialist"].user.full_name,
                "department": entry["specialist"].department.name,
                "report": _summary_counts(build_report(entry["works"])),
            }
            for entry in by_employee.values()
        ]
        employee_breakdown.sort(key=lambda e: e["full_name"])

        response = serialize_report(institute_report, request)
        response["deduplicated_count"] = len(merged_groups)
        response["duplicate_groups"] = [
            {
                "report_code": members[0].report_code,
                "title": members[0].title,
                "authors": [m.specialist.user.full_name for m in members],
            }
            for members in merged_groups
        ]
        response["department_breakdown"] = department_breakdown
        response["employee_breakdown"] = employee_breakdown
        return Response(response)


def _summary_counts(report_dict):
    """Flat {code: count} map (plus section totals) for compact breakdown
    tables -- the full nested structure isn't needed per-row."""
    flat = {}
    for section in report_dict["sections"]:
        for line in section["lines"]:
            flat[line["code"]] = line["count"]
        flat[f"total_{section['id']}"] = section["total"]
    return flat


def _period_label(year, date_from, date_to):
    if year:
        return str(year)
    if date_from or date_to:
        return f"{date_from or '...'} — {date_to or '...'}"
    return "barcha davr"


class MyReportExportView(APIView):
    """GET /api/reports/me/export/?year= -- Excel download of the
    logged-in employee's own report."""

    permission_classes = [IsVerifiedSpecialist]

    def get(self, request):
        from django.http import HttpResponse

        from .excel_export import build_personal_report_workbook, workbook_to_bytes

        profile = SpecialistProfile.objects.select_related("user", "department").get(user=request.user)
        year = request.query_params.get("year")
        date_from = _parse_date(request.query_params.get("date_from"))
        date_to = _parse_date(request.query_params.get("date_to"))

        qs = ScientificWork.objects.filter(specialist=profile).filter(
            period_filter(year=year, date_from=date_from, date_to=date_to)
        )
        report = build_report(qs)

        employee_info = {
            "full_name": profile.user.full_name,
            "academic_degree": profile.get_academic_degree_display(),
            "position": profile.get_position_display(),
            "department": profile.department.name,
        }
        wb = build_personal_report_workbook(report, _period_label(year, date_from, date_to), employee_info)

        filename = f"hisobot_{year or 'barcha'}_{profile.user.last_name}.xlsx"
        response = HttpResponse(
            workbook_to_bytes(wb),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class InstituteReportExportView(APIView):
    """GET /api/reports/institute/export/?year=&department= -- staff only,
    Excel download of the institute-wide (deduplicated) report."""

    permission_classes = [IsStaffUser]

    def get(self, request):
        from django.http import HttpResponse

        from .excel_export import build_institute_report_workbook, workbook_to_bytes

        year = request.query_params.get("year")
        department_slug = request.query_params.get("department")

        qs = ScientificWork.objects.filter(
            specialist__user__is_email_verified=True, specialist__user__is_active=True
        ).select_related("specialist__user", "specialist__department")
        qs = qs.filter(period_filter(year=year))

        department_label = None
        if department_slug:
            qs = qs.filter(specialist__department__slug=department_slug)
            dept = Department.objects.filter(slug=department_slug).first()
            department_label = dept.name if dept else None

        all_works = list(qs)
        deduped, merged_groups = deduplicate_works(all_works)
        report = build_report(deduped)
        report["deduplicated_count"] = len(merged_groups)

        by_department = {}
        for work in deduped:
            by_department.setdefault(work.specialist.department.name, []).append(work)
        report["department_breakdown"] = [
            {"department": name, "report": _summary_counts(build_report(works))}
            for name, works in sorted(by_department.items())
        ]

        by_employee = {}
        for work in all_works:
            by_employee.setdefault(work.specialist_id, {"specialist": work.specialist, "works": []})
            by_employee[work.specialist_id]["works"].append(work)
        report["employee_breakdown"] = sorted(
            (
                {
                    "full_name": entry["specialist"].user.full_name,
                    "department": entry["specialist"].department.name,
                    "report": _summary_counts(build_report(entry["works"])),
                }
                for entry in by_employee.values()
            ),
            key=lambda e: e["full_name"],
        )

        wb = build_institute_report_workbook(report, _period_label(year, None, None), department_label)

        filename = f"hisobot_{year or 'barcha'}_{department_label or 'institut'}.xlsx"
        response = HttpResponse(
            workbook_to_bytes(wb),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
