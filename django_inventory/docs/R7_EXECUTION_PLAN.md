---
id: r7-execution-plan
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# R7 EXECUTION PLAN — Full & Final settlement (PDD §20 / §27-D5)

> Phase R7 of [IMPLEMENTATION_ROADMAP_PDD_V1.md](IMPLEMENTATION_ROADMAP_PDD_V1.md),
> implementing 🔒 PDD §20 (5-step F&F design), §27-D5 (residual advance =
> explicit AUDITED write-off — nothing disappears silently), §31.2
> (deactivation blocks LOGIN, never money — F&F depends on this).
> **🔒 ADR-0011 guardrail (roadmap, hostile review M-1): the line collector
> MUST be the `_settleable_lines` funnel — monthly F&F = ZERO earning lines +
> advance write-off + deactivate, test-pinned.**
> STATUS: **✅ ACCEPTED by owner 2026-07-05 (uncommitted — checkpoint
> policy). Post-acceptance: 8-scenario business lifecycle audit delivered +
> canonical [fnf_business_flow.md](LEARNING_2_0/DATA_FLOWS/fnf_business_flow.md).**
> Owner approved the architecture in principle and
> ordered a PRE-IMPLEMENTATION VERIFICATION first — completed CLEAN on all 4
> points before any code: partial settlements already legal (model §11.8
> comment), reverse structurally one-settlement-scoped, reopen armor
> stage-level conservative, rerate lock per (SR,role) conservative, all funnel
> consumers line-granular; LIVE 7-step lifecycle probe passed rollback-wrapped
> (settle/queue-drop/armor/double-settle-refused/reverse-restores/armor-release/
> re-settle-once). P-open-1 resolved = probe artifact (`_seed_status` seeds
> 'completed' tasks on completed SRs — 0032 parity).
> Built per plan (P-2/P-4/P-5 per recommendation): `only_worker=` filter in
> finalize · migration expense **0014** (PSI `write_off_reason` +
> `written_off_by` + coherence constraint) · `settlement_service
> write_offs=` (super-admin+reason, PSI row, NO ledger debit, reversible) ·
> `fnf_service` preview/execute (orchestration only — zero own writes) ·
> `/expense/workers/<pk>/fnf/` checklist UI + worker-detail button.
> Results: gate PASS **788** (+9 test_r7_fnf) · golden byte-identical ·
> writer gates 4b/4c green (no new money path — STOP rule checked) · LIVE
> browser E2E (fresh DEV-Leaver world: 2 settled Addas + 1 open task + ₹500
> advance): blockers rendered + FORCED POST past the disabled button refused
> server-side naming the open task → task resolved via existing audited
> cancel → executed: "2 settlement(s), ₹90.00 paid, 1 advance write-off(s)" —
> DB: two leaver-only AddaSettlements (₹30/₹60), closure SETL with write-off
> PSI (reason+actor, ledger_entry NULL), leaver balance 0/outstanding 0/
> deactivated (login refused, pages render, F&F button hidden); colleague
> utest ₹425 untouched and STILL SETTLEABLE on the shared stage (mixed-SR
> state live); monthly variant DEV-Monthly-2: zero settlements, zero ledger
> rows, deactivated (ADR-0011 pin); F&F page 360px no-overflow.
> Anchors verified against code 2026-07-05 (post-R6, gate 779).

## 1) What F&F is (business)

A worker leaves. In ONE guided flow the owner:
1. resolves the worker's open tasks (report-and-complete or audited cancel),
2. settles ALL their unsettled completed lines across every Adda,
3. clears advances — recover from payable, WRITE OFF the audited residual,
4. pays the remaining cash,
5. deactivates the account. History stays forever (PROTECT + append-only).

## 2) Design — reuse the engine, extend nothing's writer

### 2a. Worker-scoped settlement (the core mechanic) — P-1
`AddaSettlement` is Adda-FK'd and PDD §20 mandates **no new tables**, so the
cross-Adda F&F = a LOOP of per-Adda settlements scoped to the leaver:

