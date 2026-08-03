"""capture_service — single writer for CaptureAsset (Block 3A; ADR-G/E, I-1).

Why this service exists: originals are permanent knowledge; the ONLY door for
a file to become knowledge is store_capture(), which validates content by
MAGIC BYTES (never trusting client type or extension), enforces size caps,
streams a SHA-256, dedups per product, and names storage by content hash —
path traversal is structurally impossible. No image processing here; PIL
appears only for renditions (thumbnails) and — since P2, per ADR-D3 — for
EXIF *metadata reading* (`extract_exif_metadata`), which is provenance
bookkeeping, never measurement math and never CV.

INVARIANTS:
  * file/sha256/size/content_type/product/kind/source immutable after create
    (model save() guard backs the service).
  * duplicate CONTENT for the same product is refused with the existing
    asset named (DB UniqueConstraint backs it).
  * corrections = retire(reason) + upload anew; rows/files never deleted (F5).
"""
import hashlib
import logging
import posixpath

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from accounts.services import MANAGEMENT_ROLES, user_has_role

from patterns_ai.models import CaptureAsset

logger = logging.getLogger(__name__)

# App-local caps; deploy may override via settings without code change.
MAX_UPLOAD_BYTES = getattr(settings, 'PATTERNS_AI_MAX_UPLOAD_BYTES', 15 * 1024 * 1024)
MIN_UPLOAD_BYTES = 1024

# Magic-byte signatures — content-type is VERIFIED, never trusted.
_SIGNATURES = (
    ('image/jpeg', (b'\xff\xd8\xff',), 0),
    ('image/png', (b'\x89PNG\r\n\x1a\n',), 0),
    ('image/webp', (b'WEBP',), 8),   # RIFF....WEBP
)
ALLOWED_TYPES = tuple(t for t, _, _ in _SIGNATURES)


def _ensure_management(user):
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied('Only management may store capture assets.')


def _sniff_content_type(head: bytes):
    for ctype, sigs, offset in _SIGNATURES:
        for sig in sigs:
            if head[offset:offset + len(sig)] == sig:
                if ctype == 'image/webp' and not head.startswith(b'RIFF'):
                    continue
                return ctype
    return None


def _sanitize_display_name(name: str) -> str:
    """Display-only sanitation. Storage names come from the hash — the client
    name is never used for paths, so traversal is neutralized here purely for
    honest display."""
    base = posixpath.basename((name or '').replace('\\', '/'))
    base = base.replace('..', '.').strip().lstrip('.')
    return base[:200] or 'upload'


@transaction.atomic
def store_capture(*, user, product, uploaded_file, source, kind=None,
                  mat=None, metadata=None):
    """THE door: validate → hash → dedup → persist an immutable original.

    Purpose: every capture (camera or gallery) becomes knowledge through one
    audited path. Invariants: module docstring. Returns the CaptureAsset.
    """
    _ensure_management(user)
    source = CaptureAsset.Source(source)
    kind = CaptureAsset.Kind(kind or CaptureAsset.Kind.MARKER_PHOTO)

    size = getattr(uploaded_file, 'size', None)
    if size is None:
        raise ValidationError('Upload has no size — refused.')
    if size < MIN_UPLOAD_BYTES:
        raise ValidationError('File too small to be a real capture (min 1 KB).')
    if size > MAX_UPLOAD_BYTES:
        raise ValidationError(
            f'File too large ({size} bytes; max {MAX_UPLOAD_BYTES}).')

    uploaded_file.seek(0)
    head = uploaded_file.read(16)
    sniffed = _sniff_content_type(head)
    if sniffed is None:
        raise ValidationError(
            'Unsupported or disguised file type — only real JPEG/PNG/WEBP '
            'images are accepted (content is checked, not the filename).')

    sha = hashlib.sha256()
    uploaded_file.seek(0)
    for chunk in iter(lambda: uploaded_file.read(1024 * 1024), b''):
        sha.update(chunk)
    digest = sha.hexdigest()

    existing = CaptureAsset.objects.filter(product=product, sha256=digest).first()
    if existing is not None:
        raise ValidationError(
            f'This exact file already exists for this product '
            f'(asset #{existing.pk}, {existing.get_status_display()}).')

    asset = CaptureAsset(
        product=product, kind=kind, source=source,
        original_filename=_sanitize_display_name(
            getattr(uploaded_file, 'name', '')),
        content_type=sniffed, size_bytes=size, sha256=digest,
        mat=mat, metadata={'schema_version': 1, **(metadata or {})},
        uploaded_by=user)
    uploaded_file.seek(0)
    asset.file.save(f'{digest[:16]}.{asset.safe_extension()}',
                    uploaded_file, save=False)
    asset.save()
    logger.info('capture.store asset=%s product=%s sha=%s by=%s',
                asset.pk, product.pk, digest[:12], user.pk)
    return asset


