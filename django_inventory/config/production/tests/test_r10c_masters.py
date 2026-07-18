"""R10-C pins — data-driven business masters (owner rule: classifications are
rows the business edits, never Python options)."""
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from inventory.models import Role
from production.models import MachineType, Stage, StageCategory


def _user(email, role_code='worker'):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=role_code)
    u.save()
    return u


class MasterCrudTests(TestCase):
    def setUp(self):
        self.admin = _user('r10c-sa@test', 'super_admin')
        self.worker = _user('r10c-w@test')

    def test_owner_creates_new_category_via_ui(self):
        """The 'Printing tomorrow' requirement — pure data, zero code."""
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('production:stage-category-add'), {
            'code': 'printing', 'name': 'Printing',
            'display_order': 25, 'is_active': 'on'})
        self.assertEqual(resp.status_code, 302)
        cat = StageCategory.objects.get(code='printing')
        # …and it appears in the Stage form picker immediately.
        resp = self.client.get(reverse('production:stage-add'))
        self.assertContains(resp, 'Printing')

    def test_rename_reflects_in_grouping(self):
        self.client.force_login(self.admin)
        cat = StageCategory.objects.get(code='stitching')
        self.client.post(
            reverse('production:stage-category-edit', args=[cat.pk]),
            {'code': 'stitching', 'name': 'Sewing Line',
             'display_order': cat.display_order, 'is_active': 'on'})
        cat.refresh_from_db()
        self.assertEqual(cat.name, 'Sewing Line')
        from production.views.presentation import group_stages_by_category

        class E:
            def __init__(self, c): self.category = c
        groups = group_stages_by_category([E(cat)], stage_of=lambda e: e)
        self.assertEqual(groups[0]['label'], 'Sewing Line')

    def test_deactivate_hides_from_picker_keeps_existing_fk(self):
        self.client.force_login(self.admin)
        cat = StageCategory.objects.get(code='pre_production')
        self.client.post(
            reverse('production:stage-category-edit', args=[cat.pk]),
            {'code': cat.code, 'name': cat.name,
             'display_order': cat.display_order})   # is_active unchecked
        cat.refresh_from_db()
        self.assertFalse(cat.is_active)
        from production.views.access_views import StageForm
        self.assertNotIn(cat, StageForm().fields['category'].queryset)
        # existing stages keep the FK + label (history never lies)
        self.assertEqual(Stage.objects.get(code='layering').category, cat)

    def test_machine_type_master_crud_and_picker(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('production:machine-type-add'), {
            'code': 'embroidery_machine', 'name': 'Embroidery Machine',
            'is_active': 'on'})
        self.assertEqual(resp.status_code, 302)
        mt = MachineType.objects.get(code='embroidery_machine')
        self.client.post(reverse('production:machine-type-edit', args=[mt.pk]),
                         {'code': mt.code, 'name': mt.name})   # deactivate
        mt.refresh_from_db()
        self.assertFalse(mt.is_active)
        from production.views.access_views import StageForm
        self.assertNotIn(mt, StageForm().fields['machine_type'].queryset)

    def test_workers_403_on_master_pages(self):
        self.client.force_login(self.worker)
        for name in ('stage-category-list', 'stage-category-add',
                     'machine-type-list', 'machine-type-add'):
            self.assertEqual(
                self.client.get(reverse(f'production:{name}')).status_code,
                403, name)

    def test_no_static_category_options_anywhere(self):
        """Owner's final goal pinned: category names exist ONLY as rows (and
        the seed migration) — never as Python choices/constants."""
        import pathlib
        import re
        pat = re.compile(r"choices\s*=.*(Stitching|Pre Production|Finishing|Dispatch)")
        offenders = [
            str(f) for f in pathlib.Path('production').rglob('*.py')
            if 'migrations' not in str(f) and pat.search(f.read_text())
        ]
        self.assertEqual(offenders, [])