- `finalize_adda_settlement` gains optional `only_worker=None` — when set,
  `_settleable_lines` output is filtered to that worker before booking
  (colleagues' lines stay unsettled — settle-anytime C1 untouched for them).
  Writer stays `adda_settlement_service` (gates 4b/4c intact — NO new money
  path; the money-write STOP rule was checked against this design).
- New `fnf_service.py` (expense) orchestrates: collect the worker's
  uncredited lines grouped by Adda (funnel filter — monthly workers get zero
  by construction) → per Adda: `create_draft` (or reuse open draft) +
  `finalize(..., only_worker=leaver)`; Addas with zero lines for the leaver
  are SKIPPED, not errors. Each settlement carries notes `F&F <worker>`.
- Draft gate today requires ALL payable stages completed (§11.5). For an Adda
  mid-flight, the leaver's completed lines on completed stages can't settle
  until that gate passes → F&F REFUSES with an actionable list ("Adda X:
  stage Y not completed") — owner completes stages or cancels the leaver's
  mid-flight tasks first. No gate weakening (quantities-final stays true).

### 2b. Advance clearance + audited write-off — P-2
Recovery-from-payable happens inside the per-Adda finalizes (existing
owner-chosen `recoveries`, F&F UI pre-fills max-recovery). The RESIDUAL:

- **Write-off = a `PayrollSettlementItem` row with NO ledger debit** —
  `advance_outstanding` (derived: given − Σ non-reversed PSI) drops to zero
  while payable is untouched (an un-recovered loan is forgiven, not paid).
- Audit (D5): new PSI columns `write_off_reason` (mandatory) +
  `written_off_by` FK — migration expense **0014** (columns, not tables).
  Super-admin only, same posture as void/rerate/pay-basis.
- Reversible like everything else: PSI `reversed_at` already exists — a
  mistaken write-off is reversed, advance outstanding returns.

### 2c. Open tasks — P-3 (precondition, not magic)
F&F REFUSES while the worker has ACTIVE tasks (assigned/in_progress). The
F&F page lists each with links to the existing chokepoints: report+complete
(worker/management path) or cancel via `set_stage_workers` (audited,
cancel-not-delete). No bulk auto-cancel — C-TM and the R3 audit posture stay
intact. (PDD §20 step 1's "complete-with-reported or cancel" happens through
the EXISTING flows, listed by the checklist.)

### 2d. Cash + deactivate
- Remaining payable → existing `settlement_service.create_settlement`
  (payment-only event; method/date/notes). Zero payable ⇒ step skipped
  (create_settlement refuses zero — the flow branches, PDD edge case).
- Deactivate: `is_active=False` via the existing accounts update path
  (§31.2: blocks login only; PROTECT keeps every money/history row).
- The whole flow is NOT one DB transaction (multi-settlement + payment +
  deactivate = separate audited events, each atomic itself — matches the
  "settlement ≠ payment" model). The F&F page shows live progress state, so
  a mid-flow abort leaves a consistent, resumable system (already-finalized
  settlements simply exist; rerunning F&F picks up what's left).

### 2e. Monthly workers (ADR-0011, test-pinned)
Funnel yields zero lines → zero settlements booked; advances (legacy pre-M-2
ones) go straight to write-off; cash step skipped (payable 0); deactivate.

## 3) Files

| File | Change |
|---|---|
| `config/expense/services/adda_settlement_service.py` | `only_worker=` filter in finalize (sole writer unchanged) |
| `config/expense/services/fnf_service.py` (new) | orchestration: preview + execute (calls existing writers ONLY) |
| `config/expense/services/settlement_service.py` | write-off entry point (PSI writer stays here) — or in fnf_service? NO: PSI single-writer stays settlement_service (rule 5) |
| `config/expense/models.py` + migration **0014** | PSI `write_off_reason` + `written_off_by` |
| `config/expense/views.py` + `urls.py` | `WorkerFnFView` (preview checklist + confirm + execute) at `/expense/workers/<pk>/fnf/` |
| `expense templates` | `worker_fnf.html` (mobile-first checklist: open tasks / per-Adda lines+expected / advances+residual / payable preview / confirm) + F&F button on worker detail |
| tests `test_r7_fnf.py` (new) | §5 |

## 4) Owner confirmations ❓

| ID | Question | Recommendation |
|---|---|---|
| P-1 | Cross-Adda mechanics: loop of per-Adda settlements scoped via `only_worker` (no new tables, sole writer intact, era guards intact) — colleagues' lines untouched? | **yes** — the only design that satisfies §20 "reuse the engine, no new tables" without force-settling colleagues |
| P-2 | Write-off = PSI row (no ledger debit) + `write_off_reason`/`written_off_by` columns; super-admin + mandatory reason? | **yes** — outstanding derives to 0, payable untouched, reversible via existing `reversed_at`, DB-resident audit (your standing posture) |
| P-3 | Open tasks = REFUSE-with-checklist (resolve via existing flows), no bulk auto-cancel? | **yes** — keeps C-TM/R3 audit; F&F page makes it a 2-minute guided job |
| P-4 | Whole F&F flow super-admin only? | **yes** — rare, money-sensitive exit event (D3/D5 posture); managers see the button disabled with a hint |
| P-5 | Incomplete payable stages holding the leaver's lines: REFUSE with actionable list (recommended) vs settle-what's-gate-ready and leave the rest? | refuse-first is safer; a partial-F&F variant can ship later if real exits demand it |

## 5) Tests
1. `only_worker` scoping: two workers on one Adda → F&F settles ONLY the
   leaver's lines; colleague's line still settleable afterwards; era guards
   still refuse double-credit both directions.
2. Full flow: multi-Adda leaver → per-Adda settlements booked + ledger
   credits; recovery + residual write-off (outstanding → 0, payable
   unaffected, PSI carries reason/actor); cash payment; `is_active=False`.
3. **PDD edge cases (§ "Edge cases to design"):** zero-payable + outstanding
   advance (write-off-only F&F) · Adda reopen after F&F participant →
   settlement armor refuses (extend existing armor test) · open tasks ⇒
   refusal listing them.
4. **Monthly F&F (ADR-0011 pin):** zero earning lines, advance write-off,
   deactivate — colleague on same stage unaffected.
5. Write-off permissions: manager refused; empty reason refused; write-off
   reversal restores outstanding.
6. Golden ₹225 byte-identical + full gate (4b/4c writer gates must stay green
   — proof no new money path).

## 6) Browser E2E (DEV data; create freely per standing authorization)
Create **DEV-Leaver** worker + assign to a fresh DEV Adda (+ reuse 3-PATTI
world): report + complete lines on 2 Addas, take a ₹500 advance, leave one
task open. Then as super-admin: F&F page shows checklist (open task blocks →
resolve via existing cancel) → preview (lines per Adda, expected ₹, advance
residual) → execute → verify settlements + write-off + payment + deactivated
login refused; worker history pages still render. Monthly variant: F&F
dev.monthly (zero lines path) — but do NOT actually deactivate dev.monthly
(still needed for later phases) — use a throwaway DEV-Monthly-2. 360 + desktop.

## 7) Risks
| Risk | Mitigation |
|---|---|
| Multi-step flow aborts midway | each step = existing atomic audited event; F&F page is resumable (recomputes what's left) |
| Draft gate blocks mid-flight Addas | P-5 refuse-with-list; explicit owner action, nothing silent |
| `only_worker` weakens era guards | it only FILTERS the funnel output — skip logic untouched; test 1 pins both directions |
| Deactivated user breaks pages | §31.2 + PROTECT; smoke worker-detail/settlement pages post-F&F in E2E |

## 8) Rollback
Migration 0014 additive/reversible; behavior = `git revert`. Executed F&Fs
are corrected the normal way: reverse settlements / reverse write-off PSI /
reactivate user — nothing new to unwind.

## 9) Acceptance criteria
- [ ] Live browser F&F of DEV-Leaver end-to-end (block → resolve → preview →
      execute → deactivated), 360 + desktop.
- [ ] Colleagues' money untouched (test 1 + E2E spot-check).
- [ ] Residual advance visible as audited write-off (reason + actor) and
      outstanding = 0; reversal restores it.
- [ ] Monthly F&F = zero lines (ADR-0011 pin).
- [ ] Gate PASS (incl. 4b/4c) + golden intact; docs synced same session.

## 10) Order (estimated)
1. `only_worker` + funnel filter + scoping tests — ~1 h
2. PSI write-off (migration 0014 + settlement_service entry + tests) — ~1 h
3. fnf_service orchestration + refusal preconditions + tests — ~1.5 h
4. UI (checklist page + worker-detail button) — ~1.5 h
5. Browser E2E (DEV-Leaver + monthly variant) + docs — ~1.5 h
Total ≈ one working day. Uncommitted (checkpoint policy).
