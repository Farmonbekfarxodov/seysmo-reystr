from django.contrib import admin
from django.utils.html import format_html

from .models import Department, SpecialistDocument, SpecialistProfile


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "staff_count"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]

    @admin.display(description="Xodimlar soni")
    def staff_count(self, obj):
        return obj.specialists.count()


class DocumentInline(admin.TabularInline):
    model = SpecialistDocument
    extra = 0
    fields = ["original_filename", "file", "size", "uploaded_at"]
    readonly_fields = ["original_filename", "file", "size", "uploaded_at"]


@admin.register(SpecialistProfile)
class SpecialistProfileAdmin(admin.ModelAdmin):
    list_display = [
        "photo_preview",
        "user",
        "academic_degree",
        "position",
        "department",
        "created_at",
    ]
    list_filter = ["department", "academic_degree", "academic_title"]
    search_fields = ["user__email", "user__username", "user__last_name", "user__first_name"]
    inlines = [DocumentInline]
    readonly_fields = ["photo_large_preview", "created_at", "updated_at"]
    fieldsets = (
        (None, {"fields": ("user", "photo", "photo_large_preview")}),
        ("Academic info", {
            "fields": ("academic_degree", "academic_title", "position", "department")
        }),
        ("Profile content", {"fields": ("research_interests", "bio")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Rasm")
    def photo_preview(self, obj):
        if obj.photo_thumbnail:
            return format_html(
                '<img src="{}" style="width:32px;height:32px;border-radius:50%;object-fit:cover;" />',
                obj.photo_thumbnail.url,
            )
        return "—"

    @admin.display(description="Joriy rasm")
    def photo_large_preview(self, obj):
        if obj.photo_thumbnail:
            return format_html(
                '<img src="{}" style="width:160px;height:160px;border-radius:12px;object-fit:cover;" />',
                obj.photo_thumbnail.url,
            )
        return "Rasm yuklanmagan."


@admin.register(SpecialistDocument)
class SpecialistDocumentAdmin(admin.ModelAdmin):
    list_display = ["original_filename", "specialist", "size", "uploaded_at"]
    search_fields = ["original_filename", "specialist__user__email"]
