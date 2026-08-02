import os
from pathlib import Path
import warnings

from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from PIL import Image, UnidentifiedImageError


class SecureFileSystemStorage(FileSystemStorage):
    def get_valid_name(self, name):
        return os.path.basename(name)


MAX_IMAGE_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
ALLOWED_IMAGE_EXTENSIONS = frozenset({"jpg", "jpeg", "png", "webp", "heic", "heif"})
ALLOWED_IMAGE_EXTENSIONS_DOTTED = frozenset(f".{extension}" for extension in ALLOWED_IMAGE_EXTENSIONS)
IMAGE_EXTENSION_LABEL = "jpg, jpeg, png, webp, heic, heif"

_JPEG_EXTENSIONS = {"jpg", "jpeg"}
_HEIF_EXTENSIONS = {"heic", "heif"}
_HEIF_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"heif", b"mif1", b"msf1"}
_CONTENT_TYPES = {
    "jpeg": {"image/jpeg", "image/pjpeg"},
    "png": {"image/png", "image/x-png"},
    "webp": {"image/webp"},
    "heif": {"image/heic", "image/heif", "image/heic-sequence", "image/heif-sequence"},
}


def image_file_extension(upload):
    return Path(str(getattr(upload, "name", ""))).suffix.lower().lstrip(".")


def is_allowed_image_extension(extension):
    return extension.lower().lstrip(".") in ALLOWED_IMAGE_EXTENSIONS


def validate_image_upload(
    upload,
    *,
    field_label="Image",
    max_bytes=MAX_IMAGE_UPLOAD_BYTES,
    max_size_label=None,
):
    if upload is None:
        raise ValidationError(f"{field_label} is required.")

    size = getattr(upload, "size", 0) or 0
    if size <= 0:
        raise ValidationError(f"{field_label} cannot be empty.")
    if max_bytes and size > max_bytes:
        raise ValidationError(
            f"{field_label} must be {max_size_label or _format_size(max_bytes)} or smaller."
        )

    extension = image_file_extension(upload)
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(f"Allowed image types: {IMAGE_EXTENSION_LABEL}.")

    header = _read_header(upload)
    detected_type = _detect_image_type(header)
    expected_type = _expected_type_for_extension(extension)
    if not detected_type:
        raise ValidationError(f"{field_label} must be a valid image file.")
    if detected_type != expected_type:
        raise ValidationError(f"{field_label} extension does not match the uploaded file content.")

    content_type = str(getattr(upload, "content_type", "") or "").split(";", 1)[0].lower()
    if content_type and content_type != "application/octet-stream":
        allowed_content_types = _CONTENT_TYPES.get(detected_type, set())
        if content_type not in allowed_content_types:
            raise ValidationError(f"{field_label} content type is not allowed.")

    if detected_type in {"jpeg", "png", "webp"}:
        _verify_with_pillow(upload, field_label)

    _rewind(upload)
    return upload


def image_upload_error(upload, **kwargs):
    try:
        validate_image_upload(upload, **kwargs)
    except ValidationError as error:
        return " ".join(error.messages)
    return ""


def _expected_type_for_extension(extension):
    if extension in _JPEG_EXTENSIONS:
        return "jpeg"
    if extension in _HEIF_EXTENSIONS:
        return "heif"
    return extension


def _detect_image_type(header):
    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp"
    if len(header) >= 12 and header[4:8] == b"ftyp" and header[8:12].lower() in _HEIF_BRANDS:
        return "heif"
    return ""


def _read_header(upload, size=32):
    position = _position(upload)
    try:
        upload.seek(0)
        return upload.read(size)
    finally:
        _seek(upload, position)


def _verify_with_pillow(upload, field_label):
    position = _position(upload)
    previous_max_pixels = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = min(
        value for value in (previous_max_pixels, MAX_IMAGE_PIXELS) if value
    )
    try:
        upload.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(upload) as image:
                image.verify()
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as error:
        raise ValidationError(f"{field_label} must be a valid image file.") from error
    finally:
        Image.MAX_IMAGE_PIXELS = previous_max_pixels
        _seek(upload, position)


def _format_size(size):
    if size % (1024 * 1024) == 0:
        return f"{size // (1024 * 1024)} MB"
    if size % 1024 == 0:
        return f"{size // 1024} KB"
    return f"{size} bytes"


def _position(upload):
    try:
        return upload.tell()
    except (AttributeError, OSError):
        return 0


def _seek(upload, position):
    try:
        upload.seek(position)
    except (AttributeError, OSError):
        return None
    return None


def _rewind(upload):
    _seek(upload, 0)
