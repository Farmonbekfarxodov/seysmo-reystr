import datetime

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from specialists.models import Department, ScientificWork, SpecialistProfile
from specialists.report_codes import build_report, compute_report_code, deduplicate_works


def make_profile(email, username, department):
    user = User.objects.create_user(
        username=username, email=email, password="StrongPass123", first_name="F", last_name="L",
    )
    user.is_active = True
    user.is_email_verified = True
    user.save()
    return SpecialistProfile.objects.create(user=user, department=department)


def make_work(profile, **kwargs):
    defaults = dict(specialist=profile, title="T", authorship="main_author", original_filename="x.pdf", size=10)
    defaults.update(kwargs)
    return ScientificWork.objects.create(**defaults)


class ReportCodeDerivationTests(TestCase):
    """Every category x classification combination -> the exact code."""

    def setUp(self):
        self.dept = Department.objects.create(name="Geofizika")
        self.profile = make_profile("rc@example.com", "rc_user", self.dept)

    def test_articles_all_journal_scopes(self):
        cases = [
            ("scopus_wos", "2.1"), ("other_foreign", "2.2"), ("cis", "2.3"), ("local", "2.4"), ("", ""),
        ]
        for scope, expected in cases:
            w = make_work(self.profile, category="foreign_article", journal_scope=scope)
            self.assertEqual(w.report_code, expected, f"journal_scope={scope}")

    def test_thesis_scopus_wos_cis_local_subsets(self):
        w1 = make_work(self.profile, category="thesis", conference_scope="scopus_wos")
        self.assertEqual(w1.report_code, "3.1")
        w2 = make_work(self.profile, category="thesis", conference_scope="other_foreign")
        self.assertEqual(w2.report_code, "3.2")
        w3 = make_work(self.profile, category="thesis", conference_scope="cis")
        self.assertEqual(w3.report_code, "3.3")
        w4 = make_work(self.profile, category="thesis", conference_scope="local", local_conf_level="international")
        self.assertEqual(w4.report_code, "3.4.1")
        w5 = make_work(self.profile, category="thesis", conference_scope="local", local_conf_level="republic")
        self.assertEqual(w5.report_code, "3.4.2")
        w6 = make_work(self.profile, category="thesis", conference_scope="local")  # missing level
        self.assertEqual(w6.report_code, "")

    def test_conference_participation(self):
        w1 = make_work(self.profile, category="conference_participation", participation_scope="foreign")
        self.assertEqual(w1.report_code, "4.1")
        w2 = make_work(self.profile, category="conference_participation", participation_scope="republic")
        self.assertEqual(w2.report_code, "4.2")

    def test_other_publication_types(self):
        w1 = make_work(self.profile, category="other_publication", publication_type="monograph")
        self.assertEqual(w1.report_code, "5.1")
        w2 = make_work(self.profile, category="other_publication", publication_type="textbook")
        self.assertEqual(w2.report_code, "5.3")
        w3 = make_work(self.profile, category="other_publication", publication_type="manual")
        self.assertEqual(w3.report_code, "5.5")

    def test_all_seven_patent_types(self):
        expected = {
            "invention": "6.1", "foreign_patent": "6.2", "utility_model": "6.3",
            "patent_application": "6.4", "trademark": "6.5",
            "software_certificate": "6.6", "license_agreement": "6.7",
        }
        for patent_category, code in expected.items():
            w = make_work(self.profile, category="patent", patent_category=patent_category)
            self.assertEqual(w.report_code, code, f"patent_category={patent_category}")

    def test_recompute_on_edit(self):
        w = make_work(self.profile, category="foreign_article", journal_scope="local")
        self.assertEqual(w.report_code, "2.4")
        w.journal_scope = "scopus_wos"
        w.save()
        self.assertEqual(w.report_code, "2.1")


class ReportYearSourceTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Geofizika")
        self.profile = make_profile("year@example.com", "year_user", self.dept)

    def test_article_uses_year_field(self):
        w = make_work(self.profile, category="foreign_article", journal_scope="local", year=2022)
        self.assertEqual(w.report_year, 2022)

    def test_patent_uses_issued_date(self):
        w = make_work(self.profile, category="patent", patent_category="invention", issued_date=datetime.date(2023, 6, 15), year=1999)
        self.assertEqual(w.report_year, 2023)

    def test_conference_participation_uses_event_date(self):
        w = make_work(self.profile, category="conference_participation", participation_scope="foreign", event_date=datetime.date(2024, 9, 1))
        self.assertEqual(w.report_year, 2024)


