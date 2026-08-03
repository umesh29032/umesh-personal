---
id: l2-data-flows-stage-earnings-flow
type: data-flow
status: active
owner: handwritten
scope: stage_earnings_flow (data-flow)
anchors: —
verified: 2026-07-13
---

# STAGE EARNINGS FLOW — the ONE lifecycle every earning-enabled stage follows

> **TL;DR:** configure the stage → assign workers → each worker reports OWN
> quantities → contribution rows (immutable) → rates frozen per Adda → expected
> earnings (visibility) → settlement (the only money gate) → append-only ledger.
> **Future earning stages reference THIS document instead of re-documenting the
> lifecycle** (owner instruction, R2 acceptance 2026-07-04). A new stage adds
> ZERO earning code — only configuration + (optionally) a schema override.
>
> Proven end-to-end by Layering (roadmap R2): 45 layers × ₹10 = ₹450 expected,
> settled to per-worker ledger credits — HISTORICAL proof: layering later
> became production-input-only/non-payable (stage-trio spec 2026-07-05); the
> LIVING proofs are Pattern Design (fixed ₹) + Cutting (per-piece), both
> settled on the real 3-PATTI flow. PDD refs: §14 §17 §18, §27-D1/D2.

## The eight steps

```
1. CONFIGURATION            Flow Editor (super-admin), per product × stage
   WorkflowStage: cost_method (per_piece|per_bundle|per_layer|fixed_cost)
                  cost_rate (₹/unit, dual-duty ADR-0009)
                  cost_billed_at (grouping — member stages pay ₹0, C-1/F2)
                  credits_workers  ← the PAYABILITY switch (PAY-2 reads it)
   WorkflowStageRoleRate: optional per-role overrides
        │
2. ASSIGNMENT               manager · worker_task_service.set_stage_workers
   WorkerStageTask per (stage_record, worker); ≤1 ACTIVE per pair (DB);
   un-assign = CANCELLED, never deleted. Assignment + skill = access (§10).
        │
3. WORKER REPORT            worker phone · /addas/<code>/report/<stage>
   Fields come from the handler's contribution_schema() — schema metadata
   drives the UI (Layering: "Layers laid"; Cutting: colour+size+qty).
   Each worker reports ONLY their own work (PDD §27-D1). Drafts allowed;
   drafts are NOT business truth.
        │
4. CONTRIBUTION             worker_task_service.report_contributions (C-TM:
   the ONLY door — manual today, barcode tomorrow, same chokepoint)
   WorkerStageContribution rows: good/alter/missing quantities; good = the
   payable count (§27-D2); reported numbers IMMUTABLE after submit —
   corrections go to verified_quantity (management), both preserved.
        │
5. SNAPSHOT                 automatic, two moments (PDD §12 freeze map)
   Adda/stage START: AddaStageRoleRate freezes the resolved ₹/unit per
   (stage_record, role) — later flow-editor edits never touch started work.
   Task COMPLETE: worker's role + expected_rate frozen onto each line.
   Correctable until settlement ONLY via audited super-admin rerate (S1.1).
        │
6. EXPECTED EARNINGS        complete_worker_task
   expected_earning = good_quantity × frozen rate. VISIBILITY ONLY — never
   money (ADR-0005 Option B). Shown instantly: My Work (Adda page) +
   My Earnings "Expected (unsettled)". Grouped stage → rate forced 0 (F2).
   PAY-2: a credits_workers stage REFUSES completion until ≥1 completed
   report — earnings must be backed by recorded work (owner P-4).
   C3 (R3): completion also BLOCKS while any worker is mid-work
   (IN_PROGRESS — transitional scope until the explicit-assignment
   migration); Super-Admin override with mandatory audited reason
   (COMPLETION_OVERRIDE on the Adda timeline). PAY-2 runs first; the
   override never bypasses PAY-2.
        │
   DOWNSTREAM POOL (J-1, owner rule 2026-07-06): the same verified-else-good
   number (= verified ?? good) is what `pool_service.materialize_stage_pool`
   freezes into the next operation's StagePoolSnapshot — the next stage never
   receives a quantity that was corrected away at verification. Same resolver,
   applied independently to capacity (pool) and money (settlement).
        │
7. SETTLEMENT               adda_settlement_service (sole writer) — the ONE
   money gate. DRAFT (no money) → FINALIZE: per line, settlement_quantity
   (= verified ?? good) × effective rate → StageWorkAssignment earning line
   + frozen AddaSettlementItem; owner-chosen advance recovery. Corrections:
   REVERSE / REVERSE+SUPERSEDE — never edit.
   R4 (PDD §27-D4): a MONTHLY worker (WorkerProfile.pay_basis — worker-level,
   never the stage) keeps steps 1-6 (production truth + analytics) but the
   funnel structurally EXCLUDES their lines here (labeled skip class in the
   draft) — salary is paid via Expenses; ₹ expectation is suppressed in step
   6's displays (badge instead, never ₹0.00). Basis is read at settlement
   time; switching back to piece-rate makes uncredited lines payable again.
        │
8. LEDGER                   ledger_service (sole writer), append-only
   CREDIT stage_earning at finalize; DEBIT advance_recovery /
   settlement_payment (cash = separate PayrollSettlement event). Balances
   always LIVE SUMs — never stored. Worker sees Expected → Earned → Paid
   (non-overlapping, proven by tests + golden ₹225).
```

