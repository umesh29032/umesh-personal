"""Expense / payroll views.

Worker-facing: a mobile "My Earnings" dashboard (own data only, never gated).
Management-facing: payroll overview (all workers), per-worker detail, advance
entry, on-demand Settlement, and worker-profile edit. All reads are scoped
through payroll_service so a worker can never see another worker's payroll.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from accounts.services import MANAGEMENT_ROLES, user_has_role
from expense.forms import AdvanceForm, SettlementForm, WorkerProfileForm
from expense.models import StageWorkAssignment, WorkerLedgerEntry, WorkerProfile
from expense.services import (
    can_view_worker, create_settlement, outstanding_advances, record_advance,
    worker_adda_earnings, worker_advances, worker_assignments, worker_ledger,
    worker_production_stats, worker_settlements, worker_stage_earnings,
    worker_summary,
)
from expense.services import payroll_service

User = get_user_model()
_ET = WorkerLedgerEntry.EntryType
_CAT = WorkerLedgerEntry.Category
_ZERO = Decimal('0.00')


class _ManagementOnly(UserPassesTestMixin):
    def test_func(self):
        return user_has_role(self.request.user, MANAGEMENT_ROLES)


def _month_start():
    return timezone.now().date().replace(day=1)


class MyEarningsView(LoginRequiredMixin, TemplateView):
    """Worker's own payroll — mobile view. Always self-scoped, never role-gated."""
    template_name = 'expense/my_earnings.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        worker = self.request.user
        ctx['summary'] = worker_summary(worker, since=_month_start())
        ctx['prod_stats'] = worker_production_stats(worker)
        ctx['stage_earnings'] = worker_stage_earnings(worker)
        ctx['adda_earnings'] = worker_adda_earnings(worker, limit=15)
        ctx['assignments'] = worker_assignments(worker, limit=8)
        ctx['settlements'] = worker_settlements(worker, limit=10)
        ctx['advances'] = worker_advances(worker, limit=10)
        ctx['is_self'] = True
        ctx['viewed_worker'] = worker
        return ctx


class WorkerPayrollDetailView(LoginRequiredMixin, TemplateView):
    """Per-worker payroll. A worker may view only themselves; management any."""
    template_name = 'expense/worker_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        worker = get_object_or_404(User, pk=self.kwargs['pk'])
        if not can_view_worker(self.request.user, worker.pk):
            raise PermissionDenied("You can only view your own payroll.")
        is_management = user_has_role(self.request.user, MANAGEMENT_ROLES)
        ctx['summary'] = worker_summary(worker, since=_month_start())
        ctx['prod_stats'] = worker_production_stats(worker)
        ctx['stage_earnings'] = worker_stage_earnings(worker)
        ctx['adda_earnings'] = worker_adda_earnings(worker)
        ctx['assignments'] = worker_assignments(worker, limit=25)
        ctx['ledger'] = worker_ledger(worker, limit=50)
        ctx['settlements'] = worker_settlements(worker, limit=25)
        ctx['advances'] = worker_advances(worker, limit=25)
        ctx['outstanding_advances'] = outstanding_advances(worker)
        ctx['profile'] = getattr(worker, 'worker_profile', None)
        ctx['viewed_worker'] = worker
        ctx['is_self'] = (self.request.user.pk == worker.pk)
        ctx['is_management'] = is_management
        return ctx


class PayrollOverviewView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """All workers with live balances — management only."""
    template_name = 'expense/payroll_overview.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Grouped ledger aggregate (payable / earnings / settled), keyed by worker.
        ledger = {
            r['worker']: r for r in
            WorkerLedgerEntry.objects.values('worker').annotate(
                credits=Sum('amount', filter=Q(entry_type=_ET.CREDIT)),
                debits=Sum('amount', filter=Q(entry_type=_ET.DEBIT)),
                reversals=Sum('amount', filter=Q(entry_type=_ET.DEBIT, category=_CAT.REVERSAL)),
                settled=Sum('amount', filter=Q(entry_type=_ET.DEBIT, category=_CAT.SETTLEMENT_PAYMENT)),
            )
        }
        # Advance outstanding = Σ given − Σ recovered (separate loan pool).
        given_map = {
            r['worker']: r['s'] for r in
            payroll_service.WorkerAdvance.objects.values('worker').annotate(s=Sum('amount'))
        }
        recovered_map = {
            r['advance__worker']: r['s'] for r in
            payroll_service.PayrollSettlementItem.objects
            .values('advance__worker').annotate(s=Sum('amount_recovered'))
        }
        pieces_map = {
            p['worker']: p['pieces'] for p in
            StageWorkAssignment.objects.filter(voided_at__isnull=True)
            .values('worker').annotate(pieces=Sum('allocated_quantity'))
        }
        worker_ids = set(ledger) | set(given_map) | set(recovered_map)
        users = {
            u.pk: u for u in
            User.objects.filter(pk__in=worker_ids).select_related('role')
        }
        workers = []
        total_payable = _ZERO
        total_advance_out = _ZERO
        for wid in worker_ids:
            lr = ledger.get(wid, {})
            credits = lr.get('credits') or _ZERO
            debits = lr.get('debits') or _ZERO
            reversals = lr.get('reversals') or _ZERO
            payable = credits - debits
            adv_out = (given_map.get(wid) or _ZERO) - (recovered_map.get(wid) or _ZERO)
            total_payable += payable
            total_advance_out += adv_out
            u = users.get(wid)
            workers.append({
                'worker': u,
                'role': u.role if u else None,
                'pieces': pieces_map.get(wid, 0),
                'total_earnings': credits - reversals,
                'advance_outstanding': adv_out,
                'total_settled': lr.get('settled') or _ZERO,
                'payable': payable,
            })
        workers.sort(key=lambda w: w['payable'], reverse=True)
        ctx['workers'] = workers
        ctx['total_payable'] = total_payable
        ctx['total_advance_out'] = total_advance_out
        return ctx


