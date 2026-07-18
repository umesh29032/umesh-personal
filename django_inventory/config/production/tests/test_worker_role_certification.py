"""V1.1 Worker Role Certification — Phase A (Production app, 2026-07-12).

Pins the 3 bugs found + fixed during the worker-role audit so they can
never regress silently:

  FIX-1 complete_cutting_legacy: was `_ensure_can_manage` (= PRODUCTION
        roles, name trap) — any worker could complete Cutting (stage
        advance + barcode generation + cost freeze). Now MANAGEMENT-only.
  FIX-2 save_layering_draft: production role alone let ANY worker tamper
        layering drafts on any Adda. Draft = write surface → assigned
        worker, helper skill, or management only.
  FIX-3 _build_cutting_context: per-bundle-item allocation rows (era-A ₹
        earning snapshots of OTHER workers) were built for every viewer.
        Management-only ctx now — workers receive zero allocation bytes
        (V2-3 visibility rule: own money only).

Certification report: docs/WORKER_ROLE_CERTIFICATION.md
"""
from decimal import Decimal
from unittest import mock

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import RequestFactory, TestCase
from django.utils import timezone

from accounts.models import Role, Skill, User
from production.models import (
    Adda, AddaStageRecord, CuttingPieceBreakup, CuttingRecord, CuttingStream,
    Product, ProductPattern, ProductPatternAssignment, ProductSize, Stage,
    WorkflowStage, WorkerStageTask,
)
from production.services import pool_service


def _user(email, *, role_code='worker', skills=(), is_super=False):
    u = User.objects.create_user(email=email, password='x',
                                 is_superuser=is_super, is_staff=is_super)
    u.role = Role.objects.get(code=role_code)
    u.save()
    for s in skills:
        u.skills.add(Skill.objects.get(name=s))
    return u


class LegacyCuttingCompleteGateTests(TestCase):
    """FIX-1: the legacy single-shot cutting completion is a management act."""

    @classmethod
    def setUpTestData(cls):
        cls.worker = _user('wcert-w1@test', skills=['cutting_master'])
        cls.mgr = _user('wcert-m1@test', role_code='manager')
        # Adda with NO current stage: the role gate fires BEFORE any stage
        # validation, so worker → PermissionDenied while manager falls
        # through to the "not at Cutting" ValidationError (gate passed).
        product = Product.objects.create(code='WCERT1', name='WCert1')
        cls.adda = Adda.objects.create(code='WCERT1-001', product=product)

    def _call(self, user):
        from production.stages.cutting.service import complete_cutting_legacy
        return complete_cutting_legacy(
            adda=self.adda, pieces_cut=5, worker_ids=[], notes='', user=user)

    def test_worker_blocked_even_with_cutting_skill(self):
        with self.assertRaisesMessage(
                PermissionDenied,
                'only management can complete the cutting stage'):
            self._call(self.worker)

    def test_manager_passes_the_role_gate(self):
        with self.assertRaisesMessage(ValidationError,
                                      'not at Cutting stage'):
            self._call(self.mgr)   # role gate passed; stage check refuses


class LayeringDraftGateTests(TestCase):
    """FIX-2: layering draft save = write surface → assigned / helper / mgmt."""

    def setUp(self):
        from production.services import create_adda, start_layering
        admin = _user('wcert-adm@test', role_code='super_admin',
                      is_super=True,
                      skills=['cutting_master', 'cutting_master_helper'])
        self.assigned = _user('wcert-asg@test', skills=['cutting_master'])
        self.outsider = _user('wcert-out@test', skills=['cutting_master'])
        self.helper = _user('wcert-hlp@test',
                            skills=['cutting_master_helper'])
        self.mgr = _user('wcert-m2@test', role_code='manager')
        self.adda = create_adda(admin,
                                product=Product.objects.get(code='T-SHIRT'))
        self.sr = start_layering(adda=self.adda,
                                 worker_ids=[self.assigned.pk], user=admin)

    def _draft(self, user, note):
        from production.stages.layering.service import save_layering_draft
        return save_layering_draft(
            adda=self.adda, layer_length_meters=None, duration_minutes=None,
            notes=note, per_entry_data={}, user=user)

    def test_unassigned_worker_blocked(self):
        with self.assertRaisesMessage(PermissionDenied,
                                      'not assigned to this stage'):
            self._draft(self.outsider, 'tamper')
        self.sr.refresh_from_db()
        self.assertEqual(self.sr.draft_notes, '')   # nothing written

    def test_assigned_worker_helper_and_management_allowed(self):
        for user, note in ((self.assigned, 'mine'),
                           (self.helper, 'helper pass'),
                           (self.mgr, 'mgmt pass')):
            self._draft(user, note)
            self.sr.refresh_from_db()
            self.assertEqual(self.sr.draft_notes, note)


