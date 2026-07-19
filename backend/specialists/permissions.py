from rest_framework import permissions


class IsVerifiedSpecialist(permissions.BasePermission):
    """Grants access only to authenticated, email-verified users who have
    a SpecialistProfile. There is no approval step -- verifying email is
    the only gate for dashboard access."""

    message = "Faqat tasdiqlangan email manzilga ega xodimlar uchun."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_email_verified
            and hasattr(user, "specialist_profile")
        )
