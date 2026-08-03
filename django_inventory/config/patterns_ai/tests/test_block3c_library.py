"""Block-3C tests — read-only Marker Library (list/detail/thumbnails)."""
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Role
from production.models import Adda, Product, Stage, WorkflowStage
from patterns_ai.models import CaptureAsset, Marker
from patterns_ai.services import capture_service as cap
from patterns_ai.services import marker_service as ms
from patterns_ai.services import marker_feedback_service as fb

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix='pai3c-media-')

def _real_png(seed: int) -> bytes:
    """Generate a genuine PNG (PIL-readable, >1 KB) — unique per seed."""
    import io
    from PIL import Image
    img = Image.frombytes('RGB', (64, 64),
                          bytes((i * seed + j) % 256
                                for i in range(64) for j in range(64 * 3)))
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    data = buf.getvalue()
    return data + b'\x00' * max(0, 1100 - len(data))   # ensure >1 KB


@override_settings(MEDIA_ROOT=MEDIA)
class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('pai3c@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('pai3c-w@test.local', password='x', role=wk)
        cls.product = Product.objects.create(code='PAI3C', name='PAI 3C')
        st, _ = Stage.objects.get_or_create(code='pai3c_s', defaults={'name': 'S'})
        ws = WorkflowStage.objects.create(product=cls.product, stage=st, order=1)
        cls.adda = Adda.objects.create(code='PAI3C-001', product=cls.product,
                                       current_stage=ws)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    _seed = 0

    def asset(self, salt=b''):
        type(self)._seed += 1
        return cap.store_capture(
            user=self.mgr, product=self.product,
            uploaded_file=SimpleUploadedFile('c.png', _real_png(type(self)._seed),
                                             content_type='image/png'),
            source=CaptureAsset.Source.CAMERA)

    def marker(self, **kw):
        d = dict(user=self.mgr, product=self.product,
                 origin=Marker.Origin.IMPORTED, usable_width_mm=940)
        d.update(kw)
        return ms.create_marker(**d)


class ListTests(_Base):
    def test_list_renders_columns_and_thumb_url_not_original(self):
        a = self.asset()
        m = self.marker(origin=Marker.Origin.MANUAL_PHOTO, photo=a,
                        label='chalk')
        self.client.force_login(self.mgr)
        resp = self.client.get(reverse('patterns_ai:marker-list'))
        self.assertContains(resp, m.reference)
        self.assertContains(resp, 'PAI3C')
        self.assertContains(resp, '940')
        self.assertContains(resp, f'/patterns/captures/{a.pk}/thumb/')
        # ORIGINAL path never leaks into HTML
        self.assertNotContains(resp, a.file.url if hasattr(a.file, 'url') else 'originals/')
        self.assertNotContains(resp, 'originals/')

    def test_pagination_and_ordering(self):
        for i in range(25):
            self.marker(usable_width_mm=900 + i)
        self.client.force_login(self.mgr)
        r1 = self.client.get(reverse('patterns_ai:marker-list'))
        self.assertContains(r1, 'Page 1 / 2')
        r2 = self.client.get(reverse('patterns_ai:marker-list') + '?page=2')
        self.assertContains(r2, 'Page 2 / 2')
        rw = self.client.get(reverse('patterns_ai:marker-list') + '?sort=width')
        body = rw.content.decode()
        self.assertLess(body.index('>900<'), body.index('>905<'))  # ascending width

    def test_permissions(self):
        url = reverse('patterns_ai:marker-list')
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)


class DetailTests(_Base):
    def test_detail_biography_lineage_summary(self):
        base = self.marker(label='old')
        m = self.marker(supersedes=base, benchmarked_against=base)
        ms.transition_marker(user=self.mgr, marker=m, to_status='validated')
        u = fb.record_usage(user=self.mgr, marker=m, adda=self.adda,
                            plies=30, repeats=3)
        fb.record_outcome(user=self.mgr, usage=u, fabric_in_mm=45000,
                          garments_cut=60)
        self.client.force_login(self.mgr)
        resp = self.client.get(reverse('patterns_ai:marker-detail',
                                       kwargs={'reference': m.reference}))
        self.assertContains(resp, m.reference)
        self.assertContains(resp, 'candidate → validated')     # biography
        self.assertContains(resp, base.reference)              # lineage links
        self.assertContains(resp, 'PAI3C-001')                 # usage row
        self.assertContains(resp, '75.00')                     # m/100 metric
        self.assertContains(resp, 'n=1')                       # honest n
        # superseded ancestor page shows forward link
        resp2 = self.client.get(reverse('patterns_ai:marker-detail',
                                        kwargs={'reference': base.reference}))
        self.assertContains(resp2, m.reference)

    def test_detail_404_and_permissions(self):
        self.client.force_login(self.mgr)
        self.assertEqual(self.client.get(
            reverse('patterns_ai:marker-detail',
                    kwargs={'reference': 'MRK-999999'})).status_code, 404)
        m = self.marker()
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(
            reverse('patterns_ai:marker-detail',
                    kwargs={'reference': m.reference})).status_code, 403)


class ThumbTests(_Base):
    def test_thumb_served_gated_and_regenerable(self):
        from django.core.files.storage import default_storage
        from patterns_ai.services.capture_service import thumbnail_path
        a = self.asset()
        url = reverse('patterns_ai:capture-thumb', kwargs={'pk': a.pk})
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(url).status_code, 403)   # gated
        self.client.force_login(self.mgr)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'image/jpeg')
        body = b''.join(resp.streaming_content)
        self.assertEqual(body[:3], b'\xff\xd8\xff')               # real JPEG
        # regenerable: delete derived file → served again
        default_storage.delete(thumbnail_path(a))
        resp2 = self.client.get(url)
        self.assertEqual(resp2.status_code, 200)

    def test_unreadable_original_gives_404_never_original(self):
        a = self.asset(salt=b'2')
        # corrupt the ORIGINAL on disk (rendition build must fail cleanly)
        with a.file.storage.open(a.file.name, 'wb') as fh:
            fh.write(b'not-an-image')
        self.client.force_login(self.mgr)
        resp = self.client.get(reverse('patterns_ai:capture-thumb',
                                       kwargs={'pk': a.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_sweep_ignores_derived_class(self):
        import io
        from django.core.management import call_command
        a = self.asset(salt=b'3')
        self.client.force_login(self.mgr)
        self.client.get(reverse('patterns_ai:capture-thumb', kwargs={'pk': a.pk}))
        out = io.StringIO()
        call_command('verify_patterns_media', stdout=out)
        self.assertIn('orphans=0', out.getvalue())     # derived ≠ orphan
