from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from specialists.models import Department, SpecialistProfile
from specialists.validators import validate_photo

from .models import EmailVerificationCode
from .utils import EmailCodeRateLimited, issue_verification_code, latest_verification_for

User = get_user_model()

ACADEMIC_DEGREE_CHOICES = SpecialistProfile.AcademicDegree.values
ACADEMIC_TITLE_CHOICES = SpecialistProfile.AcademicTitle.values
POSITION_CHOICES = SpecialistProfile.Position.values


class RegisterSerializer(serializers.ModelSerializer):
    """Creates the (inactive) User + SpecialistProfile + photo in one
    multipart request, then emails the verification code. Documents/articles
    are NOT accepted here -- they can only be uploaded from the dashboard
    after the account exists (see specialists.views.MyDocumentsView)."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    academic_degree = serializers.ChoiceField(choices=ACADEMIC_DEGREE_CHOICES, required=False)
    academic_title = serializers.ChoiceField(choices=ACADEMIC_TITLE_CHOICES, required=False)
    position = serializers.ChoiceField(choices=POSITION_CHOICES, required=False, allow_blank=True)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())
    research_interests = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    photo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            "id",
            "last_name",
            "first_name",
            "patronymic",
            "email",
            "username",
            "password",
            "password_confirm",
            "photo",
            "academic_degree",
            "academic_title",
            "position",
            "department",
            "research_interests",
        ]

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Bu foydalanuvchi nomi band.")
        return value

    def validate_email(self, value):
        from django.conf import settings

        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Bu email allaqachon ro'yxatdan o'tgan.")

        allowed_domain = (settings.ALLOWED_EMAIL_DOMAIN or "").strip().lower()
        if allowed_domain and not value.endswith("@" + allowed_domain):
            raise serializers.ValidationError(
                f"Ro'yxatdan o'tish faqat @{allowed_domain} domenidagi elektron pochta uchun ochiq."
            )
        return value

    def validate_photo(self, value):
        if value is not None:
            validate_photo(value)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Parollar mos kelmadi."})
        try:
            validate_password(attrs["password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        photo = validated_data.pop("photo", None)
        academic_degree = validated_data.pop("academic_degree", SpecialistProfile.AcademicDegree.NONE)
        academic_title = validated_data.pop("academic_title", SpecialistProfile.AcademicTitle.NONE)
        position = validated_data.pop("position", "")
        department = validated_data.pop("department")
        research_interests = validated_data.pop("research_interests", "")
        password = validated_data.pop("password")

        user = User(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            patronymic=validated_data.get("patronymic", ""),
            is_active=False,
            is_email_verified=False,
        )
        user.set_password(password)
        user.save()

        SpecialistProfile.objects.create(
            user=user,
            photo=photo,
            academic_degree=academic_degree,
            academic_title=academic_title,
            position=position,
            department=department,
            research_interests=research_interests,
        )

        issue_verification_code(user)
        return user


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs):
        email = attrs["email"].lower().strip()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Email yoki kod noto'g'ri.")

        if user.is_email_verified:
            raise serializers.ValidationError("Bu hisob allaqachon tasdiqlangan.")

        verification = latest_verification_for(user)
        if verification is None or verification.is_used:
            raise serializers.ValidationError("Tasdiqlash kodi topilmadi. Yangi kod so'rang.")
        if verification.is_locked:
            raise serializers.ValidationError("Urinishlar soni tugadi. Yangi kod so'rang.")
        if verification.is_expired:
            raise serializers.ValidationError("Kodning muddati tugagan. Yangi kod so'rang.")

        if not verification.check_code(attrs["code"]):
            verification.attempts_used += 1
            verification.save(update_fields=["attempts_used"])
            remaining = 5 - verification.attempts_used
            raise serializers.ValidationError(
                f"Kod noto'g'ri. Qolgan urinishlar: {max(remaining, 0)}."
            )

        attrs["user"] = user
        attrs["verification"] = verification
        return attrs

    def save(self):
        user = self.validated_data["user"]
        verification = self.validated_data["verification"]
        verification.is_used = True
        verification.save(update_fields=["is_used"])
        user.is_active = True
        user.is_email_verified = True
        user.save(update_fields=["is_active", "is_email_verified"])
        return user


class ResendCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        value = value.lower().strip()
        self.user = User.objects.filter(email__iexact=value).first()
        if self.user is None:
            return value
        if self.user.is_email_verified:
            raise serializers.ValidationError("Bu hisob allaqachon tasdiqlangan.")

        last = latest_verification_for(self.user)
        if last is not None:
            from django.conf import settings

            cooldown = settings.EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS
            elapsed = (timezone.now() - last.created_at).total_seconds()
            if elapsed < cooldown:
                wait = int(cooldown - elapsed)
                raise serializers.ValidationError(
                    f"Yangi kod so'rashdan oldin {wait} soniya kuting."
                )
        return value

    def save(self):
        if self.user is not None:
            try:
                issue_verification_code(self.user)
            except EmailCodeRateLimited as exc:
                raise serializers.ValidationError({"email": [str(exc)]})


class MeSerializer(serializers.ModelSerializer):
    """GET /api/me/ -- basic account info."""

    full_name = serializers.CharField(read_only=True)
    has_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "patronymic",
            "full_name",
            "is_email_verified",
            "has_profile",
        ]

    def get_has_profile(self, obj):
        return hasattr(obj, "specialist_profile")


class LoginTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Accepts a single `login` field (username OR email). Only blocks on
    unverified email -- there's no approval step, so a verified account can
    always log in."""

    default_error_messages = {"no_active_account": "Login yoki parol noto'g'ri."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["login"] = serializers.CharField()
        self.fields.pop(self.username_field, None)

    def validate(self, attrs):
        login_value = attrs.pop("login", "").strip()
        user_obj = User.objects.filter(
            Q(username__iexact=login_value) | Q(email__iexact=login_value)
        ).first()

        if user_obj is None:
            raise serializers.ValidationError({"detail": "Login yoki parol noto'g'ri."})

        if not user_obj.is_email_verified or not user_obj.is_active:
            raise serializers.ValidationError(
                {"detail": "Email tasdiqlanmagan. Kodni tasdiqlang.", "code": "unverified_email"}
            )

        attrs[self.username_field] = user_obj.get_username()
        data = super().validate(attrs)
        data["user"] = MeSerializer(self.user).data
        return data
