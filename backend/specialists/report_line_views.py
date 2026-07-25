"""Drill-down: the exact records behind one report-line count, with
per-record and per-line (ZIP) PDF download. Reuses the exact same
counting/classification logic as the report summary (report_codes.py) so
a modal's row count always equals the number shown on the report."""

import re
import unicodedata

import zipstream
from django.http import Http404, StreamingHttpResponse
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ScientificWork, SpecialistProfile
from .report_codes import deduplicate_works_full, line_label, resolve_line_records
from .report_views import IsStaffUser, _parse_date, period_filter
from .serializers import ScientificWorkSerializer


def _safe_name_part(text, max_len=40):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\-]+", "_", text).strip("_")
    return text[:max_len] or "fayl"


def _unique_arcname(base_dir, stem, used_names):
    candidate = f"{base_dir}/{stem}.pdf"
    if candidate not in used_names:
        used_names[candidate] = 1
        return candidate
    used_names[candidate] += 1
    numbered = f"{base_dir}/{stem}_{used_names[candidate]}.pdf"
    used_names[numbered] = 1
    return numbered


def _file_chunk_iterator(work):
    with work.file.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            yield chunk


def _serialize_record(work, request, authors=None):
    data = ScientificWorkSerializer(work, context={"request": request}).data
    data["download_url"] = request.build_absolute_uri(work.file.url) if work.file else None
    if authors is not None:
        data["authors"] = authors
    return data


def _authors_for_group(members):
    return [
        {
            "specialist_id": m.specialist.user_id,
            "full_name": m.specialist.user.full_name,
            "is_main_author": m.authorship == ScientificWork.Authorship.MAIN_AUTHOR,
        }
        for m in members
    ]


def _pick_download_work(members):
    """The main author's copy if it has a file, else any co-author's copy
    that has one, else None."""
    main = next((m for m in members if m.authorship == ScientificWork.Authorship.MAIN_AUTHOR and m.file), None)
    if main:
        return main
    return next((m for m in members if m.file), None)


def _build_manifest(included, skipped):
    lines = [f"Jami kiritilgan fayllar: {len(included)}"]
    for name in included:
        lines.append(f"  - {name}")
    if skipped:
        lines.append("")
        lines.append(f"Sertifikat/fayl mavjud bo'lmagani uchun o'tkazib yuborilgan yozuvlar: {len(skipped)}")
        for title in skipped:
            lines.append(f"  - {title}")
    return "\n".join(lines).encode("utf-8")


class MyReportLineView(APIView):
    """GET /api/reports/me/line/?code=&year=&date_from=&date_to= -- the
    logged-in employee's own records behind one report line. No author
    column -- every record is already theirs."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = SpecialistProfile.objects.get(user=request.user)
        code = request.query_params.get("code")
        year = request.query_params.get("year")
        date_from = _parse_date(request.query_params.get("date_from"))
        date_to = _parse_date(request.query_params.get("date_to"))

        works = list(
            ScientificWork.objects.filter(specialist=profile).filter(
                period_filter(year=year, date_from=date_from, date_to=date_to)
            )
        )
        records = resolve_line_records(works, code)
        return Response({
            "code": code,
            "label": line_label(code),
            "count": len(records),
            "results": [_serialize_record(w, request) for w in records],
        })


class MyReportLineZipView(APIView):
    """GET /api/reports/me/line/zip/?code=&year= -- ZIP of the logged-in
    employee's own PDFs for one report line."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "report-zip"

    def get(self, request):
        profile = SpecialistProfile.objects.get(user=request.user)
        code = request.query_params.get("code")
        year = request.query_params.get("year")

        works = list(ScientificWork.objects.filter(specialist=profile).filter(period_filter(year=year)))
        records = resolve_line_records(works, code)
        if not records:
            raise Http404("Bu band bo'yicha yozuvlar topilmadi.")

        zs = zipstream.ZipStream(compress_type=zipstream.ZIP_DEFLATED)
        used_names = {}
        included, skipped = [], []
        for work in records:
            if not work.file:
                skipped.append(work.title)
                continue
            arcname = _unique_arcname(code, _safe_name_part(work.title), used_names)
            zs.add(_file_chunk_iterator(work), arcname=arcname)
            included.append(arcname)
        zs.add(_build_manifest(included, skipped), arcname=f"{code}/_haqida.txt")

        filename = f"{code}_{year or 'barcha'}_shaxsiy.zip"
        response = StreamingHttpResponse(zs, content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class InstituteReportLineView(APIView):
    """GET /api/reports/institute/line/?code=&year=&department=&employee=
    -- staff only. Deduplicated records behind one line across the
    selected scope, WITH each record's co-authors listed."""

    permission_classes = [IsStaffUser]

    def get(self, request):
        code = request.query_params.get("code")
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

        deduped, groups_by_id = deduplicate_works_full(list(qs))
        records = resolve_line_records(deduped, code)

        results = [
            _serialize_record(w, request, authors=_authors_for_group(groups_by_id[w.pk]))
            for w in records
        ]
        return Response({
            "code": code,
            "label": line_label(code),
            "count": len(records),
            "results": results,
        })


class InstituteReportLineZipView(APIView):
    """GET /api/reports/institute/line/zip/?code=&year=&department= --
    staff only. ZIP of one line's PDFs across the institute (or a
    department), one file per deduplicated work (main author's copy
    preferred), named with the author's surname."""

    permission_classes = [IsStaffUser]
    throttle_scope = "report-zip"

    def get(self, request):
        code = request.query_params.get("code")
        year = request.query_params.get("year")
        department_slug = request.query_params.get("department")

        qs = ScientificWork.objects.filter(
            specialist__user__is_email_verified=True, specialist__user__is_active=True
        ).select_related("specialist__user", "specialist__department")
        qs = qs.filter(period_filter(year=year))
        department_label = "institut"
        if department_slug:
            qs = qs.filter(specialist__department__slug=department_slug)
            department_label = department_slug

        deduped, groups_by_id = deduplicate_works_full(list(qs))
        records = resolve_line_records(deduped, code)
        if not records:
            raise Http404("Bu band bo'yicha yozuvlar topilmadi.")

        zs = zipstream.ZipStream(compress_type=zipstream.ZIP_DEFLATED)
        used_names = {}
        included, skipped = [], []
        for representative in records:
            members = groups_by_id[representative.pk]
            source = _pick_download_work(members)
            if source is None:
                skipped.append(representative.title)
                continue
            surname = source.specialist.user.last_name
            stem = f"{_safe_name_part(surname)}_{_safe_name_part(representative.title)}"
            arcname = _unique_arcname(code, stem, used_names)
            zs.add(_file_chunk_iterator(source), arcname=arcname)
            included.append(arcname)
        zs.add(_build_manifest(included, skipped), arcname=f"{code}/_haqida.txt")

        filename = f"{code}_{year or 'barcha'}_{department_label}.zip"
        response = StreamingHttpResponse(zs, content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
