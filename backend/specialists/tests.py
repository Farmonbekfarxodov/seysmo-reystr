from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from specialists.models import Department, SpecialistProfile


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
        # Both verified employees appear, including the one with legacy
        # is_public=False / moderation_status=rejected -- those fields are
        # no longer read by the application.
        response = self.client.get(reverse("specialist-search"))
        self.assertEqual(response.data["count"], 2)
        names = {r["full_name"] for r in response.data["results"]}
        self.assertEqual(names, {"Ivanova Elena", "Legacy Person"})

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
        # Documents ARE public here -- they're the researcher's published
        # articles, which is the whole point of this registry.
        self.assertIn("documents", response.data)


class DocumentUploadTests(APITestCase):
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

    def test_pdf_upload_succeeds(self):
        response = self.client.post(
            reverse("specialist-me-documents"), {"file": self._pdf()}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.profile.documents.count(), 1)

    def test_non_pdf_upload_rejected(self):
        image = SimpleUploadedFile("photo.png", b"not really a png", content_type="image/png")
        response = self.client.post(
            reverse("specialist-me-documents"), {"file": image}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_cap_on_document_count(self):
        for i in range(7):
            response = self.client.post(
                reverse("specialist-me-documents"), {"file": self._pdf(f"article{i}.pdf")}, format="multipart"
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.profile.documents.count(), 7)

    def test_uploaded_document_appears_in_public_detail(self):
        self.client.post(reverse("specialist-me-documents"), {"file": self._pdf("published.pdf")}, format="multipart")
        response = self.client.get(reverse("specialist-detail", kwargs={"id": self.user.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["documents"]), 1)
        self.assertEqual(response.data["documents"][0]["original_filename"], "published.pdf")

    def test_register_endpoint_no_longer_accepts_documents(self):
        # Documents are dashboard-only now -- register/ shouldn't create any
        # even if a client tries to sneak a "documents" field in.
        response = self.client.post(
            reverse("auth-register"),
            {
                "last_name": "New", "first_name": "Person", "email": "new.person@example.com",
                "username": "new_person", "password": "StrongPass123", "password_confirm": "StrongPass123",
                "department": self.department.id, "documents": [self._pdf()],
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_user = User.objects.get(email="new.person@example.com")
        self.assertEqual(new_user.specialist_profile.documents.count(), 0)
