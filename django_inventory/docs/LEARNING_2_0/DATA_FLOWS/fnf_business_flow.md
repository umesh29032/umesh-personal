---
id: l2-data-flows-fnf-business-flow
type: data-flow
status: active
owner: handwritten
scope: fnf_business_flow (data-flow)
anchors: —
verified: 2026-07-13
---

# F&F BUSINESS FLOW — the ONE way a worker exits (Full & Final)

> **TL;DR:** worker leaves → resolve open tasks (existing flows) → settle the
> leaver's eligible earnings per Adda (engine reuse, colleagues untouched) →
> recover advances from payable → WRITE OFF the audited residual → pay cash →
> deactivate. History stays forever. **Future exit-related work references
> THIS document** (owner instruction, R7 acceptance 2026-07-05).
> PDD refs: §20, §27-D5, §31.2. Built: R7 (gate 788, live E2E 2026-07-05).
> Entry point: worker detail → "Full & Final" (super-admin only, P-4).

## The six steps

```
1. WORKER LEAVES            super-admin opens /expense/workers/<id>/fnf/
   The page is a live CHECKLIST — it recomputes on every load, so an
   interrupted F&F simply resumes from whatever is left.
        │
2. RESOLVE OPEN TASKS       BLOCKER — F&F refuses while any assigned/
   in-progress task exists, naming each (Adda/stage). Resolution uses the
   EXISTING chokepoints only: worker/management submits the report, or the
   manager removes the worker from the stage roster (audited cancel-not-
   delete). No bulk auto-cancel exists — C-TM discipline holds.
   Also a BLOCKER: an Adda whose payable stages are not all completed
   (quantities must be final before money — the §11.5 draft gate is never
   weakened; complete the stage or cancel the leaver's mid-flight work).
        │
3. SETTLE ELIGIBLE EARNINGS fnf_service → per Adda holding uncredited lines:
   finalize(only_worker=leaver) — the SAME settlement engine, the SAME
   _settleable_lines funnel (era-A/era-B/monthly guards run FIRST; the
   leaver filter applies to the OUTPUT). One AddaSettlement per Adda, items
   frozen for the leaver only. Colleagues' lines stay settleable (§11.8
   partial settlements are legal). Consequences until a reverse: that
   stage cannot reopen (armor) and that (stage, role) rate is locked.
        │
4. RECOVER ADVANCES         from payable, at settlement — the normal
   owner-chosen recovery on the settlement screens (nothing F&F-specific).
        │
5. WRITE OFF THE RESIDUAL   what recovery didn't cover is FORGIVEN on
   record (D5): a PayrollSettlementItem with write_off_reason + written_off_by
   and NO ledger debit — outstanding derives to 0, payable is untouched
   (a forgiven loan is not a payment). Super-admin + MANDATORY reason;
   reversible via the same reversed_at stamp as any recovery.
        │
6. PAY + DEACTIVATE         remaining payable → one cash PayrollSettlement
   ("F&F closure", carries the write-off lines); then is_active=False.
   §31.2: deactivation blocks LOGIN ONLY — every money flow (settle,
   reverse, re-settle, display) still works on a deactivated worker.
   PROTECT + append-only keep the full history forever.
```

## The monthly-worker path (🔒 ADR-0011)

Identical flow, three structural differences — all by construction, test-pinned:
- **Step 3 settles ZERO lines** — the funnel excludes monthly workers, so no
  AddaSettlement is created at all (their pay never flows through settlement).
- **Step 6 cash is ₹0** (payable is permanently 0) — the closure event exists
  only if there is a write-off to carry.
- Advances (legacy pre-M-2 rows; new ones are blocked) exit via step 5's
  write-off — the ONLY exit for a monthly worker's outstanding advance.
Production history, quantities, dashboards: untouched, like any worker.

## Edge cases (each pinned by a test or live probe, 2026-07-05)

| Case | Behavior |
|---|---|
| Zero payable + outstanding advance | write-off-only F&F: no settlements, ₹0 cash, PSI write-off, deactivate |
| Open task anywhere | refuse, naming Adda/stage — resolve via existing flows |
| Payable stage incomplete on an Adda with the leaver's lines | refuse, naming the stages (P-5 refuse-first; no partial-quantity money) |
| Adda shared with active colleagues | their lines untouched AND still settleable afterwards (mixed settled/unsettled state on one stage record — verified safe) |
| Reverse an F&F settlement later | leaver's lines become settleable again; ledger nets back; balance may go NEGATIVE = the already-paid cash is now an overpayment, VISIBLE and correctable (supersede → re-settle; never silent) |
| Reopen an Adda stage after F&F | BLOCKED by settlement armor until that settlement is reversed — then reopen works (armor releases) |
| Settlement queue after F&F | leaver's lines are era-B-skipped; the Adda stays queued while colleagues have uncredited lines, drops when fully credited |
| Re-run F&F on the same worker | natural resume: nothing left ⇒ no-op steps; deactivate idempotent |
| Write-off reversed later | outstanding is restored; recover normally if the worker returns, or write off again |
| Double pay | impossible: era-B skip + symmetric era-A guard + "nothing to settle" refusal — a credited line never re-enters the funnel |
| Money skipped permanently | impossible: an uncredited COMPLETED line stays settleable forever (no expiry); F&F REFUSES rather than skips |
| Settling later becomes impossible | never: deactivation blocks nothing financial (§31.2), reverse restores settleability, drafts are recomputable scratchpads |

## What F&F deliberately is NOT
- NOT a second settlement system — `fnf_service` writes nothing itself; it
  sequences the existing sole writers (adda_settlement_service /
  settlement_service / ledger via them). The money-write STOP rule applies.
- NOT one giant transaction — each step is its own audited atomic event
  (settlement ≠ payment model); an abort leaves a consistent, resumable state.
- NOT a history eraser — nothing is deleted, ever.

## Where the deeper truth lives (don't re-document)

| Facet | Canonical |
|---|---|
| earning lifecycle feeding step 3 | [stage_earnings_flow.md](stage_earnings_flow.md) |
| settlement money-write / reverse | [adda_settlement_flow.md](adda_settlement_flow.md) + CHOKEPOINTS/adda_settlement_service.md |
| monthly exclusion | [ADR-0011](../../adr/0011-monthly-salary-factory-level.md) + R4/R5 receipts |
| business intent | [PRODUCT_DESIGN_DOCUMENT.md](../../PRODUCT_DESIGN_DOCUMENT.md) §20 / §27-D5 / §31.2 |
| implementation receipt | [R7_EXECUTION_PLAN.md](../../R7_EXECUTION_PLAN.md) (status header) |

### Verification sources
Written 2026-07-05 at R7 acceptance from code verified the same day
(fnf_service, adda_settlement_service, settlement_service) + 9 R7 tests +
the live DEV-Leaver / DEV-Monthly-2 browser E2E + the pre-implementation
7-step lifecycle probe. Confidence: High.
