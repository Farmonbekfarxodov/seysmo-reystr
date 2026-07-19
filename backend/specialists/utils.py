from django.conf import settings
from django.core.mail import send_mail


def notify_moderation_result(profile):
    """Emails the employee when an admin approves or rejects their profile.
    Called from SpecialistProfile.save() on a genuine status transition."""

    if profile.moderation_status == profile.ModerationStatus.APPROVED:
        subject = "Profilingiz tasdiqlandi"
        message = (
            f"Assalomu alaykum, {profile.user.first_name}!\n\n"
            "Profilingiz administrator tomonidan tasdiqlandi va endi institut "
            "xodimlari reyestrida ko'rinadi (agar ko'rinish yoqilgan bo'lsa).\n\n"
            "Profilingizni shaxsiy kabinetdan tahrirlashingiz mumkin."
        )
    elif profile.moderation_status == profile.ModerationStatus.REJECTED:
        subject = "Profilingiz bo'yicha qaror"
        reason = profile.rejection_reason or "Sabab ko'rsatilmagan."
        message = (
            f"Assalomu alaykum, {profile.user.first_name}!\n\n"
            "Afsuski, profilingiz hozircha tasdiqlanmadi.\n"
            f"Sabab: {reason}\n\n"
            "Ma'lumotlaringizni yangilab, qayta ko'rib chiqilishini so'rashingiz mumkin."
        )
    else:
        return

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[profile.user.email],
        fail_silently=True,
    )