## Adding the NEXT earning stage (the whole recipe)

1. Stage already in the flow? Then it is ONLY configuration: flow editor →
   cost_method + rate (+ role rates) + ungrouped + **Pays workers** ✓.
2. Different reporting fields/unit? Override `contribution_schema()` in the
   stage's handler (see `stages/layering/handler.py` — ~10 lines). The report
   UI, parser, freeze, settlement, and ledger all follow automatically.
3. Nothing else. No earning code, no settlement code, no ledger code. If you
   are writing any of those for a new stage, you are outside the architecture —
   stop (PDD §30, CI single-writer gates will fail you anyway).

Per-stage quirks (e.g. Layering's Σ-reported vs lay_count reconciliation WARN)
live in that stage's handler/service and its own doc — they never duplicate
this lifecycle.

A360 follow-up (owner one-rule directive, 2026-07-05): a NON-PAYABLE stage
(`credits_workers=False`) now freezes rate 0 / earning 0 — EXACTLY like a
grouped member, via the same `effective_pay_rate` chokepoint (F2). No hidden
expectations anywhere: freeze, rerate, settlement, and every dashboard agree.

R8 proved the recipe twice on the REAL 3-PATTI flow (2026-07-05): Pattern
Design = `fixed_cost` ₹500 with a CHECKLIST report (schema mode='checklist',
one contribution qty=1 — fixed pay is literally rate×1 through this exact
lifecycle; a chokepoint guard refuses a second completed report on a fixed
stage) · Cutting = per_piece ₹100 (config only). Layering is now
production-input-only (`credits_workers=False` — steps 5-8 simply never
engage; steps 1-4 unchanged).

## Where the deeper truth lives (don't re-document)

| Facet | Canonical |
|---|---|
| report path call-chain | [worker_reporting_flow.md](worker_reporting_flow.md) + CHOKEPOINTS/worker_task_service.md |
| settlement money-write | [adda_settlement_flow.md](adda_settlement_flow.md) + CHOKEPOINTS/adda_settlement_service.md |
| rates/costing duality | [costing_flow.md](costing_flow.md) + ADR-0009 + CHOKEPOINTS/cost_service.md |
| business intent | [../../PRODUCT_DESIGN_DOCUMENT.md](../../PRODUCT_DESIGN_DOCUMENT.md) §14/§17/§18 |
| freeze map | PDD §12 |

### Verification Sources
Written 2026-07-04 at R2 acceptance, from code verified the same day
(worker_task_service, stage_rate_service, adda_settlement_service,
flow_service, layering handler/service) + the live 3-PATTI-006 browser E2E.
Confidence: High.
