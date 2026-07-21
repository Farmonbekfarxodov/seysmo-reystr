from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from specialists.models import Department, ScientificWork, SpecialistProfile


class PublicSearchTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.geo = Department.objects.create(name="Geofizika")
        self.risk = Department.objects.create(name="Seysmik xavf")

        self.verified = self._make_specialist(
            "verified@example.com", "verified", "Ivanova", "Elena", self.geo, verified=True,
        )
        self.unverified = self._make_specialist(
            "unverified@example.com", "unverified", "Unverified", "Person", self.risk, verified=False,
        )
        # Deliberately set the legacy fields to "hidden"/"rejected" values to
        # prove they no longer affect visibility -- there's no moderation
        # step and no visibility toggle anymore.
        self.legacy_hidden_rejected = self._make_specialist(
            "legacy@example.com", "legacy", "Legacy", "Person", self.risk, verified=True,
            is_public=False, moderation_status="rejected",
        )

    def _make_specialist(self, email, username, last, first, department, *, verified, **profile_kwargs):
        user = User.objects.create_user(
            username=username, email=email, password="StrongPass123", first_name=first, last_name=last,
        )
        user.is_active = verified
        user.is_email_verified = verified
        user.save()
        SpecialistProfile.objects.create(user=user, department=department, **profile_kwargs)
        return user

    def test_departments_list_is_public(self):
        response = self.client.get(reverse("department-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_search_is_public_no_auth_required(self):
        response = self.client.get(reverse("specialist-search"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_returns_all_verified_accounts_regardless_of_legacy_fields(self):
        response = self.client.get(reverse("specialist-search"))
        self.assertEqual(response.data["count"], 2)
        names = {r["full_name"] for r in response.data["results"]}
        self.assertEqual(names, {"Ivanova Elena", "Legacy Person"})

    def test_search_card_includes_works_count(self):
        response = self.client.get(reverse("specialist-search"), {"name": "Ivanova"})
        self.assertEqual(response.data["results"][0]["works_count"], 0)

    def test_unverified_account_never_appears_in_public_search(self):
        response = self.client.get(reverse("specialist-search"), {"name": "Unverified"})
        self.assertEqual(response.data["count"], 0)

    def test_search_filters_by_department_slug(self):
        response = self.client.get(reverse("specialist-search"), {"department": self.geo.slug})
        self.assertEqual(response.data["count"], 1)

    def test_unverified_account_detail_not_found_publicly(self):
        response = self.client.get(reverse("specialist-detail", kwargs={"id": self.unverified.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_legacy_hidden_rejected_account_detail_still_publicly_visible(self):
        response = self.client.get(
            reverse("specialist-detail", kwargs={"id": self.legacy_hidden_rejected.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_detail_never_exposes_email_or_username(self):
        response = self.client.get(reverse("specialist-detail", kwargs={"id": self.verified.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("email", response.data)
        self.assertNotIn("username", response.data)

    def test_public_detail_includes_works_counts(self):
        response = self.client.get(reverse("specialist-detail", kwargs={"id": self.verified.id}))
        self.assertEqual(response.data["works_count"], 0)
        self.assertEqual(
            set(response.data["works_by_category"].keys()),
            {"foreign_article", "local_article", "thesis", "patent", "monograph"},
        )


class ScientificWorkTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.department = Department.objects.create(name="Geofizika")
        self.user = User.objects.create_user(
            username="researcher", email="researcher@example.com", password="StrongPass123",
            first_name="Re", last_name="Searcher",
        )
        self.user.is_active = True
        self.user.is_email_verified = True
        self.user.save()
        self.profile = SpecialistProfile.objects.create(user=self.user, department=self.department)

        login = self.client.post(reverse("auth-login"), {"login": "researcher", "password": "StrongPass123"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    def _pdf(self, name="article.pdf"):
        return SimpleUploadedFile(name, b"%PDF-1.4 fake pdf content", content_type="application/pdf")

    # --- basic create/list/PDF enforcement ---------------------------------

    def test_foreign_article_with_all_required_fields_succeeds(self):
        response = self.client.post(reverse("my-works-list-create"), {
            "category": "foreign_article", "title": "Test Article", "doi": "10.1/abc",
            "year": 2024, "authorship": "main_author", "file": self._pdf(),
        }, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.profile.works.count(), 1)

    def test_foreign_article_missing_doi_rejected(self):
        response = self.client.post(reverse("my-works-list-create"), {
            "category": "foreign_article", "title": "Test Article",
            "year": 2024, "authorship": "main_author", "file": self._pdf(),
        }, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("doi", response.data)

    def test_local_article_missing_journal_name_rejected(self):
        response = self.client.post(reverse("my-works-list-create"), {
            "category": "local_article", "title": "Test", "doi": "10.1/xyz", "year": 2024,
            "link": "https://example.com", "authorship": "main_author", "file": self._pdf(),
        }, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("journal_name", response.data)

    def test_local_article_missing_link_rejected(self):
        response = self.client.post(reverse("my-works-list-create"), {
            "category": "local_article", "title": "Test", "journal_name": "J", "doi": "10.1/xyz",
            "year": 2024, "authorship": "main_author", "file": self._pdf(),
        }, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("link", response.data)

    def test_patent_missing_certificate_number_rejected(self):
        response = self.client.post(reverse("my-works-list-create"), {
            "category": "patent", "title": "Test Patent", "patent_category": "invention",
            "patent_type": "local", "issued_date": "2024-05-01", "authorship": "main_author",
            "file": self._pdf(),
        }, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("certificate_number", response.data)

    def test_patent_does_not_require_doi_or_plain_year(self):
        response = self.client.post(reverse("my-works-list-create"), {
            "category": "patent", "title": "Test Patent", "patent_category": "invention",
            "patent_type": "local", "certificate_number": "AB-123",
            "issued_date": "2024-05-01", "authorship": "main_author", "file": self._pdf(),
        }, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # year is auto-derived from issued_date for cross-category sorting.
        self.assertEqual(response.data["year"], 2024)

    def test_monograph_missing_publisher_rejected(self):
        response = self.client.post(reverse("my-works-list-create"), {
            "category": "monograph", "title": "Test Book", "year": 2024,
            "authorship": "main_author", "file": self._pdf(),
        }, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("publisher", response.data)

    def test_thesis_missing_thesis_category_rejected(self):
        response = self.client.post(reverse("my-works-list-create"), {
            "category": "thesis", "title": "Test Thesis", "journal_name": "Conf",
            "year": 2024, "authorship": "main_author", "file": self._pdf(),
        }, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("thesis_category", response.data)

    def test_every_category_rejects_submission_without_pdf(self):
        response = self.client.post(reverse("my-works-list-create"), {
            "category": "monograph", "title": "No File", "publisher": "Pub",
            "year": 2024, "authorship": "main_author",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_non_pdf_upload_rejected(self):
        fake = SimpleUploadedFile("not-a-pdf.pdf", b"this is definitely not a pdf", content_type="application/pdf")
        response = self.client.post(reverse("my-works-list-create"), {
            "category": "monograph", "title": "Fake", "publisher": "Pub",
            "year": 2024, "authorship": "main_author", "file": fake,
        }, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_docx_renamed_to_pdf_fails_magic_byte_check(self):
        fake = SimpleUploadedFile("renamed.pdf", b"PK\x03\x04 this is a docx zip header", content_type="application/pdf")
        response = self.client.post(reverse("my-works-list-create"), {
            "category": "monograph", "title": "Fake", "publisher": "Pub",
            "year": 2024, "authorship": "main_author", "file": fake,
        }, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_cap_on_work_count(self):
        for i in range(7):
            response = self.client.post(reverse("my-works-list-create"), {
                "category": "monograph", "title": f"Book {i}", "publisher": "Pub",
                "year": 2024, "authorship": "main_author", "file": self._pdf(f"book{i}.pdf"),
            }, format="multipart")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.profile.works.count(), 7)

    # --- update / delete -----------------------------------------------

    def _create_work(self, **overrides):
        payload = {
            "category": "monograph", "title": "Original", "publisher": "Pub",
            "year": 2024, "authorship": "main_author", "file": self._pdf(),
        }
        payload.update(overrides)
        response = self.client.post(reverse("my-works-list-create"), payload, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        return response.data["id"]

    def test_update_metadata_without_touching_file(self):
        work_id = self._create_work()
        response = self.client.patch(
            reverse("my-work-detail", kwargs={"id": work_id}), {"title": "Updated title"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated title")

    def test_update_can_replace_file(self):
        work_id = self._create_work()
        response = self.client.patch(
            reverse("my-work-detail", kwargs={"id": work_id}),
            {"file": self._pdf("replacement.pdf")},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["original_filename"], "replacement.pdf")

    def test_delete_work(self):
        work_id = self._create_work()
        response = self.client.delete(reverse("my-work-detail", kwargs={"id": work_id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.profile.works.count(), 0)

    def test_cannot_access_another_employees_work(self):
        other_dept = Department.objects.create(name="Boshqa")
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="StrongPass123",
            first_name="Other", last_name="Person",
        )
        other_user.is_active = True
        other_user.is_email_verified = True
        other_user.save()
        other_profile = SpecialistProfile.objects.create(user=other_user, department=other_dept)
        other_work = ScientificWork.objects.create(
            specialist=other_profile, category="monograph", title="Not yours", publisher="Pub",
            year=2024, authorship="main_author", file=self._pdf(), original_filename="x.pdf", size=10,
        )
        response = self.client.delete(reverse("my-work-detail", kwargs={"id": other_work.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- DOI duplicate confirm flow --------------------------------------

    def test_duplicate_doi_same_employee_warns_then_confirm_succeeds(self):
        self._create_work(category="foreign_article", title="A", publisher="Pub", doi="10.1/dup", year=2024)

        warn = self.client.post(reverse("my-works-list-create"), {
            "category": "foreign_article", "title": "B", "doi": "10.1/dup",
            "year": 2024, "authorship": "main_author", "file": self._pdf("b.pdf"),
        }, format="multipart")
        self.assertEqual(warn.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(warn.data.get("code")[0]), "duplicate_doi")

        confirmed = self.client.post(reverse("my-works-list-create"), {
            "category": "foreign_article", "title": "B", "doi": "10.1/dup",
            "year": 2024, "authorship": "main_author", "file": self._pdf("b2.pdf"),
            "confirm_duplicate": "true",
        }, format="multipart")
        self.assertEqual(confirmed.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.profile.works.filter(doi="10.1/dup").count(), 2)

    def test_duplicate_doi_across_different_employees_is_allowed(self):
        self._create_work(category="foreign_article", title="A", publisher="Pub", doi="10.1/shared", year=2024)

        other_dept = Department.objects.create(name="Boshqa2")
        other_user = User.objects.create_user(
            username="other2", email="other2@example.com", password="StrongPass123",
            first_name="Other", last_name="Two",
        )
        other_user.is_active = True
        other_user.is_email_verified = True
        other_user.save()
        SpecialistProfile.objects.create(user=other_user, department=other_dept)

        login = self.client.post(reverse("auth-login"), {"login": "other2", "password": "StrongPass123"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        response = self.client.post(reverse("my-works-list-create"), {
            "category": "foreign_article", "title": "Shared DOI work", "doi": "10.1/shared",
            "year": 2024, "authorship": "main_author", "file": self._pdf(),
        }, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # --- public visibility -----------------------------------------------

    def test_public_works_endpoint_returns_only_verified_employees_works(self):
        self._create_work()
        response = self.client.get(reverse("specialist-works-public", kwargs={"id": self.user.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_public_works_endpoint_404s_for_unverified_employee(self):
        unverified = User.objects.create_user(
            username="unverified2", email="unverified2@example.com", password="StrongPass123",
            first_name="Un", last_name="Verified",
        )
        SpecialistProfile.objects.create(user=unverified, department=self.department)
        response = self.client.get(reverse("specialist-works-public", kwargs={"id": unverified.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_works_endpoint_filters_by_category(self):
        self._create_work(category="monograph")
        self._create_work(
            category="foreign_article", title="FA", publisher="", doi="10.1/cat-filter", year=2024
        )
        response = self.client.get(
            reverse("specialist-works-public", kwargs={"id": self.user.id}), {"category": "monograph"}
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["category"], "monograph")
