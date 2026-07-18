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
from expense.forms import (
    AdvanceForm, FactoryExpenseForm, SettlementForm, WorkerProfileForm,
)
from expense.models import StageWorkAssignment, WorkerLedgerEntry, WorkerProfile
from expense.services import (
    can_view_worker, create_settlement, is_monthly, outstanding_advances,
    record_advance, set_pay_basis, unsettled_contribution_count,
    unsettled_expected,
    worker_adda_earnings, worker_advances, worker_assignments, worker_ledger,
    worker_production_stats, worker_settlements, worker_stage_earnings,
    worker_summary,
)
from expense.services import payroll_service
from expense.services.settlement_resolver import settlement_quantity

User = get_user_model()
_ET = WorkerLedgerEntry.EntryType
_CAT = WorkerLedgerEntry.Category
_ZERO = Decimal('0.00')


class _ManagementOnly(UserPassesTestMixin):
    def test_func(self):
        return user_has_role(self.request.user, MANAGEMENT_ROLES)


class _WorkerFromPk:
    """Shared `pk → worker` lookup for the per-worker management pages."""
    def _worker(self):
        return get_object_or_404(User, pk=self.kwargs['pk'])


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
        # R4 (PDD §27-D4 clause 3): monthly worker sees quantities but NO ₹
        # expectation (suppressed entirely, not ₹0.00 — owner P-4).
        ctx['is_monthly'] = is_monthly(worker)
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
        ctx['is_monthly'] = is_monthly(worker)          # R4 — same P-4 rule
        # R7: F&F entry — button gated to super-admin (service re-validates).
        from accounts.services import ROLE_SUPER_ADMIN
        ctx['is_super_admin'] = user_has_role(self.request.user,
                                              [ROLE_SUPER_ADMIN])
        return ctx


