import secrets

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailVerificationCode


class EmailCodeRateLimited(Exception):
    """Raised when a user has requested too many codes within the hour."""


def generate_numeric_code(length: int = 6) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(length))


def codes_sent_in_last_hour(user) -> int:
    one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
    return EmailVerificationCode.objects.filter(user=user, created_at__gte=one_hour_ago).count()


def issue_verification_code(user) -> EmailVerificationCode:
    if codes_sent_in_last_hour(user) >= settings.EMAIL_VERIFICATION_MAX_CODES_PER_HOUR:
        raise EmailCodeRateLimited(
            f"Only {settings.EMAIL_VERIFICATION_MAX_CODES_PER_HOUR} codes are allowed per hour."
        )

    raw_code = generate_numeric_code()
    expires_at = timezone.now() + timezone.timedelta(minutes=settings.EMAIL_VERIFICATION_CODE_TTL_MINUTES)
    verification = EmailVerificationCode(user=user, expires_at=expires_at)
    verification.set_code(raw_code)
    verification.save()

    send_mail(
        subject="Seysmologiya instituti — tasdiqlash kodi",
        message=(
            f"Assalomu alaykum, {user.first_name}!\n\n"
            f"Tasdiqlash kodingiz: {raw_code}\n"
            f"Kod {settings.EMAIL_VERIFICATION_CODE_TTL_MINUTES} daqiqadan so'ng amal qilishdan to'xtaydi.\n\n"
            "Agar siz bu so'rovni yubormagan bo'lsangiz, bu xabarni e'tiborsiz qoldiring."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return verification


def latest_verification_for(user):
    return user.verification_codes.order_by("-created_at").first()
