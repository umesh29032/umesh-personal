---
id: r5-hostile-review-2026-07-05
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# Hostile review — monthly workers + FactoryExpense (post-R5, 2026-07-05)

> Owner-ordered adversarial verification of the R4/R5 + ADR-0011 surface.
> Method: full enumeration of ledger/settlement/costing write paths (grep +
> code read), LIVE probes against the dev DB (rollback-wrapped where they
> would write money), and browser verification with the DEV fixtures.
> **Nothing below was accepted because "the code looks correct" — every
> verdict cites its probe.**

## Verdict summary

| # | Severity | Finding | Status |
|---|---|---|---|
| H-1 | HIGH (flag-gated) | era-A allocation path credits MONTHLY workers when the `LEDGER_CREDIT_AT_ALLOCATION` rollback lever is ON | **FIXED same day** (owner-approved pay_basis guard in allocate_stage_work + regression tests — Part 2) |
| M-1 | MED (future) | R7 F&F could bypass the monthly funnel if built with its own line-collector | guardrail documented in roadmap |
| M-2 | MED (business) | Advance to a monthly worker has NO in-system recovery path | owner decision needed |
| M-3 | MED (business) | No duplicate-salary protection (same worker + month, twice) | owner decision needed |
| M-4 | LOW/MED | Monthly workers invisible on the payroll overview until they hold money history | owner decision needed |
| L-2 | LOW | Recon report flags monthly-worked stages `unpaid`/`under_allocated` — indistinguishable from genuinely-unpaid | documented; enhancement optional |
| L-3 | LOW | Legacy `User.salary` field = second, disconnected salary concept (informational only) | owner decision needed |
| — | — | Everything else in scope | **CLEAN, probe-cited below** |

## H-1 — era-A lever credits monthly workers (LIVE-PROVEN)

`allocation_service.allocate_stage_work` (expense) predates R4 and has **no
`pay_basis` check**. With the ADR-0007 rollback lever ON it books an SWA +
immediate `STAGE_EARNING` ledger CREDIT for ANY worker — including monthly.
Salary (FactoryExpense) + allocation credit = the exact double-pay ADR-0011
forbids.

Probes (dev DB, rollback-wrapped):
- Lever OFF (production default): refused — *"Allocation-time crediting is
  disabled…"* ✓
- Lever ON: `SWA created=True, ledger rows 0→1` for dev.monthly — **hole
  confirmed**; transaction rolled back (0 rows after).

Mitigations today: lever defaults OFF everywhere; flipping it requires an env
change; ADR-0007's era-A deletion (gated backlog) removes the path entirely.

**Recommended fix (small, not yet applied — owner go):** a `pay_basis` guard
inside `allocate_stage_work` (refuse monthly workers regardless of the lever)
+ one test. Alternative: accept documented risk until era-A deletion.

## M-2 — advances to monthly workers are a dead end

`record_advance` accepts any worker. But BOTH recovery paths are unreachable
for monthly workers: Adda-settlement recovery requires the worker among the
settled workers (they never are), and cash-settlement recovery requires
`total_settled ≤ payable` (their payable is permanently ₹0 — probe: cash
₹500 to dev.monthly refused with *"exceeds pending payable 0.00"*). An
advance to a monthly worker sits outstanding until R7 F&F write-off or
off-system salary netting. Options: (a) block advances to monthly workers,
(b) allow + build salary-deduction recovery later, (c) accept + document.

## M-3 — duplicate salary entries

Nothing prevents recording July salary twice for the same worker. Real-owner
risk (fat-finger month-end). Recommended: soft warn-and-confirm (same pattern
as the R4 pay-basis confirm) when a non-voided salary row already exists for
that worker + calendar month. Not built — owner call.

## M-4 — payroll overview roster

`PayrollOverviewView` builds its roster from ledger ∪ advances ∪ recoveries —
correct for a payable board, but a monthly worker with no money history is
absent (browser-proven: dev.monthly not listed). No management surface today
lists "my monthly workers" as such. Options: pay-basis badge + include-monthly
row on the overview, or a pay-basis column/filter on Team Members. Owner call.

## L-2 / L-3 (documented)

- **L-2:** `reconcile_stage_pay` classifies monthly-worked stages as
  `unpaid`/`under_allocated` (soft flags — S5's finalize-BLOCK reads only
  `over_allocated`, which monthly exclusion can never produce since it only
  LOWERS paid qty). Cosmetic noise; danger is a human "fixing" an under
  flag via the allocation lever (= H-1 route). Optional future enhancement:
  annotate the monthly share in recon rows.