class PayrollOverviewView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """All workers with live balances — management only."""
    template_name = 'expense/payroll_overview.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Grouped ledger aggregate keyed by worker. PA-12-C: mirror worker_summary's
        # netting EXACTLY so the overview agrees with each worker's own page — earnings
        # = EARNING-category credits net of earning reversals (NOT all-credits − all-
        # reversals, which wrongly counted a CREDIT/REVERSAL from a reversed recovery/
        # payment as earnings); settled = SETTLEMENT_PAYMENT debits net of their reversals.
        _EARN = (_CAT.STAGE_EARNING, _CAT.PRODUCTION_EARNING)
        ledger = {
            r['worker']: r for r in
            WorkerLedgerEntry.objects.values('worker').annotate(
                credits=Sum('amount', filter=Q(entry_type=_ET.CREDIT)),
                debits=Sum('amount', filter=Q(entry_type=_ET.DEBIT)),
                earned=Sum('amount', filter=Q(entry_type=_ET.CREDIT, category__in=_EARN)),
                earned_reversed=Sum('amount', filter=Q(
                    category=_CAT.REVERSAL, reverses__category__in=_EARN)),
                settled=Sum('amount', filter=Q(entry_type=_ET.DEBIT, category=_CAT.SETTLEMENT_PAYMENT)),
                settled_reversed=Sum('amount', filter=Q(
                    category=_CAT.REVERSAL, reverses__category=_CAT.SETTLEMENT_PAYMENT)),
            )
        }
        # Advance outstanding = Σ given − Σ recovered (separate loan pool).
        given_map = {
            r['worker']: r['s'] for r in
            payroll_service.WorkerAdvance.objects.values('worker').annotate(s=Sum('amount'))
        }
        recovered_map = {
            r['advance__worker']: r['s'] for r in
            # PA-12-B: exclude REVERSED recoveries (reversed_at set), like advance_outstanding
            # — else a reversed settlement's recovery understates advance_outstanding here.
            payroll_service.PayrollSettlementItem.objects.filter(reversed_at__isnull=True)
            .values('advance__worker').annotate(s=Sum('amount_recovered'))
        }
        pieces_map = {
            p['worker']: p['pieces'] for p in
            StageWorkAssignment.objects.filter(voided_at__isnull=True)
            .values('worker').annotate(pieces=Sum('allocated_quantity'))
        }
        # M-4 (hostile review 2026-07-05): MONTHLY workers are payroll-relevant
        # even with zero money history — management must always see who is on
        # a monthly basis. Roster = money-history workers ∪ monthly workers;
        # each row carries is_monthly for the badge (and to hide Settle —
        # their pay never flows through settlement, ADR-0011/R4).
        monthly_ids = set(
            WorkerProfile.objects
            .filter(pay_basis=WorkerProfile.PayBasis.MONTHLY,
                    user__is_active=True)
            .values_list('user_id', flat=True))
        worker_ids = set(ledger) | set(given_map) | set(recovered_map) | monthly_ids
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
            payable = credits - debits
            adv_out = (given_map.get(wid) or _ZERO) - (recovered_map.get(wid) or _ZERO)
            total_payable += payable
            total_advance_out += adv_out
            u = users.get(wid)
            workers.append({
                'worker': u,
                'role': u.role if u else None,
                'is_monthly': wid in monthly_ids,
                'pieces': pieces_map.get(wid, 0),
                # PA-12-C: net of earning reversals only (matches worker_summary), not
                # all-credits − all-reversals.
                'total_earnings': (lr.get('earned') or _ZERO) - (lr.get('earned_reversed') or _ZERO),
                'advance_outstanding': adv_out,
                'total_settled': (lr.get('settled') or _ZERO) - (lr.get('settled_reversed') or _ZERO),
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


class SettlementCreateView(LoginRequiredMixin, _ManagementOnly, _WorkerFromPk, TemplateView):
    """Owner settles one worker, any time (the 'Start Settlement' flow).

    GET  → show pending payable + a table of outstanding advances; cash defaults
           to full payable. POST → owner sets cash + per-advance recovery → one
           atomic settlement. Per-advance recoveries are parsed from POST here
           because the rows are dynamic (one per outstanding advance).
    """
    template_name = 'expense/settlement_form.html'


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


class WorkerProfileEditView(LoginRequiredMixin, _ManagementOnly, _WorkerFromPk, FormView):
    """Management edits a worker's payroll profile (bank/UPI/opening advance)."""
    template_name = 'expense/worker_profile_form.html'
    form_class = WorkerProfileForm


    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        profile, _ = WorkerProfile.objects.get_or_create(user=self._worker())
        kw['instance'] = profile
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        worker = self._worker()
        ctx['viewed_worker'] = worker
        # R4: the pay-basis control — visible read-only to managers, editable
        # only by super-admin (owner P-2); server re-validates in the service.
        from accounts.services import ROLE_SUPER_ADMIN
        profile, _ = WorkerProfile.objects.get_or_create(user=worker)
        ctx['pay_basis'] = profile.pay_basis
        ctx['pay_basis_choices'] = WorkerProfile.PayBasis.choices
        ctx['is_super_admin'] = user_has_role(self.request.user, [ROLE_SUPER_ADMIN])
        # Owner R4 addendum: unsettled lines ⇒ the change needs an explicit
        # confirmation — surface the count so the warning can be concrete.
        ctx['pay_basis_unsettled'] = unsettled_contribution_count(worker)
        return ctx

    def form_valid(self, form):
        # RCP-1A F3: opening_advance is a displayed ₹ figure (WP-A informational)
        # — the write still goes through THE payroll_service chokepoint
        # (guards + audit log), never a bare form.save().
        try:
            payroll_service.update_payout_profile(
                self._worker(), actor=self.request.user, **form.cleaned_data)
        except ValidationError as exc:
            messages.error(self.request, getattr(exc, 'message', str(exc)))
            return self.render_to_response(self.get_context_data(form=form))
        messages.success(self.request, "Worker profile saved.")
        return redirect(reverse('expense:worker-detail', args=[self._worker().pk]))


class WorkerPayBasisUpdateView(LoginRequiredMixin, _ManagementOnly, View):
    """R4 (PDD §27-D4): change a worker's pay basis. Parse POST → delegate to
    `payroll_service.set_pay_basis`, which owns EVERY guard (super-admin P-2,
    unsettled-lines confirmation, audit row) — never trust the form."""

    def post(self, request, pk):
        worker = get_object_or_404(User, pk=pk)
        basis = request.POST.get('pay_basis', '')
        confirmed = bool(request.POST.get('confirm_unsettled'))
        try:
            profile = set_pay_basis(worker, basis, actor=request.user,
                                    confirmed=confirmed)
            messages.success(
                request,
                f"Pay basis for {worker.get_full_name() or worker.email} "
                f"changed to {profile.get_pay_basis_display()}.")
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, getattr(exc, 'message', str(exc)))
        return redirect(reverse('expense:worker-profile', args=[worker.pk]))


# ─── R7 (PDD §20 / §27-D5): Full & Final settlement — orchestration UI ───────

class WorkerFnFView(LoginRequiredMixin, _ManagementOnly, _WorkerFromPk, TemplateView):
    """Guided exit flow: checklist (GET) + execute (POST). The view renders
    and parses ONLY — fnf_service owns every guard (super-admin P-4, open-task
    and draft-gate refusals, write-off reason). No new money writer: fnf
    orchestrates the existing settlement/payment/PSI chokepoints."""
    template_name = 'expense/worker_fnf.html'


    def get_context_data(self, **kwargs):
        from expense.services import fnf_preview
        from accounts.services import ROLE_SUPER_ADMIN
        ctx = super().get_context_data(**kwargs)
        worker = self._worker()
        ctx['viewed_worker'] = worker
        ctx['is_super_admin'] = user_has_role(self.request.user,
                                              [ROLE_SUPER_ADMIN])
        if ctx['is_super_admin']:
            ctx['pv'] = fnf_preview(worker, user=self.request.user)
        return ctx

    def post(self, request, pk):
        from expense.services import fnf_execute
        worker = self._worker()
        try:
            receipt = fnf_execute(
                worker, user=request.user,
                write_off_reason=request.POST.get('write_off_reason', ''))
            messages.success(
                request,
                f"Full & Final complete for "
                f"{worker.get_full_name() or worker.email}: "
                f"{len(receipt['settlements'])} settlement(s), "
                f"₹{receipt['paid']} paid, "
                f"{receipt['write_offs']} advance write-off(s). "
                "Account deactivated — history preserved.")
            return redirect(reverse('expense:worker-detail', args=[worker.pk]))
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, getattr(exc, 'message', str(exc)))
            return redirect(reverse('expense:worker-fnf', args=[worker.pk]))