class CuttingAllocationCtxVisibilityTests(TestCase):
    """FIX-3: bundle allocation rows (other workers' ₹) = management-only ctx."""

    def setUp(self):
        from production.stages.cutting.service import create_bundle_with_pieces
        self.mgr = _user('wcert-m3@test', role_code='manager')
        self.worker = _user('wcert-w3@test', skills=['cutting_master'])
        product = Product.objects.create(code='WCERT3', name='WCert3')
        size = ProductSize.objects.create(product=product, code='m',
                                          label='M', display_order=1)
        from raw_materials.models import ClothColor
        navy = ClothColor.objects.create(name='WCert3 Navy')
        cutting = Stage.objects.get(code='cutting')
        ws = WorkflowStage.objects.create(product=product, stage=cutting,
                                          order=1, cost_rate=Decimal('1'))
        self.adda = Adda.objects.create(code='WCERT3-001', product=product,
                                        current_stage=ws)
        pat = ProductPattern.objects.create(code='WCERT3-BODY', name='Body')
        ProductPatternAssignment.objects.create(product=product, pattern=pat,
                                                pieces_count=1)
        lane = CuttingStream.objects.create(adda=self.adda,
                                            fabric_group='body', sequence=1,
                                            is_blocking=True, reason='')
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=ws, stream=lane,
            started_at=timezone.now(), completed_at=timezone.now())
        cr = CuttingRecord.objects.create(stage_record=self.sr, pieces_cut=30)
        breakup = CuttingPieceBreakup.objects.create(
            cutting_record=cr, pattern=pat, color=navy, size=size, count=30)
        # Viewing the console requires an assignment (GAP-4 lane scoping) —
        # the worker is legitimately ON the stage, yet must see no alloc rows.
        WorkerStageTask.objects.create(stage_record=self.sr,
                                       worker=self.worker,
                                       status=WorkerStageTask.Status.ASSIGNED)
        provider = mock.patch.object(pool_service, 'MANDATORY_PATTERNS_PROVIDER',
                                     lambda product: {pat.pk})
        provider.start()
        self.addCleanup(provider.stop)
        bundle = create_bundle_with_pieces(
            adda=self.adda, size_id=size.pk, user=self.mgr,
            selections=[{'breakup_id': breakup.pk, 'take_count': 10}])
        # The workspace snapshot lists bundles via cutting_record (era-A
        # anchor — the shape the leak occurred on); pin it the same way.
        bundle.cutting_record = cr
        bundle.save(update_fields=['cutting_record'])

    def _ctx(self, user):
        from production.views.stage_views import _build_cutting_context
        request = RequestFactory().get('/production/addas/WCERT3-001/cutting/')
        request.user = user
        return _build_cutting_context(request, self.adda)

    def test_worker_gets_zero_allocation_bytes(self):
        ctx = self._ctx(self.worker)
        bundles = list(ctx['bundles'])
        self.assertEqual(len(bundles), 1)
        self.assertEqual(bundles[0].alloc_items, [])   # FIX-3: empty for worker

    def test_management_still_sees_allocation_rows(self):
        ctx = self._ctx(self.mgr)
        bundles = list(ctx['bundles'])
        self.assertEqual(len(bundles), 1)
        self.assertEqual(len(bundles[0].alloc_items), 1)
        row = bundles[0].alloc_items[0]
        self.assertIn('allocated', row)
        self.assertIn('remaining', row)
