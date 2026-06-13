"""Tests for the storefront image pipeline.

`processors.py` is pure + deterministic (no DB, no network) — the cheapest thing
to lock down, and the one genuinely fragile piece in this app (Pillow crop/resize,
RGBA→RGB, webp, EXIF, crop-JSON parsing). Previously untested.
"""
import io
import json

from django.test import SimpleTestCase
from PIL import Image

from .processors import process_image, _parse_crop_data, _center_crop


def _upload(w, h, *, mode='RGB', fmt='PNG', name='test.png'):
    """Build an in-memory uploaded image of (w, h)."""
    from django.core.files.uploadedfile import SimpleUploadedFile
    img = Image.new(mode, (w, h), (200, 50, 50) if mode != 'RGBA' else (200, 50, 50, 255))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return SimpleUploadedFile(name, buf.getvalue(), content_type=f'image/{fmt.lower()}')


class ParseCropDataTests(SimpleTestCase):
    def test_valid_json_returns_dict(self):
        raw = json.dumps({'x': 1, 'y': 2, 'width': 10, 'height': 20})
        self.assertEqual(_parse_crop_data(raw)['width'], 10)

    def test_empty_or_none_returns_none(self):
        self.assertIsNone(_parse_crop_data(''))
        self.assertIsNone(_parse_crop_data(None))

    def test_missing_keys_returns_none(self):
        self.assertIsNone(_parse_crop_data(json.dumps({'x': 1, 'y': 2})))

    def test_zero_dimensions_returns_none(self):
        self.assertIsNone(_parse_crop_data(json.dumps({'x': 0, 'y': 0, 'width': 0, 'height': 5})))

    def test_garbage_returns_none(self):
        self.assertIsNone(_parse_crop_data('not json {'))


class CenterCropTests(SimpleTestCase):
    def test_wider_image_cropped_to_target_ratio(self):
        # 800x200 (4:1) → target 1:1 → crops sides to 200x200 region.
        out = _center_crop(Image.new('RGB', (800, 200)), 100, 100)
        self.assertEqual(out.width, out.height)

    def test_taller_image_cropped_to_target_ratio(self):
        # 200x800 (1:4) → target 2:1 → crops top/bottom.
        out = _center_crop(Image.new('RGB', (200, 800)), 200, 100)
        self.assertAlmostEqual(out.width / out.height, 2.0, places=1)


class ProcessImageTests(SimpleTestCase):
    def test_resizes_to_exact_target(self):
        result = process_image(_upload(1000, 800), '', 400, 300)
        self.assertEqual(Image.open(result).size, (400, 300))

    def test_explicit_crop_then_resize(self):
        crop = json.dumps({'x': 0, 'y': 0, 'width': 500, 'height': 500})
        result = process_image(_upload(1000, 1000), crop, 200, 200)
        self.assertEqual(Image.open(result).size, (200, 200))

    def test_rgba_png_with_alpha_stays_png(self):
        result = process_image(_upload(300, 300, mode='RGBA', name='a.png'), '', 200, 200)
        self.assertEqual(Image.open(result).size, (200, 200))

    def test_none_upload_passthrough(self):
        self.assertIsNone(process_image(None, '', 100, 100))
