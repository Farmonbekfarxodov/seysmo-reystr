import io
import zipfile

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from specialists.models import Department, ScientificWork, SpecialistProfile
from specialists.report_codes import build_report, deduplicate_works_full, resolve_line_records


def make_profile(email, username, department, last_name="L", first_name="F"):
    user = User.objects.create_user(
        username=username, email=email, password="StrongPass123", first_name=first_name, last_name=last_name,
    )
    user.is_active = True
    user.is_email_verified = True
    user.save()
    return SpecialistProfile.objects.create(user=user, department=department)


def pdf(name="x.pdf"):
    return SimpleUploadedFile(name, b"%PDF-1.4 fake pdf content", content_type="application/pdf")


def make_work(profile, with_file=True, **kwargs):
    defaults = dict(specialist=profile, title="T", authorship="main_author")
    defaults.update(kwargs)
    work = ScientificWork(**defaults)
    if with_file:
        work.file = pdf(f"{defaults['title']}.pdf")
        work.original_filename = f"{defaults['title']}.pdf"
        work.size = 20
    work.save()
    return work


class LineResolutionMatchesSummaryTests(TestCase):
    """The modal's row count must exactly equal the report summary count."""

    def setUp(self):
        self.dept = Department.objects.create(name="Geofizika")
        self.profile = make_profile("match@example.com", "match_user", self.dept)

    def _assert_matches(self, code, section_id):
        works = list(ScientificWork.objects.filter(specialist=self.profile))
        report = build_report(works)
        section = next(s for s in report["sections"] if s["id"] == section_id)
        if code == section_id:
            expected = section["total"]
        else:
            expected = next(l["count"] for l in section["lines"] if l["code"] == code)
        actual = len(resolve_line_records(works, code))
        self.assertEqual(actual, expected, f"code={code}")

    def test_plain_leaf_code(self):
        make_work(self.profile, category="foreign_article", journal_scope="local", year=2024)
        make_work(self.profile, category="foreign_article", journal_scope="other_foreign", year=2024)
        self._assert_matches("2.4", "II")
        self._assert_matches("2.2", "II")
        self._assert_matches("II", "II")

    def test_section_total_with_local_conference_sublevels(self):
        make_work(self.profile, category="thesis", conference_scope="local", local_conf_level="international", year=2024)
        make_work(self.profile, category="thesis", conference_scope="local", local_conf_level="international", year=2024)
        make_work(self.profile, category="thesis", conference_scope="local", local_conf_level="republic", year=2024)
        make_work(self.profile, category="thesis", conference_scope="scopus_wos", year=2024)
        self._assert_matches("3.4", "III")
        self._assert_matches("3.4.1", "III")
        self._assert_matches("3.1", "III")
        self._assert_matches("III", "III")

    def test_subset_abroad_codes(self):
        make_work(self.profile, category="other_publication", publication_type="monograph", published_abroad=True, publisher="P", year=2024)
        make_work(self.profile, category="other_publication", publication_type="monograph", published_abroad=False, publisher="P", year=2024)
        self._assert_matches("5.1", "V")
        self._assert_matches("5.2", "V")
        self._assert_matches("V", "V")  # total must NOT include the 5.2 subset

    def test_quartile_qualified_code(self):
        make_work(
            self.profile, category="foreign_article", journal_scope="scopus_wos",
            indexed_in="both", scopus_quartile="Q1", wos_quartile="Q3", doi="10.1/a", year=2024,
        )
        make_work(
            self.profile, category="foreign_article", journal_scope="scopus_wos",
            indexed_in="scopus", scopus_quartile="Q1", doi="10.1/b", year=2024,
        )
        works = list(ScientificWork.objects.filter(specialist=self.profile))
        report = build_report(works)
        self.assertEqual(report["quartile_matrix"]["scopus"]["Q1"], 2)
        records = resolve_line_records(works, "2.1:scopus:Q1")
        self.assertEqual(len(records), 2)
        records_wos = resolve_line_records(works, "2.1:wos:Q3")
        self.assertEqual(len(records_wos), 1)


class DrilldownAPIPersonalTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.dept = Department.objects.create(name="Geofizika")
        self.profile = make_profile("me@example.com", "me_user", self.dept, last_name="Karimov", first_name="Ali")
        login = self.client.post(reverse("auth-login"), {"login": "me_user", "password": "StrongPass123"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    def test_line_response_matches_count_and_has_no_author_field(self):
        make_work(self.profile, category="other_publication", publication_type="monograph", publisher="P", year=2024)
        response = self.client.get(reverse("report-me-line"), {"code": "5.1", "year": 2024})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertNotIn("authors", response.data["results"][0])

    def test_record_without_file_shows_null_download_url(self):
        make_work(
            self.profile, with_file=False, category="conference_participation",
            conference_name="C", location="Tashkent", event_date="2024-05-01",
            presentation_type="oral", participation_scope="republic", year=2024,
        )
        response = self.client.get(reverse("report-me-line"), {"code": "4.2", "year": 2024})
        self.assertIsNone(response.data["results"][0]["download_url"])

    def test_cannot_access_another_employees_records(self):
        other_dept = Department.objects.create(name="Boshqa")
        other_profile = make_profile("other@example.com", "other_user", other_dept)
        make_work(other_profile, category="other_publication", publication_type="monograph", publisher="P", year=2024)

        response = self.client.get(reverse("report-me-line"), {"code": "5.1", "year": 2024})
        # My own report has zero -- the other employee's record must not appear.
        self.assertEqual(response.data["count"], 0)

    def test_zip_download_contains_only_own_files(self):
        make_work(self.profile, category="other_publication", publication_type="monograph", publisher="P", year=2024, title="MyBook")
        response = self.client.get(reverse("report-me-line-zip"), {"code": "5.1", "year": 2024})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = b"".join(response.streaming_content)
        zf = zipfile.ZipFile(io.BytesIO(content))
        names = zf.namelist()
        self.assertTrue(any("MyBook" in n for n in names))
        self.assertIn("5.1/_haqida.txt", names)

    def test_zip_skips_fileless_and_manifest_notes_it(self):
        make_work(
            self.profile, with_file=False, category="conference_participation",
            conference_name="C", location="Tashkent", event_date="2024-05-01",
            presentation_type="oral", participation_scope="republic", year=2024, title="NoCert",
        )
        response = self.client.get(reverse("report-me-line-zip"), {"code": "4.2", "year": 2024})
        content = b"".join(response.streaming_content)
        zf = zipfile.ZipFile(io.BytesIO(content))
        manifest = zf.read("4.2/_haqida.txt").decode("utf-8")
        self.assertIn("NoCert", manifest)
        self.assertIn("o'tkazib yuborilgan", manifest)
        # Only the manifest itself should be present, no actual PDF.
        self.assertEqual(len(zf.namelist()), 1)


class DrilldownAPIInstituteTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.dept = Department.objects.create(name="Geofizika")
        self.p1 = make_profile("inst1@example.com", "inst1", self.dept, last_name="Karimov", first_name="Ali")
        self.p2 = make_profile("inst2@example.com", "inst2", self.dept, last_name="Yusupova", first_name="Malika")
        self.staff = User.objects.create_user(
            username="staffuser", email="staffx@example.com", password="StrongPass123",
            first_name="S", last_name="T", is_staff=True,
        )
        self.staff.is_active = True
        self.staff.is_email_verified = True
        self.staff.save()

    def _staff_auth(self):
        login = self.client.post(reverse("auth-login"), {"login": "staffuser", "password": "StrongPass123"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    def test_coauthored_work_shows_one_row_with_both_authors(self):
        make_work(self.p1, category="foreign_article", journal_scope="local", doi="10.1/SHARED", year=2024, authorship="main_author")
        make_work(self.p2, category="foreign_article", journal_scope="local", doi="10.1/SHARED", year=2024, authorship="co_author")

        self._staff_auth()
        response = self.client.get(reverse("report-institute-line"), {"code": "2.4", "year": 2024})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        authors = response.data["results"][0]["authors"]
        self.assertEqual(len(authors), 2)
        names = {a["full_name"] for a in authors}
        self.assertEqual(names, {self.p1.user.full_name, self.p2.user.full_name})
        main_flags = {a["full_name"]: a["is_main_author"] for a in authors}
        self.assertTrue(main_flags[self.p1.user.full_name])
        self.assertFalse(main_flags[self.p2.user.full_name])

    def test_non_coauthored_records_each_show_single_author(self):
        make_work(self.p1, category="other_publication", publication_type="monograph", publisher="P1", doi="", year=2024, title="BookOne")
        make_work(self.p2, category="other_publication", publication_type="monograph", publisher="P2", doi="", year=2024, title="BookTwo")

        self._staff_auth()
        response = self.client.get(reverse("report-institute-line"), {"code": "5.1", "year": 2024})
        self.assertEqual(response.data["count"], 2)
        for row in response.data["results"]:
            self.assertEqual(len(row["authors"]), 1)

    def test_non_staff_employee_forbidden(self):
        login = self.client.post(reverse("auth-login"), {"login": "inst1", "password": "StrongPass123"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.get(reverse("report-institute-line"), {"code": "5.1", "year": 2024})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_forbidden(self):
        response = self.client.get(reverse("report-institute-line"), {"code": "5.1", "year": 2024})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_institute_zip_uses_main_author_file_and_names_by_surname(self):
        make_work(self.p1, category="foreign_article", journal_scope="local", doi="10.1/ZIP1", year=2024, authorship="main_author", title="SharedPaper")
        make_work(self.p2, category="foreign_article", journal_scope="local", doi="10.1/ZIP1", year=2024, authorship="co_author", title="SharedPaper")

        self._staff_auth()
        response = self.client.get(reverse("report-institute-line-zip"), {"code": "2.4", "year": 2024})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = b"".join(response.streaming_content)
        zf = zipfile.ZipFile(io.BytesIO(content))
        names = zf.namelist()
        self.assertTrue(any("Karimov" in n and "SharedPaper" in n for n in names))
        # Only ONE pdf entry for the deduplicated pair, plus the manifest.
        pdf_entries = [n for n in names if n.endswith(".pdf")]
        self.assertEqual(len(pdf_entries), 1)

    def test_institute_zip_non_staff_forbidden(self):
        login = self.client.post(reverse("auth-login"), {"login": "inst1", "password": "StrongPass123"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.get(reverse("report-institute-line-zip"), {"code": "5.1", "year": 2024})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ZipManyRecordsSmokeTest(APITestCase):
    """50 records -- confirms the streaming path holds up at moderate
    scale without errors (a true memory-profile test is out of scope for
    a unit test, but this exercises the exact same generator-based code
    path used in production)."""

    def setUp(self):
        cache.clear()
        self.dept = Department.objects.create(name="Geofizika")
        self.profile = make_profile("bulk@example.com", "bulk_user", self.dept)
        login = self.client.post(reverse("auth-login"), {"login": "bulk_user", "password": "StrongPass123"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    def test_fifty_records_zip_correctly(self):
        for i in range(50):
            make_work(
                self.profile, category="other_publication", publication_type="monograph",
                publisher="P", year=2024, title=f"Book{i}",
            )
        response = self.client.get(reverse("report-me-line-zip"), {"code": "5.1", "year": 2024})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = b"".join(response.streaming_content)
        zf = zipfile.ZipFile(io.BytesIO(content))
        pdf_entries = [n for n in zf.namelist() if n.endswith(".pdf")]
        self.assertEqual(len(pdf_entries), 50)
        self.assertEqual(len(set(pdf_entries)), 50)  # all unique names
