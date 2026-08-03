"""Phase-E worker certification (2026-07-12): master CRUD writes =
MANAGEMENT acts — the old ProductionRoleMixin + PRODUCTION_ROLES service
gate let any worker create/edit/archive/hard-delete cloth types/colors/
storage locations (browser+shell-proven; same name-trap class as M9/BUG-1).
Lists stay ProductionRole (read-only; SidebarItemRule blocks workers there)."""
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import archive_master, hard_delete_master

User = get_user_model()


class MasterWriteGateTests(TestCase):
    def setUp(self):
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        self.worker = User.objects.create_user('certew@test.local', password='x', role=wk)
        self.manager = User.objects.create_user('certem@test.local', password='x', role=mgr)
        self.ct = ClothType.objects.create(name='CERT-E-TYPE')

    def test_worker_blocked_from_master_write_views(self):
        self.client.force_login(self.worker)
        urls = [
            reverse('raw_materials:cloth-type-create'),
            reverse('raw_materials:cloth-type-update', args=[self.ct.pk]),
            reverse('raw_materials:cloth-type-archive', args=[self.ct.pk]),
            reverse('raw_materials:cloth-type-delete', args=[self.ct.pk]),
            reverse('raw_materials:cloth-color-create'),
            reverse('raw_materials:storage-create'),
        ]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403, url)
        # POST inertia: no row created, archive flag untouched
        resp = self.client.post(reverse('raw_materials:cloth-type-create'),
                                {'name': 'CERT-E-HACK'})
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(ClothType.objects.filter(name='CERT-E-HACK').exists())
        resp = self.client.post(
            reverse('raw_materials:cloth-type-archive', args=[self.ct.pk]))
        self.assertEqual(resp.status_code, 403)
        self.ct.refresh_from_db()
        self.assertTrue(self.ct.is_active)

    def test_manager_passes_master_write_views(self):
        self.client.force_login(self.manager)
        self.assertEqual(
            self.client.get(reverse('raw_materials:cloth-type-create')).status_code, 200)
        resp = self.client.post(
            reverse('raw_materials:cloth-type-archive', args=[self.ct.pk]))
        self.assertEqual(resp.status_code, 302)
        self.ct.refresh_from_db()
        self.assertFalse(self.ct.is_active)

    def test_service_gate_blocks_worker(self):
        # Defence in depth — the service refuses even if a view slipped
        with self.assertRaises(PermissionDenied):
            archive_master(self.worker, self.ct)
        with self.assertRaises(PermissionDenied):
            hard_delete_master(self.worker, self.ct)

    # DEPLOYMENT_BACKLOG #5 pins (MGT-E 2026-07-12): DeleteView context lacked
    # title/list_url_name -> `{% url list_url_name %}` = NoReverseMatch 500 on
    # the confirm GET for EVERY allowed role, all three masters.
    def test_manager_delete_confirm_page_renders(self):
        cc = ClothColor.objects.create(name='CERT-E-COLOR')
        sl = StorageLocation.objects.create(name='CERT-E-LOC', code='CEL')
        self.client.force_login(self.manager)
        cases = [
            (reverse('raw_materials:cloth-type-delete', args=[self.ct.pk]),
             reverse('raw_materials:cloth-type-list'), 'Delete Cloth Type'),
            (reverse('raw_materials:cloth-color-delete', args=[cc.pk]),
             reverse('raw_materials:cloth-color-list'), 'Delete Cloth Color'),
            (reverse('raw_materials:storage-delete', args=[sl.pk]),
             reverse('raw_materials:storage-list'), 'Delete Storage Location'),
        ]
        for url, list_url, title in cases:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, url)
            body = resp.content.decode()
            self.assertIn(f'href="{list_url}"', body, url)   # Cancel link reverses
            self.assertIn(title, body, url)

    def test_manager_delete_confirm_then_post_deletes(self):
        # Full workflow: confirm page -> POST -> row gone + redirect to list
        victim = ClothType.objects.create(name='CERT-E-DELETE-ME')
        self.client.force_login(self.manager)
        url = reverse('raw_materials:cloth-type-delete', args=[victim.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse('raw_materials:cloth-type-list'))
        self.assertFalse(ClothType.objects.filter(pk=victim.pk).exists())
