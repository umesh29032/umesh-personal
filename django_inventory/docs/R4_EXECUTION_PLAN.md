---
id: r4-execution-plan
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# R4 EXECUTION PLAN — MONTHLY pay basis (PDD §27-D4)

> Phase R4 of [IMPLEMENTATION_ROADMAP_PDD_V1.md](IMPLEMENTATION_ROADMAP_PDD_V1.md),
> implementing 🔒 PDD §17 (MONTHLY row) + §27-D4 (owner-resolved): *monthly is a
> property of the WORKER (`WorkerProfile.pay_basis`), never the stage — a stage
> can host piece-rate karigar + monthly helper simultaneously. Monthly workers
> still submit production entries for analytics; those entries MUST NEVER
> generate settlement lines. Salary is paid via Expenses (§21 → phase R5).*
> STATUS: **✅ ACCEPTED by owner 2026-07-05 (uncommitted — checkpoint
> policy). Audit-sufficiency confirmed post-acceptance: `set_pay_basis` is the
> only pay_basis writer (form field-list excludes it, admin readonly), so the
> WorkerPayBasisAudit chain (old→new, actor, unsettled count, timestamp; rows
> append-only, PROTECT FKs) reconstructs every historical change; no-audit-rows
> = piece_rate since creation. DEV test data RETAINED through R5-R7 by owner
> instruction.** Owner approved P-1 (settlement-time read, no
> per-contribution snapshot) / P-2 (super-admin only) / P-3 (DB audit table) /
> P-4 (suppress entirely + badge) + ADDENDUM: pay-basis change over unsettled
> lines needs a WARNING + EXPLICIT CONFIRMATION (not a hard block) —
> implemented as `confirmed=` gate in `set_pay_basis` (server-enforced) +
> checkbox in the amber warning box on the profile page.
> Hardening beyond plan: `set_pay_basis` JOINS settlement advisory lock 5374
> (same F1 pattern as `rerate_stage_role`) — a basis flip can't race a
> finalize between its `_settleable_lines` read and its money write.
> Results: gate PASS **750** (+16 test_r4_monthly_basis; 2 preview_lines
> 3-tuple unpacks updated) · golden ₹225 byte-identical · LIVE browser E2E
> (fresh DEV-marked data: dev.monthly@test.local, DEV-Manager, Adda
> 3-PATTI-008 + DEV-R4M-001/ADST-0004): refusal message without confirm,
> confirmed change + audit row (old→new/actor/unsettled=1/ts), monthly worker
> sees qty + "Monthly Salary" badge and ZERO ₹ tokens (My Earnings + My Work,
> 360px no-overflow), draft shows "Excluded — monthly-salary worker" panel
> (qty only, no ₹ column), finalize booked ₹200 to utest ONLY (monthly worker
> 0 ledger rows all-time, settlement_line NULL), manager sees read-only panel
> AND a forged manager POST was refused server-side; piece-rate colleague's
> views unchanged.
> Anchors verified against code 2026-07-04 (post-R3 acceptance).

## 1) Current behavior vs target

| | Today | R4 target (D4) |
|---|---|---|
| Pay basis | every worker is implicitly piece-rate | `WorkerProfile.pay_basis` = `piece_rate` (default) \| `monthly` |
| Settlement lines | every COMPLETED contribution on a payable stage becomes a settleable line | monthly workers' contributions **structurally excluded** at the single settlement funnel — a 4th labeled skip class |
| Expected ₹ display | My Work + My Earnings show frozen `expected_earning` | monthly worker: **quantities always shown** (production truth / analytics), **₹ expectation suppressed** (not ₹0.00 — no figure at all) + "Monthly" badge |
| Salary payment | n/a | **OUT OF SCOPE** — lands with R5 FactoryExpense (PDD §21: "Monthly salaries recorded here") |
| Double-pay | n/a | impossible by construction: salary (R5 expense) + settlement can never both pay the same worker — settlement never emits their lines (PDD §29 risk 4) |

Production truth is UNTOUCHED: monthly workers keep reporting through the same
C-TM chokepoint; freeze (`expected_rate/earning/role_snapshot`) keeps stamping
at complete. Only the MONEY GATE and the ₹ PRESENTATION change.

## 2) Design — guard at the one money funnel

### 2a. Model (migration expense **0012**)
`WorkerProfile.pay_basis` — `TextChoices` `PIECE_RATE='piece_rate'` (default) /
`MONTHLY='monthly'`. Profiles are `get_or_create`-on-demand (models.py:389), so
**no backfill**: absent profile ⇒ default ⇒ piece_rate. Nothing changes for any
existing worker.