# ─── R5 (PDD §21 / ADR-0011): Factory expenses — factory-level cost records ──
# NOT a ledger: these views/services never touch WorkerLedgerEntry or costing.

def _parse_month(request):
    """?month=YYYY-MM, strict parse, garbage → current month (never 500).
    MEE-C: promoted from FactoryExpenseListView._month (INERT — same code) so
    the recurring-expense pages reuse THE one parser instead of a copy."""
    raw = request.GET.get('month', '')
    try:
        year, month = int(raw[:4]), int(raw[5:7])
        if raw[4] != '-' or not 1 <= month <= 12:
            raise ValueError
        return year, month
    except (ValueError, IndexError):
        today = timezone.now().date()
        return today.year, today.month


class FactoryExpenseListView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """Month-scoped list + per-category totals. POST = void (super-admin +
    mandatory reason — enforced by expense_service, never trusted to the UI).
    Voided rows stay visible (struck-through) — nothing disappears."""
    template_name = 'expense/factory_expense_list.html'

    def _month(self):
        return _parse_month(self.request)

    def get_context_data(self, **kwargs):
        from expense.models import FactoryExpense
        from expense.services import expense_service
        from accounts.services import ROLE_SUPER_ADMIN
        ctx = super().get_context_data(**kwargs)
        year, month = self._month()
        ctx['year'], ctx['month'] = year, month
        ctx['month_value'] = f"{year:04d}-{month:02d}"
        ctx['expenses'] = (
            FactoryExpense.objects
            .filter(expense_date__year=year, expense_date__month=month)
            .select_related('entered_by', 'worker', 'voided_by')
        )
        ctx['totals'] = expense_service.monthly_totals(year, month)
        ctx['is_super_admin'] = user_has_role(self.request.user,
                                              [ROLE_SUPER_ADMIN])
        return ctx

    def post(self, request, *args, **kwargs):
        from expense.models import FactoryExpense
        from expense.services import void_expense
        expense = get_object_or_404(FactoryExpense,
                                    pk=request.POST.get('expense_id'))
        try:
            void_expense(expense, actor=request.user,
                         reason=request.POST.get('void_reason', ''))
            messages.success(request, "Expense voided.")
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, getattr(exc, 'message', str(exc)))
        month = request.POST.get('month', '')
        url = reverse('expense:factory-expense-list')
        return redirect(f"{url}?month={month}" if month else url)


