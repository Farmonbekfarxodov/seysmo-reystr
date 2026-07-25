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
    """Kept only because the already-applied historical migration 0001
    references this by dotted path (FileField.upload_to). Removing it would
    break `migrate` on a fresh install replaying migration history, even
    though the SpecialistDocument model itself is gone."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    unique_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    return f"specialist_documents/{instance.specialist.user_id}/{unique_name}"


def work_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    unique_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    return f"scientific_works/{instance.specialist.user_id}/{unique_name}"


def photo_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    return f"specialist_photos/{instance.user_id}/{uuid.uuid4().hex}.{ext}"


class SpecialistProfile(models.Model):
    class AcademicDegree(models.TextChoices):
        NONE = "none", "Yo'q"
        BACHELOR = "bachelor", "Bakalavr"
        MASTER = "master", "Magistr"
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


class ScientificWork(models.Model):
    """A single scientific work of any of the six categories. One table
    for all categories (category-specific fields are blank when unused);
    required-field enforcement per category lives in the serializer.

    Every record maps to exactly one official annual-report line via
    `report_code` (see specialists/report_codes.py), recomputed on every
    save and backfillable via the `recalc_report_codes` management command.
    """

    class Category(models.TextChoices):
        FOREIGN_ARTICLE = "foreign_article", "Xorijiy maqola"
        LOCAL_ARTICLE = "local_article", "Mahalliy maqola"
        THESIS = "thesis", "Tezis"
        CONFERENCE_PARTICIPATION = "conference_participation", "Anjumanda ishtirok"
        PATENT = "patent", "Patent"
        OTHER_PUBLICATION = "other_publication", "Boshqa nashr"

    class Authorship(models.TextChoices):
        MAIN_AUTHOR = "main_author", "Asosiy muallif"
        CO_AUTHOR = "co_author", "Hammuallif"

    # --- Articles (report section II) --------------------------------
    class JournalScope(models.TextChoices):
        SCOPUS_WOS = "scopus_wos", "Scopus va/yoki Web of Science bazasiga kiritilgan"
        OTHER_FOREIGN = "other_foreign", "Boshqa xorijiy jurnal"
        CIS = "cis", "MDH jurnali"
        LOCAL = "local", "Mahalliy jurnal"

    class IndexedIn(models.TextChoices):
        SCOPUS = "scopus", "Scopus"
        WOS = "wos", "Web of Science"
        BOTH = "both", "Scopus va Web of Science"

    class Quartile(models.TextChoices):
        Q1 = "Q1", "Q1"
        Q2 = "Q2", "Q2"
        Q3 = "Q3", "Q3"
        Q4 = "Q4", "Q4"

    # --- Theses (report section III) ----------------------------------
    class ConferenceScope(models.TextChoices):
        SCOPUS_WOS = "scopus_wos", "Scopus/WoS to'plami"
        OTHER_FOREIGN = "other_foreign", "Boshqa xorijiy anjuman"
        CIS = "cis", "MDH anjumani"
        LOCAL = "local", "Mahalliy anjuman"

    class LocalConfLevel(models.TextChoices):
        INTERNATIONAL = "international", "Xalqaro anjuman"
        REPUBLIC = "republic", "Respublika anjumani"

    # --- Conference participation (report section IV) -----------------
    class PresentationType(models.TextChoices):
        ORAL = "oral", "Og'zaki"
        PLENARY = "plenary", "Plenar"

    class ParticipationScope(models.TextChoices):
        FOREIGN = "foreign", "Xorijiy"
        REPUBLIC = "republic", "Respublika"

    # --- Other publications (report section V) -------------------------
    class PublicationType(models.TextChoices):
        MONOGRAPH = "monograph", "Monografiya"
        TEXTBOOK = "textbook", "Darslik"
        MANUAL = "manual", "O'quv qo'llanma"

    # --- Patents / IP (report section VI) -------------------------------
    class PatentCategory(models.TextChoices):
        INVENTION = "invention", "Ixtiro (patent)"
        FOREIGN_PATENT = "foreign_patent", "Xorijiy patent"
        UTILITY_MODEL = "utility_model", "Foydali modelga patent"
        PATENT_APPLICATION = "patent_application", "Patent uchun talabnoma"
        TRADEMARK = "trademark", "Tovar belgisi"
        SOFTWARE_CERTIFICATE = "software_certificate", "Dasturiy mahsulot guvohnomasi"
        LICENSE_AGREEMENT = "license_agreement", "Litsenziya shartnomasi"

    specialist = models.ForeignKey(SpecialistProfile, on_delete=models.CASCADE, related_name="works")
    category = models.CharField(max_length=30, choices=Category.choices)

    # Common fields
    title = models.CharField(max_length=500)
    year = models.PositiveIntegerField(null=True, blank=True)
    authorship = models.CharField(max_length=20, choices=Authorship.choices, blank=True)
    project_name = models.CharField(max_length=255, blank=True)
    link = models.URLField(max_length=500, blank=True)
    doi = models.CharField(max_length=255, blank=True)

    # PDF is required for every category EXCEPT conference_participation
    # (enforced in the serializer) -- nullable here to allow that exception.
    file = models.FileField(
        upload_to=work_upload_path, blank=True, null=True, validators=[validate_uploaded_document]
    )
    original_filename = models.CharField(max_length=255, blank=True)
    size = models.PositiveIntegerField(null=True, blank=True, help_text="File size in bytes")

    # Articles: journal_scope drives 2.1-2.4; indexed_in/quartiles only
    # apply when journal_scope == scopus_wos.
    journal_scope = models.CharField(max_length=20, choices=JournalScope.choices, blank=True)
    indexed_in = models.CharField(max_length=10, choices=IndexedIn.choices, blank=True)
    scopus_quartile = models.CharField(max_length=2, choices=Quartile.choices, blank=True)
    wos_quartile = models.CharField(max_length=2, choices=Quartile.choices, blank=True)
    publisher = models.CharField(max_length=255, blank=True)  # also used by other_publication
    impact_factor = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)

    # Local article / thesis
    journal_name = models.CharField(max_length=255, blank=True)

    # Thesis: conference_scope drives 3.1-3.4; local_conf_level only
    # applies when conference_scope == local.
    conference_scope = models.CharField(max_length=20, choices=ConferenceScope.choices, blank=True)
    local_conf_level = models.CharField(max_length=20, choices=LocalConfLevel.choices, blank=True)

    # Conference participation (certificate-based, section IV)
    conference_name = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    event_date = models.DateField(null=True, blank=True)
    presentation_type = models.CharField(max_length=20, choices=PresentationType.choices, blank=True)
    participation_scope = models.CharField(max_length=20, choices=ParticipationScope.choices, blank=True)

    # Patent / IP
    patent_category = models.CharField(max_length=30, choices=PatentCategory.choices, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)
    issued_date = models.DateField(null=True, blank=True)

    # Other publications: publication_type drives 5.1/5.3/5.5;
    # published_abroad additionally flags 5.2/5.4 (a SUBSET, not extra count).
    publication_type = models.CharField(max_length=20, choices=PublicationType.choices, blank=True)
    published_abroad = models.BooleanField(default=False)
    isbn = models.CharField(max_length=50, blank=True)
    pages = models.PositiveIntegerField(null=True, blank=True)

    # Derived, indexed -- see specialists/report_codes.py. Empty means
    # "not yet classifiable" (missing required classification fields);
    # such records are excluded from report counts and flagged.
    report_code = models.CharField(max_length=10, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-created_at"]

    def save(self, *args, **kwargs):
        from .report_codes import compute_report_code

        self.report_code = compute_report_code(self)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"

    @property
    def report_year(self):
        """Which calendar year this record counts toward, per category."""
        if self.category == self.Category.PATENT:
            return self.issued_date.year if self.issued_date else None
        if self.category == self.Category.CONFERENCE_PARTICIPATION:
            return self.event_date.year if self.event_date else None
        return self.year

