from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import EmailVerificationCode, User
from accounts.utils import latest_verification_for
from specialists.models import Department, SpecialistProfile


class RegistrationAndVerificationTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.department = Department.objects.create(name="Geofizika")

    def _register(self, **overrides):
        payload = dict(
            last_name="Aliyeva",
            first_name="Nilufar",
            patronymic="",
            email="nilufar@example.com",
            username="nilufar",
            password="StrongPass123",
            password_confirm="StrongPass123",
            academic_degree="phd",
            academic_title="none",
            position="junior_researcher",
            department=self.department.id,
            research_interests="Seysmik to'lqinlar",
        )
        payload.update(overrides)
        return self.client.post(reverse("auth-register"), payload)

    def test_register_creates_inactive_unverified_profile(self):
        response = self._register()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="nilufar@example.com")
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_email_verified)
        self.assertTrue(hasattr(user, "specialist_profile"))
        self.assertEqual(EmailVerificationCode.objects.filter(user=user).count(), 1)

    def test_passwords_must_match(self):
        response = self._register(password_confirm="Different123")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_email_rejected(self):
        self._register()
        response = self._register(username="another")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_department_is_required_and_must_exist(self):
        response = self._register(department=99999)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_with_correct_code_activates_account(self):
        from django.utils import timezone

        self._register()
        user = User.objects.get(email="nilufar@example.com")
        EmailVerificationCode.objects.filter(user=user).delete()
        raw_code = "123456"
        verification = EmailVerificationCode(
            user=user, expires_at=timezone.now() + timezone.timedelta(minutes=15)
        )
        verification.set_code(raw_code)
        verification.save()

        response = self.client.post(
            reverse("auth-verify-email"), {"email": user.email, "code": raw_code}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)
        # No approval step -- verification alone makes the profile public.
        self.assertTrue(user.specialist_profile.is_searchable)

    def test_verify_email_with_wrong_code_fails_and_counts_attempt(self):
        self._register()
        user = User.objects.get(email="nilufar@example.com")

        response = self.client.post(
            reverse("auth-verify-email"), {"email": user.email, "code": "000000"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        verification = latest_verification_for(user)
        self.assertEqual(verification.attempts_used, 1)


class LoginTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.department = Department.objects.create(name="Geofizika")
        self.user = User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="StrongPass123",
            first_name="Log",
            last_name="In",
        )
        self.user.is_active = True
        self.user.is_email_verified = True
        self.user.save()
        SpecialistProfile.objects.create(user=self.user, department=self.department)

    def test_login_with_username_returns_tokens(self):
        response = self.client.post(
            reverse("auth-login"), {"login": "loginuser", "password": "StrongPass123"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_email_returns_tokens(self):
        response = self.client.post(
            reverse("auth-login"), {"login": "login@example.com", "password": "StrongPass123"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_returns_no_moderation_fields(self):
        # There's no approval workflow -- the login response's user object
        # shouldn't carry any moderation-related keys.
        response = self.client.post(
            reverse("auth-login"), {"login": "loginuser", "password": "StrongPass123"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("moderation_status", response.data["user"])
        self.assertNotIn("rejection_reason", response.data["user"])

    def test_login_wrong_password_fails(self):
        response = self.client.post(
            reverse("auth-login"), {"login": "loginuser", "password": "WrongPass"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unverified_account_blocked(self):
        self.user.is_email_verified = False
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            reverse("auth-login"), {"login": "loginuser", "password": "StrongPass123"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data.get("code")[0]), "unverified_email")
