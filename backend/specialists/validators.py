import os

from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image

try:
    import magic  # python-magic, optional; best-effort magic-byte sniffing
except ImportError:  # pragma: no cover
    magic = None


def validate_uploaded_document(f):
    """Server-side validation of a credential document: extension,
    declared content-type, and size — independent of client-side checks."""

    ext = os.path.splitext(f.name)[1].lower().lstrip(".")
    if ext not in settings.ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError(
            f"Noto'g'ri fayl turi '.{ext}'. Ruxsat etilgan: "
            f"{', '.join(settings.ALLOWED_DOCUMENT_EXTENSIONS)}."
        )

    max_bytes = settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
    if f.size > max_bytes:
        raise ValidationError(
            f"'{f.name}' fayli juda katta. Maksimal hajm: {settings.MAX_DOCUMENT_SIZE_MB} MB."
        )

    content_type = getattr(f, "content_type", None)
    if content_type and content_type not in settings.ALLOWED_DOCUMENT_MIME_TYPES:
        raise ValidationError(f"'{f.name}' fayli uchun ruxsat etilmagan content-type.")

    if magic is not None:
        head = f.read(2048)
        f.seek(0)
        detected = magic.from_buffer(head, mime=True)
        if detected not in settings.ALLOWED_DOCUMENT_MIME_TYPES:
            raise ValidationError(f"'{f.name}' fayli haqiqiy hujjat faylga o'xshamaydi.")


def validate_photo(f):
    """Server-side validation of a profile photo: extension, size, and a
    genuine Pillow-based verification that the bytes are a real image."""

    ext = os.path.splitext(f.name)[1].lower().lstrip(".")
    if ext not in settings.ALLOWED_PHOTO_EXTENSIONS:
        raise ValidationError(
            f"Noto'g'ri fayl turi '.{ext}'. Ruxsat etilgan: "
            f"{', '.join(settings.ALLOWED_PHOTO_EXTENSIONS)}."
        )

    max_bytes = settings.MAX_PHOTO_SIZE_MB * 1024 * 1024
    if f.size > max_bytes:
        raise ValidationError(
            f"Rasm juda katta. Maksimal hajm: {settings.MAX_PHOTO_SIZE_MB} MB."
        )

    content_type = getattr(f, "content_type", None)
    if content_type and content_type not in settings.ALLOWED_PHOTO_MIME_TYPES:
        raise ValidationError("Ruxsat etilmagan rasm content-type.")

    try:
        f.seek(0)
        img = Image.open(f)
        img.verify()
    except Exception as exc:  # noqa: BLE001 - any failure means "not a real image"
        raise ValidationError("Fayl haqiqiy rasm emas yoki buzilgan.") from exc
    finally:
        f.seek(0)