- **L-3:** `accounts.User.salary` (legacy, on the user create/edit forms) has
  ZERO money-code consumers (grep-verified) — informational only. Two salary
  concepts now exist; options: prefill the salary-expense form from it, hide
  it, or leave documented.

## CLEAN verdicts (each with its probe)

1. **Settlement funnel** — preview / queue / finalize / reverse-supersede all
   route through `_settleable_lines` (grep: no other caller); finalize
   recomputes under the 5374 advisory lock; `set_pay_basis` joins 5374 (race
   closed, R4). Monthly lines structurally excluded; R4 E2E booked ₹200 to
   the colleague only, monthly ledger 0 rows, `settlement_line` NULL.
2. **Cash payment path** — payable ₹0 ⇒ every cash settlement refuses
   (probe P3). Cannot pay salary through payroll cash.
3. **Rerate / verified-quantity** — recompute analytics on monthly lines
   harmlessly; neither touches payability.
4. **Production tracking completeness** — browser-proven as dev.monthly:
   dashboard lists both assigned Addas, report surface renders identically
   (submitted state), My Work shows quantities + Monthly badge; history and
   contributions identical to piece-rate. Zero pay_basis references anywhere
   in production tracking code (grep: only the My-Work ₹-suppression in
   `adda_views`).
5. **FactoryExpense containment** — model/service/views/admin/urls live only
   in the expense app; sole external consumer is the dashboard digest via
   `expense_service.monthly_totals`; `cost_service` and `costing_views`
   import nothing from FactoryExpense; zero-ledger-interaction pinned by
   test + proven live (dev.monthly ledger still 0 after ₹9000 salary).
6. **S5 reconciliation BLOCK** — unreachable from monthly exclusion
   (`over_allocated` needs paid > produced; exclusion only lowers paid).

## Future-phase guardrails (roadmap updated, instruction #5)

| Phase | ADR-0011 interaction | Guardrail |
|---|---|---|
| R6 verified-qty audit | none (production truth; monthly lines correctable like any) | — |
| **R7 F&F** | **HIGH** — per-worker settlement | MUST reuse the `_settleable_lines` funnel (or its filter); monthly F&F = ZERO earning lines + audited advance write-off (the M-2 exit) + deactivate; test required |
| R8/R9 stage earnings | none — config-only recipe; exclusion is stage-agnostic | — |
| R10 machines | none | — |
| **R11 MissingPiece** | worker-charge/deduction designs | monthly workers have NO settlement lines to deduct from — any charging mechanism must handle them explicitly |
| G6→G5→G2→**P&L** | FactoryExpense is the intended factory-level input | P&L may SUM FactoryExpense; it must NOT allocate it into per-Adda cost (ADR-0011); settled labor + salaries are disjoint populations — no double-count by construction |
| ADR-0007 era-A deletion | **resolves H-1 permanently** | link this finding when scheduling |
| Explicit-assignment migration / TM-1 / TM-2 / S6 | none (capture + roster paths are pay-agnostic) | — |
| Future cost-allocation phase | governed by ADR-0011 | must not rewrite production/settlement/worker/FactoryExpense history |

### Verification sources
Greps + code reads 2026-07-05 (allocation_service, settlement_service,
adda_settlement_service, payroll_service, cost_service, costing_views,
reconciliation_service, dashboard, accounts models/forms); live rollback
probes P1–P3; browser session as dev.monthly + super-admin (dashboard,
report page, payroll overview). Confidence: High.

---

# Part 2 — owner decisions, fixes, and the full payment-path census (2026-07-05)

## Fixes applied (owner-approved, gate PASS 775, all browser-proven)

| Finding | Fix | Proof |
|---|---|---|
| **H-1** | `pay_basis` guard FIRST in `allocate_stage_work` — refuses monthly workers regardless of `LEDGER_CREDIT_AT_ALLOCATION` | tests: lever-ON monthly refused + zero ledger rows; lever-ON piece-rate still credits (guard is monthly-scoped) |
| **M-2** | advances BLOCKED for monthly workers — ⚠ TEMPORARY business rule (revisit when a salary-deduction recovery path exists), documented in `advance_service` | browser: ₹500 to dev.monthly refused with the rule message; DB 0 advances |
| **M-3** | duplicate salary (worker + calendar month, non-voided) ⇒ `ValidationError(code='duplicate_salary')` unless `confirmed_duplicate=True`; form re-renders with warn box + checkbox — warn-and-confirm, never hard-block | browser: warning named "1 salary entry totalling ₹9000.00 for 2026-07", confirm → recorded; other-month + voided rows don't warn (tests) |
| **M-4** | Payroll Overview roster now = money-history ∪ MONTHLY workers; monthly rows badged, Settle replaced by "Salary →" (their pay never flows through settlement) | browser: "DEV-Monthly Worker MONTHLY … Salary →", badge:true, settle:false |
| **L-3** | investigated: `User.salary` = the agreed reference salary (user forms), zero money consumers → KEPT as a convenience: picking a worker on a salary expense prefills an empty amount from it (display-only sugar) | browser: amount auto-filled 9000.00 on worker pick |

