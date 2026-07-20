import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.utils.text import slugify
from PIL import Image, ImageOps

from .validators import validate_photo, validate_uploaded_document


class Department(models.Model):
    """An institute department (e.g. Seysmik xavf). Admin-managed; a real
    dropdown at registration, not free text."""

    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


def document_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    unique_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    return f"specialist_documents/{instance.specialist.user_id}/{unique_name}"


def photo_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    return f"specialist_photos/{instance.user_id}/{uuid.uuid4().hex}.{ext}"


class SpecialistProfile(models.Model):
    class AcademicDegree(models.TextChoices):
        NONE = "none", "Yo'q"
        BSC = "bsc", "Bakalavr"
        MSC = "msc", "Magistr"
        PHD = "phd", "PhD"
        DSC = "dsc", "DSc"
        CANDIDATE_LEGACY = "candidate_legacy", "Fan nomzodi"
        DOCTOR_LEGACY = "doctor_legacy", "Fan doktori"

    class AcademicTitle(models.TextChoices):
        NONE = "none", "Yo'q"
        SENIOR_RESEARCHER = "senior_researcher", "Katta ilmiy xodim"
        DOCENT = "docent", "Dotsent"
        PROFESSOR = "professor", "Professor"
        ACADEMICIAN = "academician", "Akademik"

    class Position(models.TextChoices):
        JUNIOR_RESEARCHER = "junior_researcher", "Kichik ilmiy xodim"
        SENIOR_RESEARCHER = "senior_researcher", "Katta ilmiy xodim"
        LEADING_RESEARCHER = "leading_researcher", "Yetakchi ilmiy xodim"
        CHIEF_RESEARCHER = "chief_researcher", "Bosh ilmiy xodim"
        LAB_HEAD = "lab_head", "Laboratoriya mudiri"
        DEPARTMENT_HEAD = "department_head", "Bo'lim boshlig'i"

    class ModerationStatus(models.TextChoices):
        PENDING = "pending", "Kutilmoqda"
        APPROVED = "approved", "Tasdiqlangan"
        REJECTED = "rejected", "Rad etilgan"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="specialist_profile"
    )
    photo = models.ImageField(
        upload_to=photo_upload_path, blank=True, null=True, validators=[validate_photo]
    )
    photo_thumbnail = models.ImageField(upload_to=photo_upload_path, blank=True, null=True)

    academic_degree = models.CharField(
        max_length=20, choices=AcademicDegree.choices, default=AcademicDegree.NONE
    )
    academic_title = models.CharField(
        max_length=20, choices=AcademicTitle.choices, default=AcademicTitle.NONE
    )
    position = models.CharField(max_length=30, choices=Position.choices, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="specialists")
    research_interests = models.TextField(blank=True)
    bio = models.TextField(blank=True)

    # NOTE: is_public / moderation_status / rejection_reason are kept only
    # to avoid a schema migration -- the application no longer reads or
    # writes them. Every verified, active account's profile is public (see
    # SpecialistProfile.is_searchable and specialists.views.PUBLIC_QUERYSET).
    # There is no admin approval step.
    is_public = models.BooleanField(default=True)
    moderation_status = models.CharField(
        max_length=20, choices=ModerationStatus.choices, default=ModerationStatus.PENDING
    )
    rejection_reason = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Snapshot the photo's original filename to detect changes in
        # save() below -- but ONLY for fully-loaded instances. Partial/
        # deferred instances (e.g. Django admin's delete-confirmation
        # screen uses .only()-style queries when collecting cascade-delete
        # candidates) don't have every field loaded; touching a deferred
        # field triggers a lazy refresh_from_db() we want to avoid here.
        deferred = self.get_deferred_fields()
        self._original_photo_name = (
            (self.photo.name if self.photo else None) if "photo" not in deferred else None
        )

    def __str__(self):
        return f"{self.user.full_name} — {self.department}"

    @property
    def is_searchable(self) -> bool:
        """Every verified, active account's profile is public -- there is
        no admin approval step and no visibility toggle."""
        return self.user.is_email_verified and self.user.is_active

    def save(self, *args, **kwargs):
        photo_name_now = self.photo.name if self.photo else None
        photo_changed = photo_name_now != self._original_photo_name

        super().save(*args, **kwargs)

        if photo_changed:
            if self.photo:
                self._process_photo()
            elif self.photo_thumbnail:
                self.photo_thumbnail.storage.delete(self.photo_thumbnail.name)
                SpecialistProfile.objects.filter(pk=self.pk).update(photo_thumbnail="")
                self.photo_thumbnail.name = ""

        self._original_photo_name = self.photo.name if self.photo else None

    def _process_photo(self):
        """Strip EXIF metadata (re-encoding drops it), auto-rotate based on
        the original EXIF orientation, and generate a centered square
        thumbnail -- all via Pillow, storage-API-based so it stays
        S3-compatible."""
        width, height = settings.PHOTO_THUMBNAIL_SIZE

        with self.photo.open("rb") as f:
            img = Image.open(f)
            img = ImageOps.exif_transpose(img)
            if img.mode != "RGB":
                img = img.convert("RGB")

            main_buffer = BytesIO()
            img.save(main_buffer, format="JPEG", quality=90)
            main_bytes = main_buffer.getvalue()

            thumb = ImageOps.fit(img, (width, height), Image.LANCZOS)
            thumb_buffer = BytesIO()
            thumb.save(thumb_buffer, format="JPEG", quality=85)
            thumb_bytes = thumb_buffer.getvalue()

        old_name = self.photo.name
        new_name = old_name.rsplit(".", 1)[0] + ".jpg"
        self.photo.storage.delete(old_name)
        saved_photo_name = self.photo.storage.save(new_name, ContentFile(main_bytes))

        if self.photo_thumbnail:
            self.photo_thumbnail.storage.delete(self.photo_thumbnail.name)
        thumb_path = f"specialist_photos/{self.user_id}/{uuid.uuid4().hex}_thumb.jpg"
        saved_thumb_name = self.photo_thumbnail.storage.save(thumb_path, ContentFile(thumb_bytes))

        SpecialistProfile.objects.filter(pk=self.pk).update(
            photo=saved_photo_name, photo_thumbnail=saved_thumb_name
        )
        self.photo.name = saved_photo_name
        self.photo_thumbnail.name = saved_thumb_name


class SpecialistDocument(models.Model):
    specialist = models.ForeignKey(SpecialistProfile, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to=document_upload_path, validators=[validate_uploaded_document])
    original_filename = models.CharField(max_length=255)
    size = models.PositiveIntegerField(help_text="File size in bytes")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.original_filename