class FactoryExpenseCreateView(LoginRequiredMixin, _ManagementOnly, FormView):
    """Entry form (mobile-first). Delegates to expense_service.record_expense
    — the salary⇒worker rule and every other guard live there."""
    template_name = 'expense/factory_expense_form.html'
    form_class = FactoryExpenseForm
    success_url = reverse_lazy('expense:factory-expense-list')

    def form_valid(self, form):
        from expense.services import record_expense
        cd = form.cleaned_data
        try:
            record_expense(
                category=cd['category'], amount=cd['amount'],
                expense_date=cd['expense_date'], notes=cd.get('notes', ''),
                worker=cd.get('worker'), actor=self.request.user,
                confirmed_duplicate=bool(
                    self.request.POST.get('confirm_duplicate')))
        except (ValidationError, PermissionDenied) as exc:
            # M-3: the duplicate-salary refusal re-renders WITH the confirm
            # checkbox — warn-and-confirm, the service stays the enforcer.
            if getattr(exc, 'code', None) == 'duplicate_salary':
                self.duplicate_warning = getattr(exc, 'message', str(exc))
            messages.error(self.request, getattr(exc, 'message', str(exc)))
            return self.form_invalid(form)
        messages.success(self.request, "Expense recorded.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['duplicate_warning'] = getattr(self, 'duplicate_warning', None)
        # L-3 (hostile review): accounts.User.salary = the agreed reference
        # salary (informational field on the user forms, no money-code
        # consumers). Repurposed as a CONVENIENCE prefill for salary entries —
        # display-only sugar; the recorded amount is whatever is submitted.
        # Management-only page, same audience as the user edit form (no leak).
        ctx['worker_salaries'] = {
            str(pk): str(sal) for pk, sal in
            User.objects.filter(is_active=True, salary__isnull=False)
                        .values_list('pk', 'salary')
        }
        return ctx


# ─── MEE-C: Monthly Expense Engine surfaces (management-only) ────────────────
# THIN by contract: every write goes through the MEE-B expense_service
# functions (census ADDENDUM 1); these views parse inputs, call ONE service,
# message + redirect. View gates management; the SERVICE enforces SA on the
# levers (the pay-basis/void house pattern).

class ExpenseTemplateListView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """Template register + each template's CURRENT-period status (straight
    from the SAME preview path generation uses — no second status logic).
    POST actions (SA, service-enforced): deactivate · change_amount."""
    template_name = 'expense/expense_template_list.html'

    def get_context_data(self, **kwargs):
        from expense.models import ExpenseTemplate
        from expense.services.expense_service import generate_monthly_expenses
        from accounts.services import ROLE_SUPER_ADMIN
        ctx = super().get_context_data(**kwargs)
        year, month = _parse_month(self.request)
        ctx['year'], ctx['month'] = year, month
        ctx['month_value'] = f"{year:04d}-{month:02d}"
        # Status per template = the preview receipt (confirm=False = pure read).
        receipt = generate_monthly_expenses(year, month,
                                            actor=self.request.user)
        status = {row['template'].pk: "Pending generation"
                  for row in receipt['to_create']}
        status.update({t.pk: why for t, why in receipt['skipped']})
        templates = list(ExpenseTemplate.objects
                         .select_related('worker', 'created_by')
                         .order_by('-is_active', 'category', 'label'))
        ctx['rows'] = [{'t': t, 'status': status.get(t.pk, "—")}
                       for t in templates]
        ctx['is_super_admin'] = user_has_role(self.request.user,
                                              [ROLE_SUPER_ADMIN])
        return ctx

    def post(self, request, *args, **kwargs):
        from expense.models import ExpenseTemplate
        from expense.services.expense_service import (
            change_template_amount, deactivate_expense_template)
        template = get_object_or_404(ExpenseTemplate,
                                     pk=request.POST.get('template_id'))
        action = request.POST.get('action')
        try:
            if action == 'deactivate':
                deactivate_expense_template(template, actor=request.user)
                messages.success(request, f"Template “{template.label}” deactivated.")
            elif action == 'change_amount':
                change_template_amount(
                    template, new_amount=request.POST.get('new_amount', ''),
                    reason=request.POST.get('reason', ''), actor=request.user)
                messages.success(request, f"Amount updated for “{template.label}” (audited).")
            else:
                messages.error(request, "Unknown action.")
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, getattr(exc, 'message', str(exc)))
        month = request.POST.get('month', '')
        url = reverse('expense:expense-template-list')
        return redirect(f"{url}?month={month}" if month else url)


