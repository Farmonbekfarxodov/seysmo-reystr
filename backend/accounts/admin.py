from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import EmailVerificationCode, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["-date_joined"]
    list_display = ["username", "email", "last_name", "first_name", "is_email_verified", "is_active", "is_staff"]
    list_filter = ["is_email_verified", "is_active", "is_staff"]
    search_fields = ["username", "email", "last_name", "first_name", "patronymic"]
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("last_name", "first_name", "patronymic", "email")}),
        ("Status", {"fields": ("is_active", "is_email_verified", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "last_name", "first_name", "password1", "password2"),
        }),
    )


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at", "expires_at", "attempts_used", "is_used"]
    list_filter = ["is_used"]
    search_fields = ["user__email", "user__username"]
