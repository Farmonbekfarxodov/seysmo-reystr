from rest_framework import serializers

from .models import Department, SpecialistDocument, SpecialistProfile
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
        ]


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialistDocument
        fields = ["id", "original_filename", "size", "uploaded_at", "file"]
        read_only_fields = ["id", "size", "uploaded_at"]


class SpecialistDetailSerializer(serializers.ModelSerializer):
    """Public profile detail. Never includes email or username. Documents
    ARE included here -- they're the researcher's published articles, which
    is the whole point of the registry for this institute."""

    id = serializers.IntegerField(source="user_id", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    academic_degree = serializers.CharField(source="get_academic_degree_display", read_only=True)
    academic_title = serializers.CharField(source="get_academic_title_display", read_only=True)
    position = serializers.CharField(source="get_position_display", read_only=True)
    department = serializers.CharField(source="department.name", read_only=True)
    photo = serializers.ImageField(read_only=True)
    photo_thumbnail = serializers.ImageField(read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)

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
            "documents",
        ]


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        validate_uploaded_document(value)
        return value


class MySpecialistProfileSerializer(serializers.ModelSerializer):
    """Read/write serializer for an employee editing their own profile,
    including photo upload/replace/remove. No moderation or visibility
    toggle -- every verified account's profile is public."""

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
    documents = DocumentSerializer(many=True, read_only=True)

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
            "documents",
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