class SectionTotalsTests(TestCase):
    """The explicit "jumladan" (subset) counting rule from the spec."""

    def setUp(self):
        self.dept = Department.objects.create(name="Geofizika")
        self.profile = make_profile("totals@example.com", "totals_user", self.dept)

    def test_section_v_total_excludes_subset_inflation(self):
        # Two monographs, one of them also published abroad (5.2 subset);
        # one textbook published abroad (5.4 subset); one manual.
        make_work(self.profile, category="other_publication", publication_type="monograph", published_abroad=False)
        make_work(self.profile, category="other_publication", publication_type="monograph", published_abroad=True)
        make_work(self.profile, category="other_publication", publication_type="textbook", published_abroad=True)
        make_work(self.profile, category="other_publication", publication_type="manual")

        report = build_report(ScientificWork.objects.filter(specialist=self.profile))
        section_v = next(s for s in report["sections"] if s["id"] == "V")
        lines = {l["code"]: l["count"] for l in section_v["lines"]}

        self.assertEqual(lines["5.1"], 2)
        self.assertEqual(lines["5.2"], 1)  # subset, NOT counted in the total
        self.assertEqual(lines["5.3"], 1)
        self.assertEqual(lines["5.4"], 1)  # subset, NOT counted in the total
        self.assertEqual(lines["5.5"], 1)
        self.assertEqual(section_v["total"], 4)  # 5.1(2) + 5.3(1) + 5.5(1), NOT +5.2+5.4

    def test_section_iii_total_combines_local_sublevels_without_double_counting(self):
        make_work(self.profile, category="thesis", conference_scope="scopus_wos")
        make_work(self.profile, category="thesis", conference_scope="other_foreign")
        make_work(self.profile, category="thesis", conference_scope="cis")
        make_work(self.profile, category="thesis", conference_scope="local", local_conf_level="international")
        make_work(self.profile, category="thesis", conference_scope="local", local_conf_level="international")
        make_work(self.profile, category="thesis", conference_scope="local", local_conf_level="republic")

        report = build_report(ScientificWork.objects.filter(specialist=self.profile))
        section_iii = next(s for s in report["sections"] if s["id"] == "III")
        lines = {l["code"]: l["count"] for l in section_iii["lines"]}

        self.assertEqual(lines["3.1"], 1)
        self.assertEqual(lines["3.2"], 1)
        self.assertEqual(lines["3.3"], 1)
        self.assertEqual(lines["3.4"], 3)  # 2 international + 1 republic
        self.assertEqual(lines["3.4.1"], 2)
        self.assertEqual(lines["3.4.2"], 1)
        self.assertEqual(section_iii["total"], 6)  # 1+1+1+3, not 1+1+1+3+2+1

    def test_unclassified_records_excluded_from_all_counts(self):
        make_work(self.profile, category="foreign_article", journal_scope="scopus_wos")  # classified, 2.1
        make_work(self.profile, category="foreign_article")  # unclassified (no journal_scope)

        report = build_report(ScientificWork.objects.filter(specialist=self.profile))
        section_ii = next(s for s in report["sections"] if s["id"] == "II")
        self.assertEqual(section_ii["total"], 1)
        self.assertEqual(len(report["unclassified"]), 1)


class QuartileMatrixTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Geofizika")
        self.profile = make_profile("quartile@example.com", "quartile_user", self.dept)

    def test_quartile_sums_equal_21_count_and_both_fills_two_cells(self):
        make_work(
            self.profile, category="foreign_article", journal_scope="scopus_wos",
            indexed_in="scopus", scopus_quartile="Q1",
        )
        make_work(
            self.profile, category="foreign_article", journal_scope="scopus_wos",
            indexed_in="wos", wos_quartile="Q2",
        )
        # indexed_in=both: fills BOTH matrices without double-counting the
        # record itself in the 2.1 total (it's still just 1 record).
        make_work(
            self.profile, category="foreign_article", journal_scope="scopus_wos",
            indexed_in="both", scopus_quartile="Q1", wos_quartile="Q3",
        )

        report = build_report(ScientificWork.objects.filter(specialist=self.profile))
        section_ii = next(s for s in report["sections"] if s["id"] == "II")
        line_21 = next(l for l in section_ii["lines"] if l["code"] == "2.1")
        self.assertEqual(line_21["count"], 3)  # NOT 4 -- the "both" record counts once

        qm = report["quartile_matrix"]
        self.assertEqual(qm["scopus"]["Q1"], 2)  # the plain scopus one + the "both" one
        self.assertEqual(qm["wos"]["Q2"], 1)
        self.assertEqual(qm["wos"]["Q3"], 1)
        total_scopus = sum(qm["scopus"].values())
        total_wos = sum(qm["wos"].values())
        self.assertEqual(total_scopus, 2)
        self.assertEqual(total_wos, 2)


class DeduplicationTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Geofizika")
        self.p1 = make_profile("dedup1@example.com", "dedup1", self.dept)
        self.p2 = make_profile("dedup2@example.com", "dedup2", self.dept)
        self.p3 = make_profile("dedup3@example.com", "dedup3", self.dept)

    def test_same_doi_three_employees_counts_once_institute_wide(self):
        for profile in (self.p1, self.p2, self.p3):
            make_work(
                profile, category="foreign_article", journal_scope="scopus_wos",
                doi="10.1/SHARED", year=2024,
            )
        all_works = list(ScientificWork.objects.all())
        deduped, groups = deduplicate_works(all_works)
        self.assertEqual(len(deduped), 1)
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]), 3)

    def test_doi_case_and_prefix_normalization(self):
        make_work(self.p1, category="foreign_article", journal_scope="scopus_wos", doi="10.1/Shared", year=2024)
        make_work(self.p2, category="foreign_article", journal_scope="scopus_wos", doi="HTTPS://DOI.ORG/10.1/shared", year=2024)
        deduped, groups = deduplicate_works(list(ScientificWork.objects.all()))
        self.assertEqual(len(deduped), 1)

    def test_different_works_not_merged(self):
        make_work(self.p1, category="foreign_article", journal_scope="scopus_wos", doi="10.1/one", year=2024)
        make_work(self.p2, category="foreign_article", journal_scope="scopus_wos", doi="10.1/two", year=2024)
        deduped, groups = deduplicate_works(list(ScientificWork.objects.all()))
        self.assertEqual(len(deduped), 2)
        self.assertEqual(len(groups), 0)

    def test_no_doi_falls_back_to_title_signature(self):
        make_work(self.p1, category="other_publication", publication_type="monograph", title="Same Title!", year=2024)
        make_work(self.p2, category="other_publication", publication_type="monograph", title="same   title", year=2024)
        deduped, groups = deduplicate_works(list(ScientificWork.objects.all()))
        self.assertEqual(len(deduped), 1)

    def test_personal_reports_are_never_deduplicated(self):
        # Each author's OWN report shows their own record regardless of
        # institute-wide dedup -- build_report on a single employee's
        # queryset is never deduplicated.
        for profile in (self.p1, self.p2):
            make_work(profile, category="foreign_article", journal_scope="scopus_wos", doi="10.1/SHARED", year=2024)
        report_p1 = build_report(ScientificWork.objects.filter(specialist=self.p1))
        section_ii = next(s for s in report_p1["sections"] if s["id"] == "II")
        self.assertEqual(section_ii["total"], 1)  # p1 sees their own 1 record


class ConferenceParticipationFileExceptionTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.dept = Department.objects.create(name="Geofizika")
        self.profile = make_profile("filex@example.com", "filex_user", self.dept)
        login = self.client.post(reverse("auth-login"), {"login": "filex_user", "password": "StrongPass123"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    def test_conference_participation_saves_without_pdf(self):
        response = self.client.post(reverse("my-works-list-create"), {
            "category": "conference_participation", "title": "Talk", "conference_name": "Conf",
            "location": "Tashkent", "event_date": "2024-05-01", "presentation_type": "oral",
            "participation_scope": "republic", "authorship": "main_author",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["report_code"], "4.2")

    def test_other_categories_still_require_pdf(self):
        response = self.client.post(reverse("my-works-list-create"), {
            "category": "other_publication", "title": "Book", "publisher": "Pub",
            "year": 2024, "authorship": "main_author", "publication_type": "monograph",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_without_certificate_flagged_in_report(self):
        self.client.post(reverse("my-works-list-create"), {
            "category": "conference_participation", "title": "Talk", "conference_name": "Conf",
            "location": "Tashkent", "event_date": "2024-05-01", "presentation_type": "oral",
            "participation_scope": "foreign", "authorship": "main_author",
        })
        response = self.client.get(reverse("report-me"), {"year": "2024"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["without_certificate"], 1)


class ReportEndpointAccessTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.dept = Department.objects.create(name="Geofizika")
        self.profile = make_profile("access@example.com", "access_user", self.dept)

    def test_anonymous_cannot_access_my_report(self):
        response = self.client.get(reverse("report-me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_cannot_access_institute_report(self):
        response = self.client.get(reverse("report-institute"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_verified_employee_cannot_access_institute_report(self):
        login = self.client.post(reverse("auth-login"), {"login": "access_user", "password": "StrongPass123"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.get(reverse("report-institute"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_access_institute_report(self):
        staff = User.objects.create_user(
            username="staffuser", email="staff@example.com", password="StrongPass123",
            first_name="S", last_name="T", is_staff=True,
        )
        staff.is_active = True
        staff.is_email_verified = True
        staff.save()
        login = self.client.post(reverse("auth-login"), {"login": "staffuser", "password": "StrongPass123"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.get(reverse("report-institute"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verified_employee_can_access_own_report(self):
        login = self.client.post(reverse("auth-login"), {"login": "access_user", "password": "StrongPass123"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.get(reverse("report-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("sections", response.data)