class AdvanceCreateView(LoginRequiredMixin, _ManagementOnly, FormView):
    template_name = 'expense/advance_form.html'
    form_class = AdvanceForm
    success_url = reverse_lazy('expense:payroll-overview')

    def form_valid(self, form):
        cd = form.cleaned_data
        try:
            record_advance(
                user=self.request.user, worker=cd['worker'], amount=cd['amount'],
                advance_date=cd.get('advance_date'), notes=cd.get('notes', ''),
                attachment=cd.get('attachment'),
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, getattr(exc, 'message', str(exc)))
            return self.form_invalid(form)
        messages.success(self.request, f"Advance recorded for {cd['worker']}.")
        return super().form_valid(form)


class SettlementCreateView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """Owner settles one worker, any time (the 'Start Settlement' flow).

    GET  → show pending payable + a table of outstanding advances; cash defaults
           to full payable. POST → owner sets cash + per-advance recovery → one
           atomic settlement. Per-advance recoveries are parsed from POST here
           because the rows are dynamic (one per outstanding advance).
    """
    template_name = 'expense/settlement_form.html'

    def _worker(self):
        return get_object_or_404(User, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        worker = self._worker()
        summary = worker_summary(worker)
        ctx['viewed_worker'] = worker
        ctx['summary'] = summary
        ctx['payable'] = summary['pending_payable']
        ctx['advance_outstanding'] = summary['advance_outstanding']
        ctx['outstanding_advances'] = outstanding_advances(worker)
        ctx['form'] = kwargs.get('form') or SettlementForm(
            initial={'amount_paid': summary['pending_payable']})
        ctx['today'] = timezone.now().date()
        return ctx

    def post(self, request, *args, **kwargs):
        worker = self._worker()
        form = SettlementForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        # Parse the dynamic per-advance recovery inputs: recover_<advanceId>.
        recoveries = []
        for adv in outstanding_advances(worker):
            raw = request.POST.get(f"recover_{adv['advance'].id}", '').strip()
            if not raw:
                continue
            try:
                amt = Decimal(raw)
            except (InvalidOperation, ValueError):
                messages.error(request, f"Invalid recovery amount for advance #{adv['advance'].id}.")
                return self.render_to_response(self.get_context_data(form=form))
            if amt > 0:
                recoveries.append({'advance': adv['advance'].id, 'amount': amt})

        cd = form.cleaned_data
        try:
            settlement = create_settlement(
                user=request.user, worker=worker, amount_paid=cd['amount_paid'],
                recoveries=recoveries, settlement_date=cd.get('settlement_date'),
                method=cd['method'], notes=cd.get('notes', ''),
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, getattr(exc, 'message', str(exc)))
            return self.render_to_response(self.get_context_data(form=form))
        messages.success(
            request,
            f"Settlement {settlement.reference}: paid ₹{settlement.amount_paid}, "
            f"advance recovered ₹{settlement.advance_deducted}.")
        return redirect(reverse('expense:worker-detail', args=[worker.pk]))


class WorkerProfileEditView(LoginRequiredMixin, _ManagementOnly, FormView):
    """Management edits a worker's payroll profile (bank/UPI/opening advance)."""
    template_name = 'expense/worker_profile_form.html'
    form_class = WorkerProfileForm

    def _worker(self):
        return get_object_or_404(User, pk=self.kwargs['pk'])

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        profile, _ = WorkerProfile.objects.get_or_create(user=self._worker())
        kw['instance'] = profile
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['viewed_worker'] = self._worker()
        return ctx

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Worker profile saved.")
        return redirect(reverse('expense:worker-detail', args=[self._worker().pk]))
