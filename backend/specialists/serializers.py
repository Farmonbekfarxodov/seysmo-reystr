from django.db.models import Count
from rest_framework import serializers

from .models import Department, ScientificWork, SpecialistProfile
from .validators import validate_photo, validate_uploaded_document


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "slug"]


class SpecialistCardSerializer(serializers.ModelSerializer):
    """Public search-result card. Only whitelisted public fields."""

    id = serializers.IntegerField(source="user_id", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    academic_degree = serializers.CharField(source="get_academic_degree_display", read_only=True)
    academic_title = serializers.CharField(source="get_academic_title_display", read_only=True)
    position = serializers.CharField(source="get_position_display", read_only=True)
    department = serializers.CharField(source="department.name", read_only=True)
    photo_thumbnail = serializers.ImageField(read_only=True)
    # Populated via .annotate(works_count=Count("works")) in the view.
    works_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = SpecialistProfile
        fields = [
            "id",
            "full_name",
            "academic_degree",
            "academic_title",
            "position",
            "department",
            "photo_thumbnail",
            "works_count",
        ]


class SpecialistDetailSerializer(serializers.ModelSerializer):
    """Public profile detail. Never includes email or username."""

    id = serializers.IntegerField(source="user_id", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    academic_degree = serializers.CharField(source="get_academic_degree_display", read_only=True)
    academic_title = serializers.CharField(source="get_academic_title_display", read_only=True)
    position = serializers.CharField(source="get_position_display", read_only=True)
    department = serializers.CharField(source="department.name", read_only=True)
    photo = serializers.ImageField(read_only=True)
    photo_thumbnail = serializers.ImageField(read_only=True)
    works_by_category = serializers.SerializerMethodField()
    works_count = serializers.SerializerMethodField()

    class Meta:
        model = SpecialistProfile
        fields = [
            "id",
            "full_name",
            "academic_degree",
            "academic_title",
            "position",
            "department",
            "research_interests",
            "bio",
            "photo",
            "photo_thumbnail",
            "works_count",
            "works_by_category",
        ]

    def get_works_by_category(self, obj):
        counts = dict.fromkeys(ScientificWork.Category.values, 0)
        for row in obj.works.values("category").annotate(count=Count("id")):
            counts[row["category"]] = row["count"]
        return counts

    def get_works_count(self, obj):
        return obj.works.count()


class MySpecialistProfileSerializer(serializers.ModelSerializer):
    """Read/write serializer for an employee editing their own profile,
    including photo upload/replace/remove. Scientific works are managed
    through their own endpoints, not nested here."""

    full_name = serializers.CharField(source="user.full_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    last_name = serializers.CharField(source="user.last_name")
    first_name = serializers.CharField(source="user.first_name")
    patronymic = serializers.CharField(source="user.patronymic", required=False, allow_blank=True)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())
    department_name = serializers.CharField(source="department.name", read_only=True)
    photo = serializers.ImageField(required=False, allow_null=True)
    remove_photo = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = SpecialistProfile
        fields = [
            "id",
            "full_name",
            "email",
            "username",
            "last_name",
            "first_name",
            "patronymic",
            "photo",
            "photo_thumbnail",
            "remove_photo",
            "academic_degree",
            "academic_title",
            "position",
            "department",
            "department_name",
            "research_interests",
            "bio",
        ]
        read_only_fields = ["id", "photo_thumbnail"]

    def validate_photo(self, value):
        if value is not None:
            validate_photo(value)
        return value

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        user = instance.user
        for field in ("last_name", "first_name", "patronymic"):
            if field in user_data:
                setattr(user, field, user_data[field])
        user.save()

        remove_photo = validated_data.pop("remove_photo", False)
        new_photo = validated_data.pop("photo", None)

        for field in ("academic_degree", "academic_title", "position", "department", "research_interests", "bio"):
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        if remove_photo:
            if instance.photo:
                instance.photo.storage.delete(instance.photo.name)
            instance.photo = None
        elif new_photo is not None:
            instance.photo = new_photo

        instance.save()
        return instance


class ScientificWorkSerializer(serializers.ModelSerializer):
    """Read/write serializer for a single scientific work. Required fields
    differ per category (see CATEGORY_REQUIRED_FIELDS, plus the
    conditional rules in validate() for the article quartile fields and
    the thesis local-conference level). The PDF file is required on
    create for every category EXCEPT conference_participation, and is
    always replace-only (never removable) on update. A same-employee DOI
    duplicate raises a soft, confirmable warning unless the client passes
    confirm_duplicate=true."""

    file = serializers.FileField(required=False, allow_null=True)
    confirm_duplicate = serializers.BooleanField(write_only=True, required=False, default=False)
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    authorship_display = serializers.CharField(source="get_authorship_display", read_only=True)
    journal_scope_display = serializers.CharField(source="get_journal_scope_display", read_only=True)
    indexed_in_display = serializers.CharField(source="get_indexed_in_display", read_only=True)
    conference_scope_display = serializers.CharField(source="get_conference_scope_display", read_only=True)
    local_conf_level_display = serializers.CharField(source="get_local_conf_level_display", read_only=True)
    presentation_type_display = serializers.CharField(source="get_presentation_type_display", read_only=True)
    participation_scope_display = serializers.CharField(source="get_participation_scope_display", read_only=True)
    publication_type_display = serializers.CharField(source="get_publication_type_display", read_only=True)
    patent_category_display = serializers.CharField(source="get_patent_category_display", read_only=True)

    class Meta:
        model = ScientificWork
        fields = [
            "id",
            "category",
            "category_display",
            "title",
            "year",
            "authorship",
            "authorship_display",
            "project_name",
            "link",
            "doi",
            "file",
            "original_filename",
            "size",
            # Articles
            "journal_scope",
            "journal_scope_display",
            "indexed_in",
            "indexed_in_display",
            "scopus_quartile",
            "wos_quartile",
            "publisher",
            "impact_factor",
            "journal_name",
            # Thesis
            "conference_scope",
            "conference_scope_display",
            "local_conf_level",
            "local_conf_level_display",
            # Conference participation
            "conference_name",
            "location",
            "event_date",
            "presentation_type",
            "presentation_type_display",
            "participation_scope",
            "participation_scope_display",
            # Patent / IP
            "patent_category",
            "patent_category_display",
            "certificate_number",
            "issued_date",
            # Other publications
            "publication_type",
            "publication_type_display",
            "published_abroad",
            "isbn",
            "pages",
            # Derived / meta
            "report_code",
            "created_at",
            "updated_at",
            "confirm_duplicate",
        ]
        read_only_fields = ["id", "original_filename", "size", "report_code", "created_at", "updated_at"]

    CATEGORY_REQUIRED_FIELDS = {
        ScientificWork.Category.FOREIGN_ARTICLE: ["title", "doi", "year", "authorship", "journal_scope"],
        ScientificWork.Category.LOCAL_ARTICLE: ["title", "journal_name", "doi", "year", "link", "authorship"],
        ScientificWork.Category.THESIS: ["title", "journal_name", "year", "authorship", "conference_scope"],
        ScientificWork.Category.CONFERENCE_PARTICIPATION: [
            "title", "conference_name", "location", "event_date",
            "presentation_type", "participation_scope", "authorship",
        ],
        ScientificWork.Category.PATENT: [
            "title", "patent_category", "certificate_number", "issued_date", "authorship"
        ],
        ScientificWork.Category.OTHER_PUBLICATION: [
            "title", "publisher", "year", "authorship", "publication_type"
        ],
    }

    FIELD_LABELS = {
        "title": "Nomi",
        "doi": "DOI",
        "year": "Yili",
        "authorship": "Muallifligi",
        "journal_name": "Jurnal nomi",
        "link": "Havola",
        "journal_scope": "Jurnal turi",
        "indexed_in": "Indekslangan baza",
        "scopus_quartile": "Scopus kvartili",
        "wos_quartile": "Web of Science kvartili",
        "conference_scope": "Anjuman turi",
        "local_conf_level": "Anjuman darajasi",
        "conference_name": "Anjuman nomi",
        "location": "Joyi",
        "event_date": "Sana",
        "presentation_type": "Ma'ruza turi",
        "participation_scope": "Qamrovi",
        "patent_category": "Hujjat kategoriyasi",
        "certificate_number": "Guvohnoma raqami",
        "issued_date": "Berilgan sanasi",
        "publisher": "Nashriyot",
        "publication_type": "Nashr turi",
    }

    def _current_value(self, attrs, field):
        if field in attrs:
            return attrs[field]
        if self.instance is not None:
            return getattr(self.instance, field, None)
        return None

    def validate_file(self, value):
        if value is not None:
            validate_uploaded_document(value)
        return value

    def validate(self, attrs):
        confirm_duplicate = attrs.pop("confirm_duplicate", False)

        category = self._current_value(attrs, "category")

        # local_article's journal_scope is always "local" -- not a user
        # choice, enforced server-side regardless of what was submitted.
        if category == ScientificWork.Category.LOCAL_ARTICLE:
            attrs["journal_scope"] = ScientificWork.JournalScope.LOCAL

        required = list(self.CATEGORY_REQUIRED_FIELDS.get(category, []))
        errors = {}

        # Conditional requirements layered on top of the static list.
        if category in (ScientificWork.Category.FOREIGN_ARTICLE, ScientificWork.Category.LOCAL_ARTICLE):
            journal_scope = self._current_value(attrs, "journal_scope")
            if journal_scope == ScientificWork.JournalScope.SCOPUS_WOS:
                indexed_in = self._current_value(attrs, "indexed_in")
                if not indexed_in:
                    errors["indexed_in"] = f"{self.FIELD_LABELS['indexed_in']} majburiy."
                else:
                    if indexed_in in ("scopus", "both") and not self._current_value(attrs, "scopus_quartile"):
                        errors["scopus_quartile"] = "Scopus kvartili majburiy."
                    if indexed_in in ("wos", "both") and not self._current_value(attrs, "wos_quartile"):
                        errors["wos_quartile"] = "Web of Science kvartili majburiy."

        if category == ScientificWork.Category.THESIS:
            conference_scope = self._current_value(attrs, "conference_scope")
            if conference_scope == ScientificWork.ConferenceScope.LOCAL:
                if not self._current_value(attrs, "local_conf_level"):
                    errors["local_conf_level"] = f"{self.FIELD_LABELS['local_conf_level']} majburiy."

        for field in required:
            value = self._current_value(attrs, field)
            if value in (None, ""):
                errors[field] = f"{self.FIELD_LABELS.get(field, field)} majburiy."
        if errors:
            raise serializers.ValidationError(errors)

        # PDF required on create for every category EXCEPT conference
        # participation (certificate may arrive later).
        if (
            self.instance is None
            and category != ScientificWork.Category.CONFERENCE_PARTICIPATION
            and not attrs.get("file")
        ):
            raise serializers.ValidationError({"file": "PDF fayl yuklash majburiy."})

        doi = self._current_value(attrs, "doi")
        if doi:
            specialist = self.context["specialist"]
            qs = ScientificWork.objects.filter(specialist=specialist, doi=doi)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists() and not confirm_duplicate:
                raise serializers.ValidationError({
                    "doi": ["duplicate"],
                    "detail": "Bu DOI bilan yozuv allaqachon mavjud. Baribir saqlaysizmi?",
                    "code": "duplicate_doi",
                })

        return attrs

    def create(self, validated_data):
        specialist = self.context["specialist"]
        file = validated_data.pop("file", None)
        if file is not None:
            validated_data["original_filename"] = file.name
            validated_data["size"] = file.size
            validated_data["file"] = file
        work = ScientificWork.objects.create(specialist=specialist, **validated_data)
        self._sync_year_from_issued_date(work)
        return work

    def update(self, instance, validated_data):
        file = validated_data.pop("file", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if file is not None:
            if instance.file:
                instance.file.storage.delete(instance.file.name)
            instance.file = file
            instance.original_filename = file.name
            instance.size = file.size
        instance.save()
        self._sync_year_from_issued_date(instance)
        return instance

    @staticmethod
    def _sync_year_from_issued_date(work):
        """Patents key on issued_date (a full date); keep the common `year`
        field in sync with it so cross-category year sorting still works."""
        if work.category == ScientificWork.Category.PATENT and work.issued_date:
            if work.year != work.issued_date.year:
                ScientificWork.objects.filter(pk=work.pk).update(year=work.issued_date.year)
                work.year = work.issued_date.year
