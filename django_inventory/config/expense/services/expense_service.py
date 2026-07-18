"""FactoryExpense service — the SOLE writer of FactoryExpense (R5, PDD §21).

Append-only posture: `record_expense` creates, `void_expense` soft-voids with
a mandatory audited reason. NO edit function exists — do not add one.

🔒 ADR-0011: expenses (incl. monthly salaries) are FACTORY-LEVEL cost records.
This module must NEVER import or write ledger/settlement/costing state — no
WorkerLedgerEntry, no SWA, no processing_cost. The `worker` link on salary
rows is audit-only.
"""
from __future__ import annotations

import logging
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from accounts.services import MANAGEMENT_ROLES, user_has_role
from expense.models import FactoryExpense

logger = logging.getLogger(__name__)

_ZERO = Decimal('0.00')


@transaction.atomic
def record_expense(*, category, amount, expense_date, actor, notes='',
                   worker=None, confirmed_duplicate=False) -> FactoryExpense:
    """Create one expense row. Management-gated (P-2).

    P-1 (owner): `category=salary` REQUIRES a worker (audit: whose salary);
    every other category REFUSES one (the link means salary, nothing else).
    M-3 (owner, hostile review 2026-07-05): a second non-voided salary row for
    the same worker + calendar month needs `confirmed_duplicate=True` — a
    WARN-and-confirm, never a hard block (corrections / multiple salary
    components are legitimate). Server-enforced; the UI checkbox is sugar.
    """
    if not user_has_role(actor, MANAGEMENT_ROLES):
        raise PermissionDenied("Only management can record factory expenses.")
    if category not in FactoryExpense.Category.values:
        raise ValidationError("Unknown expense category.")
    try:
        amount = Decimal(str(amount))
    except Exception:
        raise ValidationError("Amount must be a number.")
    if amount <= 0:
        raise ValidationError("Amount must be greater than zero.")
    if expense_date is None:
        raise ValidationError("Expense date is required.")
    if category == FactoryExpense.Category.SALARY and worker is None:
        raise ValidationError("A salary expense must name the worker it pays.")
    if category != FactoryExpense.Category.SALARY and worker is not None:
        raise ValidationError(
            "Only salary expenses may be linked to a worker.")
    if category == FactoryExpense.Category.SALARY and not confirmed_duplicate:
        dup = FactoryExpense.objects.filter(
            category=FactoryExpense.Category.SALARY, worker=worker,
            voided_at__isnull=True,
            expense_date__year=expense_date.year,
            expense_date__month=expense_date.month,
        ).aggregate(n=Count('id'), total=Sum('amount'))
        if dup['n']:
            raise ValidationError(
                f"{worker.get_full_name() or worker.email} already has "
                f"{dup['n']} salary entr{'y' if dup['n'] == 1 else 'ies'} "
                f"totalling ₹{dup['total']} for "
                f"{expense_date.year:04d}-{expense_date.month:02d}. "
                "Tick the confirmation to record another (corrections or "
                "extra salary components are allowed).",
                code='duplicate_salary')
    expense = FactoryExpense.objects.create(
        category=category, amount=amount, expense_date=expense_date,
        notes=notes, entered_by=actor, worker=worker)
    logger.info("factory_expense.record id=%s cat=%s amount=%s by=%s worker=%s",
                expense.pk, category, amount, actor.pk,
                getattr(worker, 'pk', None))
    return expense


@transaction.atomic
def void_expense(expense, *, actor, reason) -> FactoryExpense:
    """Soft-void (the ONLY correction path — rows are never edited/deleted).
    Super-admin only + mandatory reason (P-2, same posture as D3/R4)."""
    from accounts.services import ROLE_SUPER_ADMIN
    if not user_has_role(actor, {ROLE_SUPER_ADMIN}):
        raise PermissionDenied("Only a Super Admin can void a factory expense.")
    reason = (reason or '').strip()
    if not reason:
        raise ValidationError("A reason is required to void an expense.")
    # Row lock: two racing voids must not both stamp.
    expense = FactoryExpense.objects.select_for_update().get(pk=expense.pk)
    if expense.voided_at is not None:
        raise ValidationError("This expense is already voided.")
    expense.voided_at = timezone.now()
    expense.voided_by = actor
    expense.void_reason = reason[:200]
    expense.save(update_fields=['voided_at', 'voided_by', 'void_reason',
                                'updated_at'])
    logger.info("factory_expense.void id=%s by=%s reason=%s",
                expense.pk, actor.pk, reason[:80])
    return expense