Plus (pending P-3): append-only `WorkerPayBasisAudit` (worker, old_basis,
new_basis, changed_by, created_at) — same migration.

### 2b. Structural guard — `_settleable_lines` (adda_settlement_service.py:97)
The ONE funnel already feeding **preview_lines + settlement_queue + finalize**
(verified: :161/:197/:295). One query resolves the candidate workers' monthly
ids (`WorkerProfile.objects.filter(user_id__in=…, pay_basis=MONTHLY)`); their
lines land in a new 4th bucket:

```
return lines, skip_a, skip_b, skip_monthly     # was 3-tuple
```
- **finalize can never see a monthly line** — exclusion is structural, not a UI
  filter. Their `settlement_line` stays NULL forever (never linked).
- Draft screen labels the 4th class: *"Monthly worker — excluded, salary via
  Expenses"* (mirrors the existing era-A/era-B labeling, views.py:412).
- Queue drops monthly-only Addas naturally (same funnel).
- 3-tuple consumers (3, all in-repo) updated together.

### 2c. `pay_basis` change chokepoint — `payroll_service.set_pay_basis`
New service function (rule 4/5 discipline): validates actor (P-2), writes
profile + audit row atomically. `WorkerProfileForm` does NOT gain the field —
the profile edit page gets a separate, permission-gated control posting to the
service. Server re-checks role; the form is never trusted.

### 2d. Presentation (analytics-only, D4 clause 3)
Single accessor `payroll_service.is_monthly(worker)` (one profile read; absent
profile → False), used by:
- **My Earnings + management worker detail** (expense/views.py:74/:97): monthly
  → suppress the "Expected (unsettled)" ₹ card, show "Monthly — salary via
  Expenses" badge. Quantities/task history unchanged.
- **My Work on Adda detail** (adda_views.py:218-239): monthly viewer → per-task
  qty + unit stay, `my_expected`/`my_expected_total` ₹ hidden, badge shown.
`unsettled_expected()` itself stays pure (it remains correct analytics); the
VIEWS decide presentation — no scattered profile reads.

### What deliberately does NOT change
- `complete_worker_task` freeze — untouched. Freezing `expected_*` for monthly
  workers is correct (analytics + it re-prices nothing). A freeze-time
  rate-zero variant was REJECTED: it would import expense models into
  `worker_task_service` (production→expense = new dependency direction, cycle
  risk) and would strand frozen ₹0 if a worker ever switches basis.
- Settlement engine, ledger, rates, golden ₹225 — piece-rate world byte-identical.
- Reconciliation (S5): verified safe — finalize-BLOCK fires only on
  `over_allocated` (paid > produced); monthly exclusion only lowers paid qty.
  A soft "under" flag may appear on mixed stages — correct by construction
  (their output IS unpaid-by-settlement); noted, never blocking.

## 3) Files to modify

| File | Change |
|---|---|
| `config/expense/models.py` | `pay_basis` choices+field on WorkerProfile (+ `WorkerPayBasisAudit` per P-3) |
| `config/expense/migrations/0012_*.py` | the migration (additive, reversible) |
| `config/expense/services/adda_settlement_service.py` | 4th skip bucket in `_settleable_lines`; consumers threaded |
| `config/expense/services/payroll_service.py` | `is_monthly` + `set_pay_basis` (audited chokepoint) |
| `config/expense/views.py` | settlement-detail 4th class ctx; My Earnings/worker-detail monthly presentation; profile-edit pay-basis control |
| `expense templates` (settlement detail, my-earnings, worker detail, profile edit) | badge + skip-class label + control (mobile-first, rule 11) |
| `config/production/views/adda_views.py` + `adda_detail.html` | My Work monthly presentation |
| `config/expense/admin.py` | show `pay_basis` read-only-ish in WorkerProfileAdmin list |
| `config/expense/tests/test_r4_monthly_basis.py` (new) | §6 |

## 4) Database migrations
**expense 0012** — add `pay_basis` (default `piece_rate`, NOT NULL) + audit
table (P-3). Purely additive; reverse = drop column/table; zero rows touched.

## 5) Owner confirmations ❓ (answer before implementation)