@transaction.atomic
def retire_capture(*, user, asset, reason):
    """Retire (never delete) an asset — the only correction path (F5)."""
    _ensure_management(user)
    if not (reason or '').strip():
        raise ValidationError('Retiring requires a reason (F2).')
    if asset.status == CaptureAsset.Status.RETIRED:
        raise ValidationError('Asset is already retired.')
    asset.status = CaptureAsset.Status.RETIRED
    asset.status_reason = reason.strip()
    asset.save(update_fields=['status', 'status_reason', 'updated_at'])
    logger.info('capture.retire asset=%s by=%s reason=%r', asset.pk, user.pk, reason)
    return asset


@transaction.atomic
def mark_corrupt(*, asset, detail):
    """Integrity-sweep writer (system actor): flag a failed verification.
    File and row stay — a corrupt original is still evidence (F5)."""
    asset.status = CaptureAsset.Status.CORRUPT
    asset.status_reason = detail[:200]
    asset.save(update_fields=['status', 'status_reason', 'updated_at'])
    logger.warning('capture.corrupt asset=%s detail=%s', asset.pk, detail)
    return asset


def verify_asset(asset):
    """Recompute the stored file's SHA-256 and compare (read-only helper;
    the sweep command decides what to do with the answer)."""
    try:
        with asset.file.open('rb') as fh:
            sha = hashlib.sha256()
            for chunk in iter(lambda: fh.read(1024 * 1024), b''):
                sha.update(chunk)
    except FileNotFoundError:
        return ('missing', 'file not found on storage')
    digest = sha.hexdigest()
    if digest != asset.sha256:
        return ('mismatch', f'sha mismatch: stored {asset.sha256[:12]} vs disk {digest[:12]}')
    return ('ok', '')


# ── renditions (ADR-G DERIVED class — regenerable, never knowledge) ─────────

THUMB_SIZE = 320


def thumbnail_path(asset, size=THUMB_SIZE) -> str:
    """Derived-class path: media/patterns_ai/<product>/derived/<sha16>_t320.jpg
    — separate subtree so retention/backup policy stays a path rule."""
    return posixpath.join('patterns_ai', str(asset.product_id), 'derived',
                          f'{asset.sha256[:16]}_t{size}.jpg')


def get_or_create_thumbnail(asset, size=THUMB_SIZE):
    """Return the storage path of a SAFE rendition (never the original).

    Lazily generated with PIL (plain resize — this is a rendition, not CV);
    regenerable at any time from the immutable original; deleting it is always
    safe (derived class). Returns None when the original is unreadable —
    callers show a placeholder, never the original.
    """
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage
    import io

    path = thumbnail_path(asset, size)
    if default_storage.exists(path):
        return path
    try:
        from PIL import Image
        with asset.file.open('rb') as fh:
            img = Image.open(fh)
            img = img.convert('RGB')
            img.thumbnail((size, size))
            buf = io.BytesIO()
            img.save(buf, 'JPEG', quality=70)
    except Exception as exc:                       # unreadable original
        logger.warning('capture.thumb_failed asset=%s err=%s', asset.pk, exc)
        return None
    default_storage.save(path, ContentFile(buf.getvalue()))
    logger.info('capture.thumb_built asset=%s path=%s', asset.pk, path)
    return path


# ── provenance (ADR-D3 §1 — metadata reading, never measurement) ────────────

_EXIF_SUBSET = {271: 'camera_make', 272: 'camera_model', 305: 'software',
                306: 'datetime', 274: 'orientation'}


def extract_exif_metadata(uploaded_file):
    """Read the fixed ADR-D3 EXIF subset from an upload (best-effort;
    absence is fine — EXIF is evidence, never authority and never math).
    Returns a dict ready to merge into CaptureAsset.metadata."""
    out = {}
    try:
        from PIL import Image
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        exif = img.getexif()
        for tag, key in _EXIF_SUBSET.items():
            if tag in exif:
                out[key] = str(exif[tag])[:100]
        out['pixel_size'] = list(img.size)
    except Exception:                                  # noqa: BLE001 - best effort
        pass
    finally:
        uploaded_file.seek(0)
    return {'exif': out} if out else {}
