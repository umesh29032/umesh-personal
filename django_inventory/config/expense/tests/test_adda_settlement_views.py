"""V2-2 PR-D: management settlement UI + the LEDGER_CREDIT_AT_ALLOCATION lever.

Covers: access gating, pending queue, draft preview (3 line classes incl. the
era-A exclusion label), finalize/reverse/supersede/discard POSTs, the flag-OFF
allocation refusal, and the symmetric cross-era guard on allocation.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from expense.models import (
    AddaSettlement, WorkerAdvance, WorkerLedgerEntry,
)
from expense.services.adda_settlement_service import (
    create_draft, finalize_adda_settlement,
)
from expense.services.allocation_service import allocate_stage_work
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage, WorkerStageTask,
)
from production.services.worker_task_service import (
    complete_worker_task, report_contributions, set_stage_workers,
)


class _Base(TestCase):
    """Same 3-PATTI-001-shaped world as the service tests, plus a client."""

    def setUp(self):
        self.mgmt = User.objects.create_user(
            email='adv-mgmt@test', password='x')
        self.mgmt.role = Role.objects.get(code='manager')
        self.mgmt.save()
        self.w1 = User.objects.create_user(email='adv-w1@test', password='x')
        self.product = Product.objects.create(code='ADV', name='ADV P')
        pay_stage, _ = Stage.objects.get_or_create(
            code='adv_cutting', defaults={'name': 'ADV Cutting'})
        self.ws_pay = WorkflowStage.objects.create(
            product=self.product, stage=pay_stage, order=1,
            cost_rate=Decimal('3'), credits_workers=True)
        self.adda = Adda.objects.create(code='ADV-001', product=self.product)
        self.sr_pay = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws_pay,
            started_at=timezone.now())
        self.client.force_login(self.mgmt)

    def _contribute(self, worker, qty):
        set_stage_workers(self.sr_pay, [worker.pk])
        task = WorkerStageTask.objects.get(
            stage_record=self.sr_pay, worker=worker)
        report_contributions(task, [{'reported_quantity': str(qty)}],
                             actor=worker)
        complete_worker_task(task, actor=worker)
        return task

    def _close_stage(self):
        self.sr_pay.completed_at = timezone.now()
        self.sr_pay.save(update_fields=['completed_at'])


class AccessTests(_Base):
    def test_worker_gets_403_everywhere(self):
        self.client.force_login(self.w1)
        for url in (reverse('expense:adda-settlement-list'),
                    reverse('expense:adda-settlement-start', args=[self.adda.pk])):
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url).status_code, 403)


class QueueAndDraftTests(_Base):
    def test_queue_shows_ready_adda_and_start_creates_draft(self):
        self._contribute(self.w1, 10)
        self._close_stage()
        resp = self.client.get(reverse('expense:adda-settlement-list'))
        self.assertContains(resp, 'ADV-001')
        self.assertContains(resp, 'Start settlement')
        resp = self.client.post(
            reverse('expense:adda-settlement-start', args=[self.adda.pk]))
        s = AddaSettlement.objects.get(adda=self.adda)
        self.assertRedirects(resp, reverse(
            'expense:adda-settlement-detail', args=[s.reference]))
        # second start RESUMES, never stacks a duplicate draft
        self.client.post(
            reverse('expense:adda-settlement-start', args=[self.adda.pk]))
        self.assertEqual(AddaSettlement.objects.filter(adda=self.adda).count(), 1)

    def test_incomplete_stage_lists_under_waiting(self):
        self._contribute(self.w1, 10)        # stage NOT closed
        resp = self.client.get(reverse('expense:adda-settlement-list'))
        self.assertContains(resp, 'Waiting on production')
        self.assertContains(resp, 'ADV Cutting')

    @override_settings(LEDGER_CREDIT_AT_ALLOCATION=True)   # era-A fixture needs the lever
    def test_draft_preview_labels_era_a_exclusion(self):
        self._contribute(self.w1, 10)
        # era-A: legacy allocation credit for the same worker+stage
        allocate_stage_work(user=self.mgmt, stage_record=self.sr_pay,
                            worker=self.w1, allocated_quantity=Decimal('10'))
        self._close_stage()
        s = create_draft(adda=self.adda, user=self.mgmt)
        resp = self.client.get(reverse(
            'expense:adda-settlement-detail', args=[s.reference]))
        self.assertContains(resp, 'already credited at allocation')
        self.assertContains(resp, 'pay the worker twice')
        self.assertNotContains(resp, 'Finalize settlement')   # nothing settleable


class FinalizeAndCorrectionTests(_Base):
    def _draft_with_work(self):
        self._contribute(self.w1, 10)
        self._close_stage()
        return create_draft(adda=self.adda, user=self.mgmt)

    def test_finalize_post_books_money_with_variance_and_recovery(self):
        adv = WorkerAdvance.objects.create(
            worker=self.w1, amount=Decimal('20'),
            advance_date=timezone.now().date(), entered_by=self.mgmt)
        s = self._draft_with_work()
        url = reverse('expense:adda-settlement-detail', args=[s.reference])
        resp = self.client.post(url, {
            'action': 'finalize',
            f'var_{self.w1.pk}_packed': '9',
            f'var_{self.w1.pk}_missing': '1',
            f'recover_{adv.pk}': '15',
        })
        self.assertRedirects(resp, url)
        s.refresh_from_db()
        self.assertEqual(s.status, AddaSettlement.Status.FINALIZED)
        self.assertEqual(s.expected_total, Decimal('30.00'))
        self.assertEqual(s.missing_total, 1)
        item = s.items.get(worker=self.w1)
        self.assertEqual(item.advance_recovered, Decimal('15.00'))
        # snapshot page renders frozen numbers + correction actions
        resp = self.client.get(url)
        self.assertContains(resp, 'Per-worker snapshot')
        self.assertContains(resp, 'Reverse')

    def test_reverse_post_restores_ledger(self):
        s = self._draft_with_work()
        finalize_adda_settlement(settlement=s, user=self.mgmt)
        url = reverse('expense:adda-settlement-detail', args=[s.reference])
        self.client.post(url, {'action': 'reverse', 'notes': 'wrong qty'})
        s.refresh_from_db()
        self.assertEqual(s.status, AddaSettlement.Status.REVERSED)
        bal = WorkerLedgerEntry.objects.filter(worker=self.w1)
        self.assertEqual(bal.count(), 2)                 # credit + reversal
        self.assertFalse(s.earning_lines.filter(voided_at__isnull=True).exists())

    def test_supersede_post_redirects_to_successor_draft(self):
        s = self._draft_with_work()
        finalize_adda_settlement(settlement=s, user=self.mgmt)
        url = reverse('expense:adda-settlement-detail', args=[s.reference])
        resp = self.client.post(url, {'action': 'supersede', 'notes': 'redo'})
        successor = AddaSettlement.objects.get(supersedes=s)
        self.assertRedirects(resp, reverse(
            'expense:adda-settlement-detail', args=[successor.reference]))
        # successor draft shows the correction chain
        resp = self.client.get(reverse(
            'expense:adda-settlement-detail', args=[successor.reference]))
        self.assertContains(resp, 'Correction chain')
        self.assertContains(resp, s.reference)

    def test_discard_post_deletes_draft_only(self):
        s = self._draft_with_work()
        url = reverse('expense:adda-settlement-detail', args=[s.reference])
        resp = self.client.post(url, {'action': 'discard'})
        self.assertRedirects(resp, reverse('expense:adda-settlement-list'))
        self.assertFalse(AddaSettlement.objects.filter(pk=s.pk).exists())
        # finalized settlements refuse discard
        s2 = create_draft(adda=self.adda, user=self.mgmt)
        finalize_adda_settlement(settlement=s2, user=self.mgmt)
        self.client.post(reverse(
            'expense:adda-settlement-detail', args=[s2.reference]),
            {'action': 'discard'})
        self.assertTrue(AddaSettlement.objects.filter(pk=s2.pk).exists())


class CutoverLeverTests(_Base):
    """LEDGER_CREDIT_AT_ALLOCATION — ADR-0007 lever. V2-3 PR-B: default is now
    OFF (settlement-only); True is the tested rollback path."""

    @override_settings(LEDGER_CREDIT_AT_ALLOCATION=True)
    def test_lever_on_allocation_still_credits(self):
        allocate_stage_work(user=self.mgmt, stage_record=self.sr_pay,
                            worker=self.w1, allocated_quantity=Decimal('5'))
        self.assertEqual(WorkerLedgerEntry.objects.filter(
            worker=self.w1, category='stage_earning').count(), 1)

    def test_default_is_settlement_only_allocation_refuses(self):
        # NO override — proves the shipped default refuses allocation credits.
        with self.assertRaisesMessage(ValidationError, 'Adda'):
            allocate_stage_work(user=self.mgmt, stage_record=self.sr_pay,
                                worker=self.w1, allocated_quantity=Decimal('5'))
        self.assertEqual(WorkerLedgerEntry.objects.count(), 0)

    @override_settings(LEDGER_CREDIT_AT_ALLOCATION=True)
    def test_symmetric_guard_blocks_allocation_after_settlement(self):
        self._contribute(self.w1, 10)
        self._close_stage()
        s = create_draft(adda=self.adda, user=self.mgmt)
        finalize_adda_settlement(settlement=s, user=self.mgmt)
        with self.assertRaisesMessage(ValidationError, 'already credited'):
            allocate_stage_work(user=self.mgmt, stage_record=self.sr_pay,
                                worker=self.w1, allocated_quantity=Decimal('10'))
        # reversal re-arms the path: settlement SWAs voided → allocation OK
        from expense.services.adda_settlement_service import reverse_adda_settlement
        reverse_adda_settlement(settlement=s, user=self.mgmt)
        swa = allocate_stage_work(
            user=self.mgmt, stage_record=self.sr_pay, worker=self.w1,
            allocated_quantity=Decimal('10'))
        self.assertIsNone(swa.adda_settlement_id)        # era-A marker stays NULL
