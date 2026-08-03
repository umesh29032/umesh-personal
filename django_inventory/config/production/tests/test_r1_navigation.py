"""R1 (roadmap phase) tests — navigation/visibility + the F1 code guard.

Scope per docs/R1_EXECUTION_PLAN.md: read-only UI/navigation + ONE write-path
change (F1 validation guard). PDD refs: §23 (buttons), §27-D7 (My Work),
§27-D6 (broadcast), §31.1-F1 (code immutability).
"""
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import Skill, User
from inventory.models import Role
from production.forms.product_forms import ProductForm
from production.models import Product
from production.services import create_adda


def _superuser(email='admin@r1.test'):
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(email=email, password='x',
                                 is_superuser=True, is_staff=True)
    u.role = role
    u.save()
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


class ProductCodeGuardTests(TestCase):
    """F1: Product.code immutable once the product has any Adda (PDD §31.1-F1)."""

    def setUp(self):
        self.user = _superuser()
        self.product = Product.objects.get(code='T-SHIRT')

    def test_code_change_refused_once_adda_exists(self):
        create_adda(self.user, product=self.product)
        self.product.code = 'T-SHIRT-NEW'
        # full_clean = Django's model validation hook — ModelForm/admin call it.
        with self.assertRaises(ValidationError) as ctx:
            self.product.full_clean()
        self.assertIn('code', ctx.exception.message_dict)

    def test_other_fields_still_editable_with_addas(self):
        create_adda(self.user, product=self.product)
        self.product.name = 'T-Shirt Renamed'
        self.product.full_clean()  # must NOT raise — only code is locked

    def test_code_change_allowed_without_addas(self):
        # Model-level rule is exactly F1 (locked once Addas exist). The FORM is
        # stricter (locks on every edit) — pinned separately below.
        p = Product.objects.create(code='R1-TEMP', name='Temp')
        p.code = 'R1-TEMP2'
        p.full_clean()  # no Adda → model allows

    def test_form_still_locks_code_on_any_edit(self):
        # Regression-pin: ProductForm disables code on edit (pre-existing,
        # stricter-than-F1 behavior we keep).
        form = ProductForm(instance=self.product)
        self.assertTrue(form.fields['code'].disabled)


def _worker(email='worker@r1.test'):
    role = Role.objects.get(code='worker')
    u = User.objects.create_user(email=email, password='x')
    u.role = role
    u.save()
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


class AddaDetailButtonsTests(TestCase):
    """R1.1 (PDD §23): Settlement + Stage-Rates navigation, management-gated."""

    def setUp(self):
        self.admin = _superuser()
        self.worker = _worker()
        self.adda = create_adda(self.admin, product=Product.objects.get(code='T-SHIRT'))
        self.url = f'/production/addas/{self.adda.code}/'

    def test_management_sees_start_settlement_when_no_adst(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertContains(resp, 'Start Settlement')
        self.assertContains(resp, 'Stage Rates')       # existing S1.1 entry intact

    def test_management_sees_settlement_detail_link_when_adst_exists(self):
        from django.utils import timezone
        from expense.services.adda_settlement_service import create_draft
        # create_draft's gate (§11.5): ≥1 payable stage AND payable stages COMPLETED.
        self.adda.product.workflow_stages.update(credits_workers=True)
        self.adda.stage_records.update(completed_at=timezone.now())
        draft = create_draft(adda=self.adda, user=self.admin)
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertContains(resp, f'Settlement · {draft.reference}')
        self.assertNotContains(resp, 'Start Settlement')

    def test_worker_sees_no_admin_buttons(self):
        self.client.force_login(self.worker)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)         # workers CAN view the Adda
        self.assertNotContains(resp, 'Start Settlement')
        self.assertNotContains(resp, 'Settlement ·')
        # AUDIT-2 F-A: assert on the LINK, not the prose. The bare string
        # "Stage Rates" also appears in this page's own CSS comment, so a
        # whole-response substring match failed while the access control was
        # in fact correct (no link rendered, and the URL 403s for workers).
        # The href is the thing a worker must not be handed.
        self.assertNotContains(
            resp, f'/production/addas/{self.adda.code}/stage-rates/')


class MyWorkSectionTests(TestCase):
    """R1.2 (PDD §27-D7): self-scoped, presentation-only My Work section."""

    def setUp(self):
        from decimal import Decimal
        self.admin = _superuser()
        self.worker_a = _worker('a@r1.test')
        self.worker_b = _worker('b@r1.test')
        product = Product.objects.get(code='T-SHIRT')
        # Rate BEFORE create_adda → AddaStageRoleRate snapshot freezes ₹10.
        # cost_billed_at=None: seeded T-SHIRT layering is GROUPED — the F2
        # structural guard rightly forces a grouped member's pay rate to 0,
        # which would freeze expected=0 and hide the ₹ this test asserts.
        product.workflow_stages.update(cost_rate=Decimal('10'), cost_billed_at=None,
                                       credits_workers=True)   # A360 rule: non-payable freezes 0
        self.adda = create_adda(self.admin, product=product)
        self.url = f'/production/addas/{self.adda.code}/'
        # Assign worker A to layering; report 12 pcs; complete → expected frozen.
        from production.services import worker_task_service as wts
        sr = self.adda.stage_records.first()
        wts.set_stage_workers(sr, [self.worker_a.pk])
        self.task = sr.worker_tasks.get(worker=self.worker_a)
        wts.report_contributions(
            self.task, [{'reported_quantity': '12'}], actor=self.worker_a)
        wts.complete_worker_task(self.task, actor=self.worker_a)

    def test_assigned_worker_sees_own_work_and_expected(self):
        self.client.force_login(self.worker_a)
        resp = self.client.get(self.url)
        self.assertContains(resp, 'My Work on this Adda')
        self.assertContains(resp, '12')                 # own quantity
        # Frozen figure = 12 × ₹10 (visibility, not money) — exact token.
        self.assertContains(resp, 'Expected ₹120.00')

    def test_other_worker_sees_nothing_of_a(self):
        self.client.force_login(self.worker_b)
        resp = self.client.get(self.url)
        self.assertNotContains(resp, 'My Work on this Adda')  # B has no tasks
        self.assertNotContains(resp, 'Expected ₹')            # A's earning absent

    def test_management_without_tasks_sees_no_my_work(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertNotContains(resp, 'My Work on this Adda')

    def test_presentation_only_no_action_controls(self):
        # Owner clarification: NO submit/edit surface inside My Work.
        self.client.force_login(self.worker_a)
        html = self.client.get(self.url).content.decode()
        start = html.index('My Work on this Adda')
        end = html.index('Stages Overview') if 'Stages Overview' in html else len(html)
        section = html[start:end]
        self.assertNotIn('<form', section)
        self.assertNotIn('<input', section)
        self.assertNotIn('<button', section)
