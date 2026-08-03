"""Block-3B tests — the manual-marker capture workflow end-to-end.

Browser-request flow via the Django test client (multipart upload → marker
created through the services → success page), plus every refusal path.
"""
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Role
from production.models import Product
from patterns_ai.models import CaptureAsset, Marker, MarkerTransitionEvent
from patterns_ai.services import capture_service as cap
from patterns_ai.services import marker_service as ms

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix='pai3b-media-')
PNG = b'\x89PNG\r\n\x1a\n' + b'\x01' * 2048
JPG = b'\xff\xd8\xff\xe0' + b'\x02' * 2048
FAKE = b'MZ\x90\x00' + b'\x00' * 2048


def form_data(product_pk, photo_bytes=PNG, name='chalk.png', **over):
    d = {'product': product_pk, 'label': "Master's tube layout",
         'usable_width_mm': 937, 'construction': 'tubular',
         'ratio_text': '1:2, 2:1', 'source': 'camera', 'notes': '',
         'photo': SimpleUploadedFile(name, photo_bytes, content_type='image/png')}
    d.update(over)
    return d


@override_settings(MEDIA_ROOT=MEDIA)
class _Base(TestCase):
    URL = None

    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('pai3b@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('pai3b-w@test.local', password='x', role=wk)
        cls.product = Product.objects.create(code='PAI3B', name='PAI 3B')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)


class WorkflowTests(_Base):
    def test_happy_flow_upload_marker_link_success_page(self):
        self.client.force_login(self.mgr)
        url = reverse('patterns_ai:manual-marker-new')
        self.assertEqual(self.client.get(url).status_code, 200)
        resp = self.client.post(url, form_data(self.product.pk))
        self.assertEqual(resp.status_code, 302)
        marker = Marker.objects.get(product=self.product)
        self.assertEqual(marker.origin, 'manual_photo')
        self.assertEqual(marker.usable_width_band, 93)
        self.assertEqual(marker.ratio['counts'], {'1': 2, '2': 1})
        self.assertIsNotNone(marker.photo)
        self.assertEqual(marker.photo.product_id, self.product.pk)
        # creation event carries the photo reference
        ev = MarkerTransitionEvent.objects.get(marker=marker)
        self.assertEqual(ev.metadata.get('photo_asset'), marker.photo_id)
        # success page renders the reference
        page = self.client.get(resp.url)
        self.assertContains(page, marker.reference)
        self.assertContains(page, 'sha')

    def test_atomicity_marker_failure_leaves_no_orphan_asset(self):
        self.client.force_login(self.mgr)
        url = reverse('patterns_ai:manual-marker-new')
        resp = self.client.post(url, form_data(self.product.pk,
                                               usable_width_mm=0))
        self.assertEqual(resp.status_code, 200)          # re-rendered w/ errors
        self.assertEqual(CaptureAsset.objects.count(), 0)
        self.assertEqual(Marker.objects.count(), 0)

    def test_duplicate_upload_shows_friendly_error(self):
        self.client.force_login(self.mgr)
        url = reverse('patterns_ai:manual-marker-new')
        self.client.post(url, form_data(self.product.pk))
        resp = self.client.post(url, form_data(self.product.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'already exists')
        self.assertEqual(Marker.objects.count(), 1)

    def test_invalid_file_rejected_via_ui(self):
        self.client.force_login(self.mgr)
        url = reverse('patterns_ai:manual-marker-new')
        resp = self.client.post(url, form_data(self.product.pk,
                                               photo_bytes=FAKE, name='x.png'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'disguised')
        self.assertEqual(CaptureAsset.objects.count(), 0)

    def test_bad_ratio_text_friendly(self):
        self.client.force_login(self.mgr)
        resp = self.client.post(reverse('patterns_ai:manual-marker-new'),
                                form_data(self.product.pk, ratio_text='banana'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'sizecode:count')


class PermissionTests(_Base):
    def test_worker_forbidden_get_and_post(self):
        self.client.force_login(self.worker)
        url = reverse('patterns_ai:manual-marker-new')
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, form_data(self.product.pk)).status_code, 403)
        # success page equally gated
        self.assertEqual(self.client.get(
            reverse('patterns_ai:manual-marker-created',
                    kwargs={'reference': 'MRK-000001'})).status_code, 403)

    def test_anonymous_redirected_to_login(self):
        resp = self.client.get(reverse('patterns_ai:manual-marker-new'))
        self.assertEqual(resp.status_code, 302)
        # project LOGIN_URL is /app/ — assert the auth redirect carries next=
        self.assertIn('next=/patterns/markers/manual/new/', resp.url)


class ServiceIntegrationTests(_Base):
    def _asset(self, data=PNG, product=None):
        return cap.store_capture(
            user=self.mgr, product=product or self.product,
            uploaded_file=SimpleUploadedFile('a.png', data,
                                             content_type='image/png'),
            source=CaptureAsset.Source.CAMERA)

    def test_manual_marker_requires_photo(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            ms.create_marker(user=self.mgr, product=self.product,
                             origin=Marker.Origin.MANUAL_PHOTO,
                             usable_width_mm=900)

    def test_photo_reuse_refused_one_photo_one_marker(self):
        from django.core.exceptions import ValidationError
        a = self._asset()
        m1 = ms.create_marker(user=self.mgr, product=self.product,
                              origin=Marker.Origin.MANUAL_PHOTO,
                              usable_width_mm=900, photo=a)
        with self.assertRaises(ValidationError) as ctx:
            ms.create_marker(user=self.mgr, product=self.product,
                             origin=Marker.Origin.MANUAL_PHOTO,
                             usable_width_mm=910, photo=a)
        self.assertIn(m1.reference, str(ctx.exception))

    def test_cross_product_photo_refused(self):
        from django.core.exceptions import ValidationError
        p2 = Product.objects.create(code='PAI3B-X', name='X')
        a = self._asset(product=p2)
        with self.assertRaises(ValidationError):
            ms.create_marker(user=self.mgr, product=self.product,
                             origin=Marker.Origin.MANUAL_PHOTO,
                             usable_width_mm=900, photo=a)

    def test_retired_photo_refused(self):
        from django.core.exceptions import ValidationError
        a = self._asset(data=JPG)
        cap.retire_capture(user=self.mgr, asset=a, reason='blurry')
        with self.assertRaises(ValidationError):
            ms.create_marker(user=self.mgr, product=self.product,
                             origin=Marker.Origin.MANUAL_PHOTO,
                             usable_width_mm=900, photo=a)
