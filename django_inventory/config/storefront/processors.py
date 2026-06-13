"""
Server-side image processing with Pillow.
Crops and resizes uploaded images to exact card dimensions.
"""
import io
import json
import logging
from pathlib import Path

from PIL import Image, ImageOps
from django.core.files.uploadedfile import InMemoryUploadedFile

logger = logging.getLogger(__name__)

# ── Dimension registry ───────────────────────────────────────────────────────
# Single source of truth: (target_width, target_height)
# Used by both the widget (aspect ratio lock) and processor (resize).

IMAGE_SPECS = {
    'hero_background_image': (1440, 600),
    'brand_logo':            (200, 80),
    'category_image':        (400, 200),
    'product_image':         (400, 300),
    'showcase_image':        (200, 200),
    'whyus_image':           (200, 200),
}

JPEG_QUALITY = 88


def process_image(uploaded_file, crop_data_json: str, target_width: int, target_height: int):
    """
    Crop and resize an uploaded image to exact target dimensions.

    Args:
        uploaded_file: Django UploadedFile (from form cleaning).
        crop_data_json: JSON string with {x, y, width, height} from Cropper.js.
                        Pass empty string or None for auto center-crop.
        target_width: Final output width in pixels.
        target_height: Final output height in pixels.

    Returns:
        InMemoryUploadedFile ready to assign to the model's ImageField.
    """
    if not uploaded_file:
        return uploaded_file

    img = Image.open(uploaded_file)

    # Fix phone EXIF orientation before anything else
    img = ImageOps.exif_transpose(img)

    # Convert RGBA → RGB for JPEG output (keep alpha for PNG)
    original_name = getattr(uploaded_file, 'name', 'image.jpg')
    ext = Path(original_name).suffix.lower()
    has_alpha = img.mode in ('RGBA', 'LA', 'PA')

    # ── Apply crop coordinates from Cropper.js ────────────────────────────
    crop_data = _parse_crop_data(crop_data_json)

    if crop_data:
        x = max(0, int(round(crop_data['x'])))
        y = max(0, int(round(crop_data['y'])))
        w = int(round(crop_data['width']))
        h = int(round(crop_data['height']))
        # Clamp to image bounds
        x2 = min(x + w, img.width)
        y2 = min(y + h, img.height)
        if x2 > x and y2 > y:
            img = img.crop((x, y, x2, y2))
    else:
        # No crop data → auto center-crop to target aspect ratio
        img = _center_crop(img, target_width, target_height)

    # ── Resize to exact target dimensions ─────────────────────────────────
    img = img.resize((target_width, target_height), Image.LANCZOS)

    # ── Save to buffer ────────────────────────────────────────────────────
    buffer = io.BytesIO()

    if ext in ('.png',) and has_alpha:
        content_type = 'image/png'
        img.save(buffer, format='PNG', optimize=True)
    elif ext in ('.webp',):
        content_type = 'image/webp'
        if img.mode == 'RGBA':
            img.save(buffer, format='WEBP', quality=JPEG_QUALITY, lossless=False)
        else:
            img = img.convert('RGB')
            img.save(buffer, format='WEBP', quality=JPEG_QUALITY)
    else:
        content_type = 'image/jpeg'
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(buffer, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        # Ensure extension matches
        if ext not in ('.jpg', '.jpeg'):
            original_name = str(Path(original_name).with_suffix('.jpg'))

    buffer.seek(0)

    return InMemoryUploadedFile(
        file=buffer,
        field_name=None,
        name=original_name,
        content_type=content_type,
        size=buffer.getbuffer().nbytes,
        charset=None,
    )


def _parse_crop_data(raw: str) -> dict | None:
    """Parse JSON crop data from widget, return dict or None."""
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if all(k in data for k in ('x', 'y', 'width', 'height')):
            if data['width'] > 0 and data['height'] > 0:
                return data
    except (json.JSONDecodeError, TypeError, KeyError):
        logger.debug("Invalid crop data: %s", raw)
    return None


def _center_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    Crop the largest possible region from the center of the image
    that matches the target aspect ratio.
    """
    target_ratio = target_w / target_h
    img_ratio = img.width / img.height

    if img_ratio > target_ratio:
        # Image is wider → crop sides
        new_w = int(img.height * target_ratio)
        offset = (img.width - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, img.height))
    elif img_ratio < target_ratio:
        # Image is taller → crop top/bottom
        new_h = int(img.width / target_ratio)
        offset = (img.height - new_h) // 2
        img = img.crop((0, offset, img.width, offset + new_h))

    return img
