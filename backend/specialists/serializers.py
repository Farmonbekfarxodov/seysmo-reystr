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
    differ per category (see CATEGORY_REQUIRED_FIELDS); the PDF file is
    required on create, optional (replace-only, never removable) on
    update. A same-employee DOI duplicate raises a soft, confirmable
    warning unless the client passes confirm_duplicate=true."""

    file = serializers.FileField(required=False)
    confirm_duplicate = serializers.BooleanField(write_only=True, required=False, default=False)
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    authorship_display = serializers.CharField(source="get_authorship_display", read_only=True)
    index_type_display = serializers.CharField(source="get_index_type_display", read_only=True)
    thesis_category_display = serializers.CharField(source="get_thesis_category_display", read_only=True)
    patent_category_display = serializers.CharField(source="get_patent_category_display", read_only=True)
    patent_type_display = serializers.CharField(source="get_patent_type_display", read_only=True)

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
            "publisher",
            "index_type",
            "index_type_display",
            "impact_factor",
            "journal_name",
            "thesis_category",
            "thesis_category_display",
            "patent_category",
            "patent_category_display",
            "patent_type",
            "patent_type_display",
            "certificate_number",
            "issued_date",
            "isbn",
            "pages",
            "created_at",
            "updated_at",
            "confirm_duplicate",
        ]
        read_only_fields = ["id", "original_filename", "size", "created_at", "updated_at"]

    CATEGORY_REQUIRED_FIELDS = {
        ScientificWork.Category.FOREIGN_ARTICLE: ["title", "doi", "year", "authorship"],
        ScientificWork.Category.LOCAL_ARTICLE: [
            "title", "journal_name", "doi", "year", "link", "authorship"
        ],
        ScientificWork.Category.THESIS: [
            "title", "journal_name", "thesis_category", "year", "authorship"
        ],
        ScientificWork.Category.PATENT: [
            "title", "patent_category", "patent_type", "certificate_number", "issued_date", "authorship"
        ],
        ScientificWork.Category.MONOGRAPH: ["title", "publisher", "year", "authorship"],
    }

    FIELD_LABELS = {
        "title": "Nomi",
        "doi": "DOI",
        "year": "Yili",
        "authorship": "Muallifligi",
        "journal_name": "Jurnal nomi",
        "link": "Havola",
        "thesis_category": "Kategoriya",
        "patent_category": "Hujjat kategoriyasi",
        "patent_type": "Hujjat turi",
        "certificate_number": "Guvohnoma raqami",
        "issued_date": "Berilgan sanasi",
        "publisher": "Nashriyot",
    }

    def _current_value(self, attrs, field):
        if field in attrs:
            return attrs[field]
        if self.instance is not None:
            return getattr(self.instance, field, None)
        return None

    def validate_file(self, value):
        validate_uploaded_document(value)
        return value

    def validate(self, attrs):
        confirm_duplicate = attrs.pop("confirm_duplicate", False)

        category = self._current_value(attrs, "category")
        required = self.CATEGORY_REQUIRED_FIELDS.get(category, [])
        errors = {}
        for field in required:
            value = self._current_value(attrs, field)
            if value in (None, ""):
                errors[field] = f"{self.FIELD_LABELS.get(field, field)} majburiy."
        if errors:
            raise serializers.ValidationError(errors)

        if self.instance is None and not attrs.get("file"):
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
        file = validated_data.pop("file")
        work = ScientificWork.objects.create(
            specialist=specialist,
            original_filename=file.name,
            size=file.size,
            file=file,
            **validated_data,
        )
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