def monthly_totals(year: int, month: int) -> dict:
    """Non-voided totals for one calendar month, derived live (never stored).
    Shape: {'total', 'count', 'by_category': {value: {'label','total','count'}}}."""
    rows = (
        FactoryExpense.objects
        .filter(expense_date__year=year, expense_date__month=month,
                voided_at__isnull=True)
        .values('category')
        .annotate(total=Sum('amount'), count=Count('id'))
    )
    by_category = {
        r['category']: {
            'label': FactoryExpense.Category(r['category']).label,
            'total': r['total'], 'count': r['count'],
        } for r in rows
    }
    return {
        'total': sum((v['total'] for v in by_category.values()), _ZERO),
        'count': sum(v['count'] for v in by_category.values()),
        'by_category': by_category,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Monthly Expense Engine (Phase 16 MEE-B; charter = PDD register entry 7;
# writers censused in R5_HOSTILE_REVIEW Part 2 ADDENDUM 1, owner-approved
# 2026-07-18). ADDITIVE section — every function ABOVE this banner is
# byte-untouched. FactoryExpense gains NO new writer here: generation CALLS
# record_expense(). Owner policies of record: M-3 collision ⇒ SKIP that salary
# template, period continues; regeneration prices at the CURRENT template
# amount (history keeps the old figure on the voided row + the audit trail).
# ═══════════════════════════════════════════════════════════════════════════


def _ensure_super_admin(actor, action):
    # Same posture as void_expense (P-2): the SA-only levers refuse everyone else.
    from accounts.services import ROLE_SUPER_ADMIN
    if not user_has_role(actor, {ROLE_SUPER_ADMIN}):
        raise PermissionDenied(f"Only a Super Admin can {action}.")


def _month_bounds(year: int, month: int):
    """Period sanity + the calendar facts (stdlib, no util module): returns
    (period_key, first_day, last_day). Clamping day-of-month to `last_day`
    handles Feb/leap/31st anchors (charter calendar rule)."""
    import calendar
    from datetime import date as _date
    if not (1 <= month <= 12 and 2000 <= year <= 2100):
        raise ValidationError("Invalid period (expected a real year/month).")
    last = calendar.monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}", _date(year, month, 1), _date(year, month, last)


def create_expense_template(*, label, category, amount, start_date,
                            end_date=None, worker=None, notes='', actor):
    """RESPONSIBILITY: owns the birth of recurring-expense configuration.
    WRITES: ExpenseTemplate INSERT only. NEVER: FactoryExpense, coverage,
    audit, or any existing row — money is never touched here.

    SA-only (MEE-D6: templates encode salary amounts). Friendly service-level
    errors mirror the DB constraints (the DB remains the last wall)."""
    from expense.models import ExpenseTemplate

    _ensure_super_admin(actor, "create an expense template")
    if category not in FactoryExpense.Category.values:
        raise ValidationError("Unknown expense category.")
    try:
        amount = Decimal(str(amount))
    except Exception:
        raise ValidationError("Amount must be a number.")
    if amount <= 0:
        raise ValidationError("Amount must be greater than zero.")
    label = (label or '').strip()
    if not label:
        raise ValidationError("A template label is required.")
    # P-1 pair (both directions — the DB CheckConstraint backs this).
    if category == FactoryExpense.Category.SALARY and worker is None:
        raise ValidationError("A salary template needs a worker (whose salary?).")
    if category != FactoryExpense.Category.SALARY and worker is not None:
        raise ValidationError("Only salary templates may reference a worker.")
    if worker is not None and not worker.is_active:
        raise ValidationError("Cannot create a salary template for an inactive worker.")
    if end_date is not None and end_date < start_date:
        raise ValidationError("End date cannot be before the start date.")
    # Friendly pre-check for the partial unique (one ACTIVE salary template per worker).
    if (worker is not None and ExpenseTemplate.objects.filter(
            category=FactoryExpense.Category.SALARY, worker=worker,
            is_active=True).exists()):
        raise ValidationError(
            "This worker already has an active salary template — deactivate it first.")
    with transaction.atomic():
        template = ExpenseTemplate.objects.create(
            label=label, category=category, amount=amount, worker=worker,
            start_date=start_date, end_date=end_date, notes=notes or '',
            created_by=actor)
    logger.info("expense_template.create id=%s label=%s by=%s",
                template.pk, label[:40], actor.pk)
    return template


def deactivate_expense_template(template, *, actor):
    """RESPONSIBILITY: owns the soft-state retirement of a template.
    WRITES: ExpenseTemplate.is_active only (UPDATE one field). NEVER: money
    rows, coverage, audit, or any other template field — history and future
    generated rows are simply no longer produced.

    SA-only. Idempotent: an already-inactive template is a no-op."""
    from expense.models import ExpenseTemplate

    _ensure_super_admin(actor, "deactivate an expense template")
    with transaction.atomic():
        template = ExpenseTemplate.objects.select_for_update().get(pk=template.pk)
        if not template.is_active:
            return template            # converge, never error on re-click
        template.is_active = False
        template.save(update_fields=['is_active', 'updated_at'])
    logger.info("expense_template.deactivate id=%s by=%s", template.pk, actor.pk)
    return template


def change_template_amount(template, *, new_amount, reason, actor):
    """RESPONSIBILITY: owns the ONE mutable money-bearing config field.
    WRITES: ExpenseTemplate.amount (UPDATE) + ExpenseTemplateAmountAudit
    (INSERT) — indivisibly, in one transaction (an unaudited change cannot
    exist). NEVER: FactoryExpense, coverage, or any already-generated row —
    covered periods keep the amount they were generated at (owner ruling
    2026-07-18: identity stable, changes traceable, history untouched).

    SA-only + mandatory reason (the void_expense/rerate posture)."""
    from expense.models import ExpenseTemplate, ExpenseTemplateAmountAudit

    _ensure_super_admin(actor, "change a template amount")
    reason = (reason or '').strip()
    if not reason:
        raise ValidationError("A reason is required to change a template amount.")
    try:
        new_amount = Decimal(str(new_amount))
    except Exception:
        raise ValidationError("Amount must be a number.")
    if new_amount <= 0:
        raise ValidationError("Amount must be greater than zero.")
    with transaction.atomic():
        template = ExpenseTemplate.objects.select_for_update().get(pk=template.pk)
        if not template.is_active:
            raise ValidationError("Cannot change the amount of a deactivated template.")
        if new_amount == template.amount:
            raise ValidationError("The new amount is the same as the current amount.")
        old = template.amount
        template.amount = new_amount
        template.save(update_fields=['amount', 'updated_at'])
        ExpenseTemplateAmountAudit.objects.create(
            template=template, old_amount=old, new_amount=new_amount,
            changed_by=actor, reason=reason[:200])
    logger.info("expense_template.amount id=%s %s→%s by=%s reason=%s",
                template.pk, old, new_amount, actor.pk, reason[:80])
    return template


def _resolve_month(year, month):
    """Classify every template for one monthly period (THE single resolution
    path — preview and confirm both read this; a future frequency adds a
    branch HERE, per the charter's enum seam). Returns (period_key,
    expense_date_fn, due:[template], skipped:[(template, reason)])."""
    from expense.models import ExpenseGenerationRecord, ExpenseTemplate

    period_key, first_day, last_day = _month_bounds(year, month)
    covered = {
        r.template_id: r for r in
        ExpenseGenerationRecord.objects
        .filter(period_key=period_key, superseded_at__isnull=True)
        .select_related('expense')
    }
    due, skipped = [], []
    for t in (ExpenseTemplate.active
              .filter(frequency=ExpenseTemplate.Frequency.MONTHLY)
              .select_related('worker')):
        if t.start_date > last_day:
            skipped.append((t, "starts after this period"))
        elif t.end_date is not None and t.end_date < first_day:
            skipped.append((t, "expired before this period"))
        elif t.pk in covered:
            cov = covered[t.pk]
            skipped.append((t, "already generated"
                            + (" (expense voided — regenerate explicitly)"
                               if cov.expense.voided_at else "")))
        elif t.worker is not None and not t.worker.is_active:
            # Q13 (owner): worker inactive ⇒ salary generation stops
            # AUTOMATICALLY — no FnF coupling, purely a generation-time check.
            skipped.append((t, "worker is inactive"))
        else:
            due.append(t)

    def expense_date_for(t):
        # Anchor day = the template's start day, clamped to this month's end.
        return first_day.replace(day=min(t.start_date.day, last_day.day))
    return period_key, expense_date_for, due, skipped


def generate_monthly_expenses(year, month, *, actor, confirm=False):
    """RESPONSIBILITY: owns period generation — turning due templates into
    ordinary FactoryExpense rows THROUGH record_expense() (the sole writer),
    plus the idempotency coverage. WRITES (confirm=True only): FactoryExpense
    via record_expense + ExpenseGenerationRecord INSERT. NEVER: templates,
    audit rows, existing expenses, ledger/settlement/costing state (no import,
    no read — ADR-0011). confirm=False = PURE READ (the preview IS this same
    resolution path).

    Management-triggered (MEE-D6). Per-template savepoint inside a per-period
    outer atomic: an M-3 duplicate-salary refusal SKIPS that template and the
    period continues (owner policy); ANY other failure rolls the whole period
    back. Idempotent: covered periods create nothing and say why."""
    from django.db import IntegrityError
    from expense.models import ExpenseGenerationRecord

    if not user_has_role(actor, MANAGEMENT_ROLES):
        raise PermissionDenied("Only management can generate recurring expenses.")
    period_key, expense_date_for, due, skipped = _resolve_month(year, month)
    plan = [{'template': t, 'amount': t.amount, 'worker': t.worker,
             'expense_date': expense_date_for(t)} for t in due]
    if not confirm:
        return {'period_key': period_key, 'to_create': plan,
                'skipped': skipped, 'created': []}

    created = []
    try:
        with transaction.atomic():                      # the period boundary
            for row in plan:
                t = row['template']
                try:
                    with transaction.atomic():          # per-template savepoint
                        expense = record_expense(
                            category=t.category, amount=t.amount,
                            expense_date=row['expense_date'], actor=actor,
                            notes=(f"Generated from template '{t.label}' "
                                   f"for {period_key}"
                                   + (f" — {t.notes}" if t.notes else "")),
                            worker=t.worker)
                        record = ExpenseGenerationRecord.objects.create(
                            template=t, period_key=period_key,
                            expense=expense, generated_by=actor)
                except ValidationError as exc:
                    if getattr(exc, 'code', None) == 'duplicate_salary':
                        # Owner policy: M-3 wins — skip, keep going. The
                        # engine NEVER passes confirmed_duplicate.
                        skipped.append((t, "manual salary exists for this "
                                           "month — void it if the template "
                                           "should win"))
                        continue
                    raise                               # real failure ⇒ outer rollback
                created.append(record)
    except IntegrityError:
        # Concurrent double-confirm: the partial unique is the serialization
        # point; the losing run rolls back whole and reports cleanly.
        raise ValidationError(
            f"Period {period_key} was generated concurrently — refresh and re-check.")
    logger.info("expense_generation.period key=%s created=%s skipped=%s by=%s",
                period_key, len(created), len(skipped), actor.pk)
    return {'period_key': period_key, 'to_create': plan,
            'skipped': skipped, 'created': created}


def regenerate_period(template, *, year, month, reason, actor):
    """RESPONSIBILITY: owns the void→regenerate supersession chain for ONE
    (template, period). WRITES: old ExpenseGenerationRecord.superseded_at
    (UPDATE one field) + FactoryExpense via record_expense + new
    ExpenseGenerationRecord INSERT — one transaction, chain lands whole or not
    at all. NEVER: the voided expense row (it stays, struck, forever), the
    template, the audit trail.

    SA-only + mandatory reason (regeneration follows a void — same lever
    owner). Allowed ONLY while the covering expense is voided; prices at the
    template's CURRENT amount (owner policy 2026-07-18)."""
    from expense.models import ExpenseGenerationRecord, ExpenseTemplate

    _ensure_super_admin(actor, "regenerate a covered period")
    reason = (reason or '').strip()
    if not reason:
        raise ValidationError("A reason is required to regenerate a period.")
    period_key, first_day, last_day = _month_bounds(year, month)
    with transaction.atomic():
        template = ExpenseTemplate.objects.select_for_update().get(pk=template.pk)
        if not template.is_active:
            raise ValidationError("Cannot regenerate for a deactivated template.")
        if template.worker is not None and not template.worker.is_active:
            raise ValidationError("Worker is inactive — salary generation is stopped (Q13).")
        try:
            current = (ExpenseGenerationRecord.objects.select_for_update()
                       .select_related('expense')
                       .get(template=template, period_key=period_key,
                            superseded_at__isnull=True))
        except ExpenseGenerationRecord.DoesNotExist:
            raise ValidationError(
                "This period was never generated — use normal generation.")
        if current.expense.voided_at is None:
            raise ValidationError(
                "The covering expense is not voided — void it first (the only door).")
        current.superseded_at = timezone.now()
        current.save(update_fields=['superseded_at', 'updated_at'])
        expense = record_expense(
            category=template.category, amount=template.amount,
            expense_date=first_day.replace(
                day=min(template.start_date.day, last_day.day)),
            actor=actor,
            notes=(f"Regenerated from template '{template.label}' for "
                   f"{period_key} — {reason}"),
            worker=template.worker)
        record = ExpenseGenerationRecord.objects.create(
            template=template, period_key=period_key, expense=expense,
            generated_by=actor, supersedes=current,
            regeneration_reason=reason[:200])
    logger.info("expense_generation.regenerate key=%s tpl=%s old=%s new=%s by=%s",
                period_key, template.pk, current.pk, record.pk, actor.pk)
    return record
