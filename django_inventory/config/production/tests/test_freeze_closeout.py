"""Freeze-closeout pins (C-1 / C-2 / C-3, 2026-07-05).

C-1: NO automatic worker assignment anywhere — creating/editing a user (the
     old retro-tag triggers) never creates tasks; manager assignment via
     set_stage_workers is the only roster source.
C-2: worker-facing listings use the LIVE composed predicate (Stage Access AND
     assignment): dashboard accordions/board/rows and Adda-page tabs never
     offer a workspace the panel gate would refuse.
C-3: the report view requires BOTH an active assignment AND current Stage
     Access — revoking access in the hub closes the report path immediately.
"""
from django.test import TestCase
from django.urls import reverse

from accounts.models import Skill, User
from inventory.models import Role
from inventory.views.dashboard import _build_dashboard_context
from production.models import AddaStageRecord, Product, Stage, WorkerStageTask
from production.services import create_adda
from production.services.worker_task_service import set_stage_workers


def _user(email, *, role_code='worker', skills=(), active=True):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=role_code)
    u.is_active = active
    u.save()
    for s in skills:
        u.skills.add(Skill.objects.get(name=s))
    return u


class C1NoAutomaticAssignmentTests(TestCase):
    def test_user_create_view_never_creates_tasks(self):
        """The old retro-tag trigger: creating a SKILLED user via Team Members
        must not touch production rosters (even with active layerings)."""
        admin = _user('c1-admin@test', role_code='super_admin',
                      skills=['cutting_master'])
        create_adda(admin, product=Product.objects.get(code='T-SHIRT'))
        self.client.force_login(admin)
        before = WorkerStageTask.objects.count()
        from accounts.models import UserType
        resp = self.client.post(reverse('accounts:user_add'), {
            'email': 'c1-new@test.local', 'first_name': 'New', 'last_name': 'Master',
            'password': 'Str0ngP@ssw0rd!', 'confirm_password': 'Str0ngP@ssw0rd!',
            'user_type': UserType.objects.get(code='worker').pk,
            'role': Role.objects.get(code='worker').pk,
            'is_active': 'on',
            'skills': [Skill.objects.get(name='cutting_master').pk],
        })
        self.assertEqual(resp.status_code, 302,
                         getattr(resp, 'context_data', {}).get('form', ''))
        self.assertTrue(User.objects.filter(email='c1-new@test.local').exists())
        self.assertEqual(WorkerStageTask.objects.count(), before)

    def test_retro_tag_symbols_are_gone(self):
        import production.services as svc
        self.assertFalse(hasattr(svc, 'sync_layering_workers_for_skill'))
        from accounts.services import user_service
        self.assertFalse(hasattr(user_service, 'sync_user_skills'))


class C2C3WorldTestCase(TestCase):
    """Shared world: one Adda at layering; one assigned worker; one skilled-
    but-unassigned worker. Layering access = master+helper (seeded)."""

    def setUp(self):
        self.admin = _user('c2-admin@test', role_code='super_admin',
                           skills=['cutting_master'])
        self.assigned = _user('c2-w1@test', skills=['cutting_master'])
        self.unassigned = _user('c2-w2@test', skills=['cutting_master'])
        self.adda = create_adda(self.admin, product=Product.objects.get(code='T-SHIRT'))
        self.sr = AddaStageRecord.objects.get(
            adda=self.adda, workflow_stage__stage__code='layering')
        set_stage_workers(self.sr, [self.assigned.pk])

    def _dash(self, user):
        class _Req:
            pass
        req = _Req()
        req.user = user
        return _build_dashboard_context(req, is_admin_view=False)

    # ── C-2: dashboard = the composed live predicate ─────────────────────
    def test_assigned_worker_gets_workspace_accordion(self):
        ctx = self._dash(self.assigned)
        addas = {a.code: a for a in ctx['active_addas']}
        self.assertIn(self.adda.code, addas)
        self.assertTrue(addas[self.adda.code].current_can_open)

    def test_unassigned_worker_sees_no_adda_card_at_all(self):
        # Worker isolation: no active task on the Adda → not even the card.
        ctx = self._dash(self.unassigned)
        self.assertEqual([a.code for a in ctx['active_addas']], [])

    def test_access_revocation_kills_accordion_and_rows_live(self):
        """The owner's barcode scenario: revoke the stage's access → the
        assigned worker's accordion + MY ACTIVE STAGES row vanish on next
        render, with the task (production truth) untouched."""
        stage = Stage.objects.get(code='layering')
        stage.access_by_skill.clear()
        ctx = self._dash(self.assigned)
        addas = {a.code: a for a in ctx['active_addas']}
        self.assertIn(self.adda.code, addas)          # card stays (assigned)
        self.assertFalse(addas[self.adda.code].current_can_open)  # workspace gone
        self.assertEqual(ctx['my_active_stages'], [])  # actionable row gone
        self.assertFalse(ctx['is_skilled_user'])       # board gone (no hardcoded skill)
        self.assertTrue(                                # truth untouched
            WorkerStageTask.objects.filter(
                stage_record=self.sr, worker=self.assigned)
            .exclude(status='cancelled').exists())

    def test_helper_board_follows_access_rows_not_constants(self):
        # Grant access to a role-less skill user via the HUB rows, not code.
        ctx = self._dash(self.assigned)
        self.assertTrue(ctx['is_skilled_user'])
        self.assertIsNotNone(ctx['helper_data'])

    def test_adda_page_can_open_matches_gate(self):
        self.client.force_login(self.unassigned)
        resp = self.client.get(reverse('production:adda-detail',
                                       kwargs={'code': self.adda.code}))
        self.assertEqual(resp.status_code, 200)
        stages = {s.stage_type: s for s in resp.context['stages']}
        self.assertTrue(stages['layering'].has_access)      # skilled…
        self.assertFalse(stages['layering'].can_open)       # …but unassigned
        self.assertContains(resp, 'Not assigned')           # honest card
        self.assertNotContains(resp, '/stage/layering/?embedded=1')

    # ── C-3: report path = assignment AND live access ────────────────────
    def test_report_requires_both_assignment_and_access(self):
        url = reverse('production:worker-report',
                      kwargs={'code': self.adda.code, 'stage_type': 'layering'})
        # Assigned + access → 200
        self.client.force_login(self.assigned)
        self.assertEqual(self.client.get(url).status_code, 200)
        # Revoke access in the hub → immediately 403, GET and POST
        Stage.objects.get(code='layering').access_by_skill.clear()
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_report_still_refuses_unassigned_even_with_access(self):
        self.client.force_login(self.unassigned)
        url = reverse('production:worker-report',
                      kwargs={'code': self.adda.code, 'stage_type': 'layering'})
        self.assertEqual(self.client.get(url).status_code, 403)