| ID | Question | Recommendation |
|---|---|---|
| P-1 | **Basis-switch semantics.** Guard reads pay_basis at SETTLEMENT time (recommended). Consequences, both directions: piece→monthly with unsettled lines ⇒ those lines will NOT pay (visible in draft as the labeled skip class; salary presumed to cover the period). monthly→piece ⇒ prior unsettled contributions BECOME payable at their frozen rates (visible in draft before finalize). Alternative — snapshotting basis per contribution at complete — rejected (production→expense import cycle + freeze-map growth for a rare owner-controlled event). | settlement-time read; switches audited (P-3) + always visible in the draft preview |
| P-2 | Who may change pay_basis? | **super_admin only** — it is a money-structure lever (same posture as D3 corrections); managers see it read-only |
| P-3 | Audit trail: DB table vs logs? | small append-only `WorkerPayBasisAudit` — your R3 principle ("investigations must not depend on external logs") |
| P-4 | Monthly worker's ₹ presentation: suppress entirely (no figure) vs show ₹0.00? | suppress entirely + "Monthly" badge — ₹0.00 reads as "worked for free", misleading |

## 6) Tests (new `test_r4_monthly_basis.py` + touched suites)

1. Default: worker without profile / fresh profile ⇒ piece_rate; settles as today.
2. **Double-pay impossibility (roadmap exit test):** monthly + piece-rate
   colleague on the SAME stage — preview puts monthly in `skip_monthly`;
   finalize books colleague's line only; monthly worker gets ZERO ledger
   entries; their contributions keep `settlement_line=NULL`.
3. Queue: Adda whose only pending lines are monthly ⇒ not offered as settleable.
4. Basis-switch pin (per P-1 decision), both directions.
5. `set_pay_basis`: super_admin OK + audit row (old/new/actor); manager
   PermissionDenied; nothing written on refusal.
6. Presentation: My Earnings + My Work context/template assertions — monthly
   worker sees quantities, sees NO ₹ token; piece-rate colleague unchanged.
7. Golden ₹225 byte-identical + full suite (`bash scripts/check.sh`, 734+).

## 7) Browser E2E (test-data authorization applies)
Create clearly-marked dev data: worker **"DEV-Monthly Worker"** (monthly) +
fresh Adda on 3-PATTI; assign monthly + utest (piece-rate) to layering; both
report; complete (C3 satisfied by both submitting); then verify — monthly
worker's My Earnings/My Work: quantities yes, ₹ no, badge yes; draft
settlement: monthly line in the labeled excluded class; finalize: utest paid,
monthly ledger empty; 360px + desktop; roles: worker/manager/super-admin
(pay-basis control visibility + server-side refusal).

## 8) Risks

| Risk | Mitigation |
|---|---|
| Monthly lines "unsettled forever" nag some surface | funnel-based consumers (queue/preview) drop them; the 2 `unsettled_expected` views get the presentation rule; recon soft-flag documented (§2d/§2 end) |
| 3-tuple→4-tuple signature break | all 3 consumers in-repo, updated + tested in the same change |
| pay_basis flipped mid-draft (draft open, basis changes, finalize) | finalize recomputes via `_settleable_lines` under lock — settlement-time read means finalize uses the CURRENT basis; draft preview is a scratchpad by design (§11.5) |
| R7 F&F interplay | monthly F&F = zero earning lines + advance clearance + salary via expenses — exactly why roadmap orders R7 after R4; no R4 code |
| UI leak (pay-basis control to non-super-admin) | template-gated AND service re-checks (never trust the form) |

## 9) Rollback
Additive migration ⇒ `migrate expense 0011` + `git revert` restores exactly.
No behavioral flag (D4 is an owner-locked default, not an experiment).

## 10) Acceptance criteria

- [ ] Monthly + piece-rate colleague on one stage: colleague settles normally,
      monthly excluded, labeled in draft, zero ledger rows — browser-verified.
- [ ] Monthly worker sees quantities but NO ₹ expectation (My Work + My
      Earnings), with badge — 360 + desktop.
- [ ] pay_basis change: super-admin only, audited (per P-2/P-3 answers).
- [ ] Piece-rate world byte-identical: golden ₹225 + full suite PASS.
- [ ] Docs synced same session (stage_earnings_flow §7 note, expense README,
      production GUIDE, PDD untouched — it already states D4).

## 11) Implementation order (estimated)

1. Model + migration + `is_monthly`/`set_pay_basis` + unit tests — ~1 h
2. `_settleable_lines` 4th bucket + 3 consumers + settlement tests — ~1.5 h
3. Presentation (2 expense views + My Work + templates + badge) — ~1 h
4. Profile-edit control + permission tests — ~45 min
5. Browser E2E (fresh dev data per §7) + docs — ~1 h

Total ≈ half a working day. Uncommitted (owner checkpoint policy).
