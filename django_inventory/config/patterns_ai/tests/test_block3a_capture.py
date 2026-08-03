"""Block-3A tests — capture foundation: upload security, integrity,
immutability, single-writer discipline. Uses an isolated MEDIA_ROOT.
"""
import hashlib
import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings

from accounts.models import Role
from production.models import Product
from patterns_ai.models import CaptureAsset
from patterns_ai.services import capture_service as cap

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix='pai3a-media-')

PNG = b'\x89PNG\r\n\x1a\n' + b'\x00' * 2048          # real PNG signature
JPG = b'\xff\xd8\xff\xe0' + b'\x00' * 2048
WEBP = b'RIFF' + b'\x00\x00\x00\x00' + b'WEBP' + b'\x00' * 2048
FAKE = b'MZ\x90\x00' + b'\x00' * 2048                # exe masquerading as image


def up(name, data, ctype='image/png'):
    return SimpleUploadedFile(name, data, content_type=ctype)


@override_settings(MEDIA_ROOT=MEDIA)
class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('pai3a@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('pai3a-w@test.local', password='x', role=wk)
        cls.product = Product.objects.create(code='PAI3A', name='PAI 3A')
        cls.product2 = Product.objects.create(code='PAI3A-B', name='PAI 3A B')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def store(self, data=PNG, name='x.png', **kw):
        d = dict(user=self.mgr, product=self.product,
                 uploaded_file=up(name, data),
                 source=CaptureAsset.Source.CAMERA)
        d.update(kw)
        return cap.store_capture(**d)


class UploadSecurityTests(_Base):
    def test_happy_png_stored_hash_named(self):
        a = self.store()
        self.assertEqual(a.content_type, 'image/png')
        self.assertEqual(a.sha256, hashlib.sha256(PNG).hexdigest())
        self.assertIn(f'patterns_ai/{self.product.pk}/originals/', a.file.name)
        self.assertTrue(a.file.name.endswith('.png'))
        self.assertEqual(a.status, 'stored')

    def test_magic_bytes_beat_client_lies(self):
        # .png name + image/png header but EXE bytes → refused
        with self.assertRaises(ValidationError):
            self.store(data=FAKE, name='innocent.png')
        # jpeg bytes with a lying .png name → accepted AS JPEG (content wins)
        a = self.store(data=JPG, name='lies.png')
        self.assertEqual(a.content_type, 'image/jpeg')
        self.assertTrue(a.file.name.endswith('.jpg'))
        w = self.store(data=WEBP, name='w.webp')
        self.assertEqual(w.content_type, 'image/webp')

    def test_size_caps(self):
        with self.assertRaises(ValidationError):
            self.store(data=PNG[:512], name='tiny.png')          # < 1 KB
        big = PNG + b'\x00' * cap.MAX_UPLOAD_BYTES
        with self.assertRaises(ValidationError):
            self.store(data=big, name='huge.png')

    def test_path_traversal_neutralized(self):
        a = self.store(name='../../../../etc/passwd\\..\\evil.png')
        self.assertNotIn('..', a.file.name)
        self.assertNotIn('..', a.original_filename)
        self.assertIn('/originals/', a.file.name)
        # display name is the sanitized basename, storage name is the hash
        self.assertNotIn('/', a.original_filename)

    def test_management_gate(self):
        with self.assertRaises(PermissionDenied):
            self.store(user=self.worker)


class DuplicateAndImmutabilityTests(_Base):
    def test_duplicate_per_product_refused_cross_product_allowed(self):
        a = self.store()
        with self.assertRaises(ValidationError) as ctx:
            self.store(name='again.png')
        self.assertIn(str(a.pk), str(ctx.exception))
        b = self.store(product=self.product2)                    # other product OK
        self.assertEqual(b.sha256, a.sha256)

    def test_identity_fields_immutable(self):
        a = self.store()
        a.sha256 = '0' * 64
        with self.assertRaises(RuntimeError):
            a.save()
        a.refresh_from_db()
        a.size_bytes = 1
        with self.assertRaises(RuntimeError):
            a.save()
        a.refresh_from_db()
        with self.assertRaises(RuntimeError):
            a.delete()

    def test_retire_with_reason_only(self):
        a = self.store()
        with self.assertRaises(ValidationError):
            cap.retire_capture(user=self.mgr, asset=a, reason='  ')
        cap.retire_capture(user=self.mgr, asset=a, reason='blurry, re-shot')
        a.refresh_from_db()
        self.assertEqual(a.status, 'retired')
        with self.assertRaises(ValidationError):
            cap.retire_capture(user=self.mgr, asset=a, reason='again')
        # file still exists — knowledge kept (F5)
        self.assertTrue(a.file.storage.exists(a.file.name))


class IntegrityTests(_Base):
    def test_verify_ok_then_tamper_then_missing(self):
        a = self.store()
        self.assertEqual(cap.verify_asset(a)[0], 'ok')
        # tamper on disk → mismatch
        with a.file.storage.open(a.file.name, 'wb') as fh:
            fh.write(b'tampered-bytes' * 100)
        state, detail = cap.verify_asset(a)
        self.assertEqual(state, 'mismatch')
        # sweep flags it corrupt with reason
        call_command('verify_patterns_media')
        a.refresh_from_db()
        self.assertEqual(a.status, 'corrupt')
        self.assertIn('sha mismatch', a.status_reason)
        # missing file → missing
        b = self.store(data=JPG, name='b.jpg')
        b.file.storage.delete(b.file.name)
        self.assertEqual(cap.verify_asset(b)[0], 'missing')

    def test_orphan_reported_as_warn_not_corruption(self):
        self.store()
        import pathlib
        from django.conf import settings
        orphan = pathlib.Path(settings.MEDIA_ROOT) / 'patterns_ai' / 'orphan.bin'
        orphan.parent.mkdir(parents=True, exist_ok=True)
        orphan.write_bytes(b'left by a rolled-back block')
        out = io.StringIO()
        call_command('verify_patterns_media', stdout=out)
        text = out.getvalue()
        self.assertIn('ORPHAN', text)
        self.assertIn('N-7', text)
        # sweep summary present and no asset got flagged for the orphan
        self.assertIn('orphans=1', text)
