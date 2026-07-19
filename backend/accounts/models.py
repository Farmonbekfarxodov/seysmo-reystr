from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractUser):
    """Every self-registered account is an institute employee/specialist --
    there is no role field. Admins are identified via is_staff/is_superuser."""

    patronymic = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(
        default=False,
        help_text="Set to True once the user confirms their email address.",
    )

    objects = UserManager()

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.username} <{self.email}>"

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.patronymic]
        return " ".join(p for p in parts if p)


class EmailVerificationCode(models.Model):
    """A one-time 6-digit code confirming a user's email address. Only the
    hash is persisted, never the raw code."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="verification_codes")
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts_used = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def set_code(self, raw_code: str):
        self.code_hash = make_password(raw_code)

    def check_code(self, raw_code: str) -> bool:
        return check_password(raw_code, self.code_hash)

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_locked(self) -> bool:
        from django.conf import settings

        return self.attempts_used >= settings.EMAIL_VERIFICATION_MAX_ATTEMPTS

    def __str__(self):
        return f"Code for {self.user.email} (used={self.is_used})"
