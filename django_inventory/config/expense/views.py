"""Expense / payroll views — EVERY money screen.

FILE MAP:
  MyEarningsView            — worker self-view (always self-scoped, never role-gated)
  PayrollOverviewView       — management all-workers board
  WorkerPayrollDetailView   — per-worker money story (mgmt or self)
  AdvanceCreateView         — loan entry
  SettlementCreateView      — CASH PAYMENT ONLY (V2-2: recovery refused here)
  WorkerProfileEditView     — bank/UPI metadata
  AddaSettlement{List,Start,Detail}View — the V2-2 settlement queue/draft/
        finalize/reverse/supersede/discard screens (PR-D)

RESPONSIBILITY: parse POST inputs (variance/recovery/verified links), gate via
_ManagementOnly, delegate to ONE service, redirect+message — views never touch
money tables. DELEGATES TO: payroll_service (ALL reads — it knows the era
rules so templates don't), adda_settlement_service, settlement_service,
ledger via those services only. INVARIANTS RELIED ON: single-writer gates
[4b/4c], era guards, recovery≤remaining — all enforced in services; the view
trusts refusals and surfaces their messages. MUST NOT ADD: any direct
WorkerLedgerEntry/SWA/Settlement write, any expected_*-as-money read
(ADR-0005), any processing_cost+earnings sum (ADR-0009).
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
from django.views.generic import TemplateView, View
from django.views.generic.edit import FormView

from accounts.services import MANAGEMENT_ROLES, user_has_role
from expense.forms import AdvanceForm, SettlementForm, WorkerProfileForm
from expense.models import StageWorkAssignment, WorkerLedgerEntry, WorkerProfile
from expense.services import (
    can_view_worker, create_settlement, outstanding_advances, record_advance,
    unsettled_expected,
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
        ctx['unsettled_expected'] = unsettled_expected(worker)
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
        ctx['unsettled_expected'] = unsettled_expected(worker)
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

        # V2-2: recovery RE-HOMED to AddaSettlement.finalize — this screen is
        # PAYMENT-ONLY. Stray recover_* inputs (stale tab) are refused loudly.
        if any(k.startswith('recover_') and str(v).strip()
               for k, v in request.POST.items()):
            messages.error(
                request,
                "Advance recovery now happens when you settle the Adda — this "
                "screen only pays cash. Settle the Adda first.")
            return self.render_to_response(self.get_context_data(form=form))

        cd = form.cleaned_data
        try:
            settlement = create_settlement(
                user=request.user, worker=worker, amount_paid=cd['amount_paid'],
                settlement_date=cd.get('settlement_date'),
                method=cd['method'], notes=cd.get('notes', ''),
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, getattr(exc, 'message', str(exc)))
            return self.render_to_response(self.get_context_data(form=form))
        messages.success(
            request,
            f"Payment {settlement.reference}: paid ₹{settlement.amount_paid}.")
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


# ─── V2-2 PR-D: Adda Settlement screens (management-only) ────────────────────
# All writes go through adda_settlement_service (single-writer); these views
# only parse POST inputs and render service output.

class AddaSettlementListView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """Pending queue (ready / waiting Addas) + settlement history."""
    template_name = 'expense/adda_settlement_list.html'

    def get_context_data(self, **kwargs):
        from expense.models import AddaSettlement
        from expense.services import adda_settlement_service as adst
        ctx = super().get_context_data(**kwargs)
        ctx['queue'] = adst.settlement_queue()
        ctx['settlements'] = (
            AddaSettlement.objects
            .select_related('adda', 'settled_by', 'supersedes')
            .order_by('-id')[:50])
        return ctx


class AddaSettlementStartView(LoginRequiredMixin, _ManagementOnly, View):
    """POST-only: open (or resume) the draft for one Adda.

    Base is `View` (not `TemplateView`): the action has no GET surface, so a
    stray GET (bookmark/refresh/back) returns 405 — never the 500 that a
    template-less `TemplateView.get()` raised (P0-1)."""

    def post(self, request, adda_pk):
        from production.models import Adda
        from expense.models import AddaSettlement
        from expense.services import adda_settlement_service as adst
        adda = get_object_or_404(Adda, pk=adda_pk)
        existing = AddaSettlement.objects.filter(
            adda=adda, status=AddaSettlement.Status.DRAFT).first()
        if existing:
            messages.info(request, f"Resuming open draft {existing.reference}.")
            return redirect(reverse('expense:adda-settlement-detail',
                                    args=[existing.reference]))
        try:
            settlement = adst.create_draft(adda=adda, user=request.user)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, getattr(exc, 'message', str(exc)))
            return redirect(reverse('expense:adda-settlement-list'))
        messages.success(request, f"Draft {settlement.reference} opened for {adda.code}.")
        return redirect(reverse('expense:adda-settlement-detail',
                                args=[settlement.reference]))


class AddaSettlementDetailView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """Draft: labeled preview (settleable / era-A skipped / era-B skipped) +
    variance + per-advance recovery inputs + Finalize/Discard. Finalized:
    frozen snapshot + Reverse / Reverse&Supersede. Reversed/Superseded:
    read-only snapshot + chain links."""
    template_name = 'expense/adda_settlement_detail.html'

    def _settlement(self):
        from expense.models import AddaSettlement
        return get_object_or_404(
            AddaSettlement.objects.select_related(
                'adda__product', 'settled_by', 'reversed_by', 'supersedes'),
            reference=self.kwargs['reference'])

    @staticmethod
    def _line_dict(c):
        qty = c.verified_quantity if c.verified_quantity is not None else c.reported_quantity
        rate = c.expected_rate or _ZERO
        return {
            'contribution': c,
            'stage': c.task.stage_record.workflow_stage.stage.name,
            'color': c.color, 'size': c.size,
            'qty': qty, 'verified': c.verified_quantity is not None,
            'rate': rate, 'amount': (qty * rate).quantize(Decimal('0.01')),
        }

    def _chain(self, settlement):
        """Ordered supersede chain (oldest → newest) around this settlement."""
        first = settlement
        while first.supersedes_id:
            first = first.supersedes
        chain, node = [], first
        while node:
            chain.append(node)
            node = node.superseded_by.first()
        return chain if len(chain) > 1 else []

    def get_context_data(self, **kwargs):
        from expense.models import AddaSettlement
        from expense.services import adda_settlement_service as adst
        ctx = super().get_context_data(**kwargs)
        s = ctx['s'] = self._settlement()
        ctx['chain'] = self._chain(s)
        if s.status == AddaSettlement.Status.DRAFT:
            lines, skip_a, skip_b = adst.preview_lines(s)
            by_worker = {}
            for c in lines:
                w = by_worker.setdefault(c.task.worker_id, {
                    'worker': c.task.worker, 'lines': [], 'expected': _ZERO})
                d = self._line_dict(c)
                w['lines'].append(d)
                w['expected'] += d['amount']
            for w in by_worker.values():
                w['advances'] = outstanding_advances(w['worker'])
            ctx['workers'] = sorted(by_worker.values(),
                                    key=lambda w: w['worker'].pk)
            ctx['grand_expected'] = sum(
                (w['expected'] for w in by_worker.values()), _ZERO)
            ctx['skip_a'] = [self._line_dict(c) for c in skip_a]
            ctx['skip_b'] = [self._line_dict(c) for c in skip_b]
        else:
            ctx['items'] = s.items.select_related('worker').order_by('worker_id')
            ctx['recoveries'] = (s.recovery_lines
                                 .select_related('advance', 'advance__worker')
                                 .order_by('id'))
        return ctx

    # ── POST actions: finalize / reverse / supersede / discard ──────────────
    def post(self, request, *args, **kwargs):
        from expense.services import adda_settlement_service as adst
        s = self._settlement()
        action = request.POST.get('action', '')
        try:
            if action == 'finalize':
                variance, recoveries = self._parse_finalize_inputs(request)
                adst.finalize_adda_settlement(
                    settlement=s, user=request.user,
                    variance=variance, recoveries=recoveries)
                messages.success(request, f"{s.reference} finalized — earnings booked.")
            elif action in ('reverse', 'supersede'):
                notes = request.POST.get('notes', '').strip()
                _, successor = adst.reverse_adda_settlement(
                    settlement=s, user=request.user,
                    supersede=(action == 'supersede'), notes=notes)
                if successor:
                    messages.success(
                        request,
                        f"{s.reference} superseded — continue in draft {successor.reference}.")
                    return redirect(reverse('expense:adda-settlement-detail',
                                            args=[successor.reference]))
                messages.success(request, f"{s.reference} reversed — ledger restored.")
            elif action == 'discard':
                adst.discard_draft(settlement=s, user=request.user)
                messages.success(request, f"Draft {s.reference} discarded.")
                return redirect(reverse('expense:adda-settlement-list'))
            else:
                messages.error(request, "Unknown action.")
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, getattr(exc, 'message', str(exc)))
        return redirect(reverse('expense:adda-settlement-detail', args=[s.reference]))

    @staticmethod
    def _parse_finalize_inputs(request):
        """variance: var_<workerId>_<field> (ints); recoveries: recover_<advId>
        (decimals). Blank/zero inputs are simply omitted."""
        variance, recoveries = {}, {}
        for key, raw in request.POST.items():
            raw = raw.strip()
            if not raw:
                continue
            if key.startswith('var_'):
                try:
                    _, wid, field = key.split('_', 2)
                    val = int(raw)
                except ValueError:
                    raise ValidationError(f"Invalid variance value for {key}.")
                if field not in ('packed', 'missing', 'rejected', 'alter') or val < 0:
                    raise ValidationError(f"Invalid variance input {key}.")
                if val:
                    variance.setdefault(int(wid), {})[field] = val
            elif key.startswith('recover_'):
                try:
                    amt = Decimal(raw)
                except InvalidOperation:
                    raise ValidationError(f"Invalid recovery amount for {key}.")
                if amt > 0:
                    recoveries[int(key.split('_', 1)[1])] = amt
        return variance, recoveries
