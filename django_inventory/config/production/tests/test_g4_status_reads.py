"""BOD-C G-4 (owner-gated 2026-07-18) — adda_status_counts + stage_breakdown
in their OWNING app, + the INERT proof: the Adda dashboard shows the SAME
numbers through the extraction as the functions return directly."""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from production.models import Adda, AddaStageRecord, Product, Stage, WorkflowStage
from production.services.operations_digest import adda_status_counts, stage_breakdown


class G4StatusReadTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sa = User.objects.create_user(
            email='g4-sa@test', password='x', is_superuser=True)
        cls.sa.role = Role.objects.get(code='super_admin')
        cls.sa.save()
        product = Product.objects.create(code='G4', name='G4 Prod')
        stage, _ = Stage.objects.get_or_create(code='g4_s', defaults={'name': 'G4 Stage'})
        ws = WorkflowStage.objects.create(
            product=product, stage=stage, order=1,
            cost_rate=Decimal('3'), credits_workers=True)
        cls.ip1 = Adda.objects.create(code='G4-IP1', product=product,
                                      status=Adda.Status.IN_PROGRESS)
        AddaStageRecord.objects.create(adda=cls.ip1, workflow_stage=ws,
                                       started_at=timezone.now())
        cls.ip1.current_stage = ws   # FK = WorkflowStage (chips group on it)
        cls.ip1.save(update_fields=['current_stage'])
        cls.hold = Adda.objects.create(code='G4-HOLD', product=product,
                                       status=Adda.Status.ON_HOLD)
        # completed_today lookup: __date converts to LOCAL tz while the
        # filter value is the UTC date (pre-existing dashboard semantics,
        # preserved verbatim). Pin to noon UTC so both dates agree at any
        # test-run hour — no midnight-straddle flake.
        from datetime import datetime, time as dtime, timezone as dttz
        noon_utc = datetime.combine(timezone.now().date(), dtime(12, 0),
                                    tzinfo=dttz.utc)
        cls.done = Adda.objects.create(code='G4-DONE', product=product,
                                       status=Adda.Status.COMPLETED,
                                       completed_at=noon_utc)

    def test_adda_status_counts(self):
        c = adda_status_counts()
        self.assertEqual(c['in_progress'], 1)
        self.assertEqual(c['on_hold'], 1)
        self.assertEqual(c['completed_today'], 1)
        self.assertEqual(c['total_completed'], 1)

    def test_stage_breakdown_only_stages_with_work(self):
        chips = stage_breakdown()
        self.assertEqual(chips, [{'label': 'G4 Stage', 'count': 1}])

    def test_adda_dashboard_is_inert_after_the_extraction(self):
        # The certified page renders the SAME numbers via the new functions.
        self.client.force_login(self.sa)
        r = self.client.get(reverse('production:dashboard'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['in_progress'], 1)
        self.assertEqual(r.context['on_hold'], 1)
        self.assertEqual(r.context['completed_today'], 1)
        self.assertEqual(r.context['total_completed'], 1)
        self.assertEqual(r.context['stage_breakdown'],
                         [{'label': 'G4 Stage', 'count': 1}])

    def test_fields_subset_matches_the_full_call(self):
        # BOD-D: the fields= subset runs the SAME expressions — one truth.
        full = adda_status_counts()
        self.assertEqual(adda_status_counts(fields=("on_hold",)),
                         {'on_hold': full['on_hold']})

    def test_date_filter_semantics_preserved(self):
        # from-dt in the future excludes everything created today —
        # EXCEPT completed_today, which the dashboard always showed globally.
        future = timezone.now() + timezone.timedelta(days=2)
        c = adda_status_counts(from_dt=future)
        self.assertEqual((c['in_progress'], c['on_hold'], c['total_completed']),
                         (0, 0, 0))
        self.assertEqual(c['completed_today'], 1)
        self.assertEqual(stage_breakdown(from_dt=future), [])