class ExpenseTemplateCreateView(LoginRequiredMixin, _ManagementOnly, FormView):
    """Template entry (mobile-first, form-shell canon). Delegates to
    expense_service.create_expense_template — SA gate + every rule live there."""
    template_name = 'expense/expense_template_form.html'
    form_class = None  # set in get_form_class (lazy import, house style)
    success_url = reverse_lazy('expense:expense-template-list')

    def get_form_class(self):
        from expense.forms import ExpenseTemplateForm
        return ExpenseTemplateForm

    def form_valid(self, form):
        from expense.services.expense_service import create_expense_template
        cd = form.cleaned_data
        try:
            create_expense_template(
                label=cd['label'], category=cd['category'],
                amount=cd['amount'], worker=cd.get('worker'),
                start_date=cd['start_date'], end_date=cd.get('end_date'),
                notes=cd.get('notes', ''), actor=self.request.user)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, getattr(exc, 'message', str(exc)))
            return self.form_invalid(form)
        messages.success(self.request, "Recurring template created.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Same L-3 prefill sugar as the manual expense form (one audience).
        ctx['worker_salaries'] = {
            str(pk): str(sal) for pk, sal in
            User.objects.filter(is_active=True, salary__isnull=False)
                        .values_list('pk', 'salary')
        }
        return ctx


class GenerateExpensesView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """Preview → confirm for one month (THE single service path both ways:
    GET renders confirm=False; POST confirm runs confirm=True). SA-only
    regenerate action for voided-covered periods (service-enforced)."""
    template_name = 'expense/generate_expenses.html'

    def get_context_data(self, **kwargs):
        from expense.services.expense_service import generate_monthly_expenses
        ctx = super().get_context_data(**kwargs)
        year, month = _parse_month(self.request)
        ctx['year'], ctx['month'] = year, month
        ctx['month_value'] = f"{year:04d}-{month:02d}"
        receipt = generate_monthly_expenses(year, month,
                                            actor=self.request.user)
        ctx['receipt'] = receipt
        # Presentation only: which skipped rows carry the voided-regenerate hint.
        ctx['skipped_rows'] = [
            {'t': t, 'why': why, 'regen': 'regenerate explicitly' in why}
            for t, why in receipt['skipped']]
        return ctx

    def post(self, request, *args, **kwargs):
        from expense.models import ExpenseTemplate
        from expense.services.expense_service import (
            generate_monthly_expenses, regenerate_period)
        year, month = _parse_month(self.request)
        month_value = f"{year:04d}-{month:02d}"
        try:
            if request.POST.get('action') == 'regenerate':
                template = get_object_or_404(
                    ExpenseTemplate, pk=request.POST.get('template_id'))
                regenerate_period(template, year=year, month=month,
                                  reason=request.POST.get('reason', ''),
                                  actor=request.user)
                messages.success(
                    request, f"Regenerated “{template.label}” for {month_value}.")
            else:
                receipt = generate_monthly_expenses(
                    year, month, actor=request.user, confirm=True)
                messages.success(
                    request,
                    f"Generated {len(receipt['created'])} expense(s) for "
                    f"{month_value}; skipped {len(receipt['skipped'])}.")
                return redirect(
                    f"{reverse('expense:factory-expense-list')}?month={month_value}")
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, getattr(exc, 'message', str(exc)))
        return redirect(
            f"{reverse('expense:expense-generate')}?month={month_value}")


# ─── RMX-D (Phase 17): Material Spend — the read-only WINDOW over the
# certified RMX-C period reads (charter = PDD entry 8; D2 permanent rule:
# aggregates management-visible; per-roll economics stay walled elsewhere).
# THIN by contract: parse month → TWO service calls → context. Zero math,
# zero ORM, zero writes, zero POST routes.