## Full payment-path census (owner-ordered; 19 sweeps)

Question: are there OTHER hidden payment paths like era-A? **Answer: NO.**

| Sweep | Result |
|---|---|
| Signals | `inventory/signals.py` = tombstone comment only; zero `@receiver`/`post_save` anywhere (rule 4 holds) |
| Management commands (4) | `reconcile_denorm`, `preview_allocation_bound`, `reconcile_pay` = zero writes; `seed_homepage` writes storefront content models only |
| Cron / celery / tasks | none exist |
| `WorkerLedgerEntry` writers | `ledger_service.py` line 41 — the ONLY `objects.create` in the codebase |
| `StageWorkAssignment` writers | allocation_service + adda_settlement_service (CI gate 4c enforces) |
| `WorkerAdvance` writers | `advance_service` only |
| `PayrollSettlement(+Item)` writers | `settlement_service` + adda_settlement recovery lines only |
| `FactoryExpense` / `WorkerPayBasisAudit` / `AddaStageRoleRate` / `RateCorrectionAudit` writers | each exactly its designated service |
| `expected_rate/earning`, `verified_quantity` | worker_task_service + stage_rate_service (rerate) only |
| `processing_cost`, `earning_amount_snapshot` | cost_service / the two SWA writers only |
| Admin overrides | ZERO `save_model`/`delete_model`/custom actions on any money admin (all `_MoneyReadOnlyAdmin`) |
| Data migrations (RunPython) | historical one-time backfills (0009 = era-marker link stamping, 0004 legacy cleanup) — no live path |
| Views writing money models | only `WorkerProfileForm.save()` (explicit field list; `pay_basis` excluded — the R4 chokepoint holds) |
| Cross-app references | storefront/raw_materials/tracking/inventory contain ZERO worker-money model references |
| "salary" strings outside accounts/expense | only the R4 badge/footer copy in `adda_detail.html` |
| Reversal paths | `reverse_entry` called from adda_settlement (reverse/supersede) + allocation void only — compensating, not originating |

**Census verdict: the era-A allocation path (H-1, now guarded) was the only
payment path missing the monthly invariant. Every money write in the codebase
flows through its single designated service.**

---

## ADDENDUM 1 — Monthly Expense Engine writers (2026-07-18, Campaign Phase 16 MEE-B; owner-approved: "MEE-B IMPLEMENTATION AUTHORIZATION — The architecture review is approved")

The Monthly Expense Engine adds FIVE expense-service-family functions and THREE engine
tables. The census invariant is UNCHANGED: every money write flows through its single
designated service.

| Table | Writes added | Writing function(s) — ALL in `expense/services/expense_service.py` | Gate |
|---|---|---|---|
| `FactoryExpense` | **NONE — no new writer.** Generation CALLS the existing `record_expense` (sole writer unchanged); generated rows are ordinary rows, voidable by the existing SA lever | `generate_monthly_expenses` / `regenerate_period` → `record_expense` | management / SA |
| `ExpenseTemplate` | INSERT (create) · UPDATE `is_active` only (deactivate — soft-state) · UPDATE `amount` only (audited change) | `create_expense_template` · `deactivate_expense_template` · `change_template_amount` | SA-only (MEE-D6) |
| `ExpenseTemplateAmountAudit` | INSERT only — append-only forever | `change_template_amount` (atomically WITH the amount UPDATE) | SA-only |
| `ExpenseGenerationRecord` | INSERT (generate/regenerate) · UPDATE `superseded_at` only (regenerate) · never DELETE | `generate_monthly_expenses` (confirm=True) · `regenerate_period` | management / SA |

No other field of any engine table is writable by any function (V1 has NO edit path for
label/notes/dates/worker/category). UI/forms/commands/admin write NOTHING (purity-pinned
in the expense suite). Owner-approved policies of record: M-3 collisions SKIP the
conflicting salary template and the period continues (the engine never passes
`confirmed_duplicate`); regeneration prices at the template's CURRENT amount, historical
rows unchanged (append-only history carries the old figure). Full write-path evidence:
[MONTHLY_EXPENSE_ENGINE_LOG.md](MONTHLY_EXPENSE_ENGINE_LOG.md) §B.0.