class MaterialSpendView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """Consumption (PRIMARY) + Purchases (secondary), both basis-labelled;
    honest-NULL banners; never blended with FactoryExpense (sibling link only
    — ADR-0011)."""
    template_name = 'expense/material_spend.html'
    http_method_names = ['get', 'head', 'options']   # read-only by shape

    def get_context_data(self, **kwargs):
        from production.services.cost_service import material_consumption_in_period
        from raw_materials.services.roll_service import material_purchases_in_period
        ctx = super().get_context_data(**kwargs)
        year, month = _parse_month(self.request)
        ctx['year'], ctx['month'] = year, month
        ctx['month_value'] = f"{year:04d}-{month:02d}"
        ctx['consumption'] = material_consumption_in_period(year, month)
        ctx['purchases'] = material_purchases_in_period(year, month)
        return ctx


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
    """Draft: labeled preview (settleable / era-A skipped / era-B skipped /
    monthly excluded, R4) + variance + per-advance recovery inputs +
    Finalize/Discard. Finalized:
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
        from production.services import cost_service
        qty = settlement_quantity(c)               # resolver (S1) — default = verified ?? reported
        # PA-11-2: grouped→0 structural guard, mirroring the finalize money-write — a stage
        # grouped after completion has a stale non-zero frozen expected_rate; the preview
        # must show the 0 that finalize will actually book, not the raw frozen rate.
        rate = cost_service.effective_pay_rate(
            c.task.stage_record.workflow_stage, c.expected_rate or _ZERO)
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
        # S5: super-admin gets the audited reconciliation-override field on the finalize form.
        from accounts.services import ROLE_SUPER_ADMIN, user_has_role
        ctx['is_super_admin'] = user_has_role(self.request.user, [ROLE_SUPER_ADMIN])
        if s.status == AddaSettlement.Status.DRAFT:
            lines, skip_a, skip_b, skip_monthly = adst.preview_lines(s)
            by_worker = {}
            for c in lines:
                w = by_worker.setdefault(c.task.worker_id, {
                    'worker': c.task.worker, 'lines': [], 'expected': _ZERO})
                d = self._line_dict(c)
                w['lines'].append(d)
                w['expected'] += d['amount']
            # PA-16-2: batch outstanding advances for ALL draft workers in 2
            # queries (was outstanding_advances() per worker = an N+1 over workers).
            adv_by_worker = payroll_service.outstanding_advances_bulk(
                [w['worker'] for w in by_worker.values()])
            for wid, w in by_worker.items():
                w['advances'] = adv_by_worker.get(wid, [])
            ctx['workers'] = sorted(by_worker.values(),
                                    key=lambda w: w['worker'].pk)
            ctx['grand_expected'] = sum(
                (w['expected'] for w in by_worker.values()), _ZERO)
            ctx['skip_a'] = [self._line_dict(c) for c in skip_a]
            ctx['skip_b'] = [self._line_dict(c) for c in skip_b]
            # R4: monthly workers' lines — excluded from settlement (D4);
            # labeled so the admin SEES what won't pay before finalizing.
            ctx['skip_monthly'] = [self._line_dict(c) for c in skip_monthly]
        else:
            ctx['items'] = s.items.select_related('worker').order_by('worker_id')
            ctx['recoveries'] = (s.recovery_lines
                                 .select_related('advance', 'advance__worker')
                                 .order_by('id'))
        # M-6 reconciliation (WARN, S1.1 / D-β + H1): surface stages where settled
        # qty exceeds recorded output (the B-1 leak) on the settlement detail. Live
        # recompute shows CURRENT state; scoped to over_allocated only (H1 — the
        # other HARD_FLAGS were noise). The persisted evidence (written at finalize)
        # is the soak's historical record; this banner is the live view.
        from expense.services import reconciliation_service as _recon
        ctx['reconciliation_warnings'] = [
            r for r in _recon.reconcile_stage_pay(adda=s.adda)
            if r['flag'] in _recon.SETTLEMENT_WARN_FLAGS
        ]
        return ctx

    # ── POST actions: finalize / reverse / supersede / discard ──────────────
    def post(self, request, *args, **kwargs):
        from expense.services import adda_settlement_service as adst
        s = self._settlement()
        action = request.POST.get('action', '')
        try:
            if action == 'finalize':
                variance, recoveries = self._parse_finalize_inputs(request)
                # S5: optional super-admin audited override of an M-6 over-allocation block.
                override = request.POST.get('reconciliation_override', '').strip() or None
                adst.finalize_adda_settlement(
                    settlement=s, user=request.user,
                    variance=variance, recoveries=recoveries,
                    reconciliation_override=override)
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
                # PA-05B-1: int(wid) must be INSIDE the try — a tampered key like
                # 'var_abc_packed' otherwise raises an unhandled ValueError → 500.
                try:
                    _, wid, field = key.split('_', 2)
                    wid = int(wid)
                    val = int(raw)
                except ValueError:
                    raise ValidationError(f"Invalid variance value for {key}.")
                if field not in ('packed', 'missing', 'rejected', 'alter') or val < 0:
                    raise ValidationError(f"Invalid variance input {key}.")
                if val:
                    variance.setdefault(wid, {})[field] = val
            elif key.startswith('recover_'):
                # PA-05B-1: int(advance_id) must be INSIDE the try too — 'recover_abc'
                # otherwise raises an unhandled ValueError → 500.
                try:
                    adv_id = int(key.split('_', 1)[1])
                    amt = Decimal(raw)
                except (ValueError, InvalidOperation):
                    raise ValidationError(f"Invalid recovery amount for {key}.")
                if amt > 0:
                    recoveries[adv_id] = amt
        return variance, recoveries
