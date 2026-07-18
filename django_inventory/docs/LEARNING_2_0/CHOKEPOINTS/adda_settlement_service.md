---
id: l2-chokepoints-adda-settlement-service
type: chokepoint
status: active
owner: handwritten
scope: adda_settlement_service (chokepoint)
anchors: config/expense/services/adda_settlement_service.py
verified: 2026-07-13
---

# Chokepoint: adda_settlement_service (THE money event)

> **CANONICAL** for the settlement lifecycle + lock order (binding spec:
> ARCHITECTURE_V2 §11/§11.5). The data-flow, request-journey, and DB-page views
> are facets that link here for the mechanism — they don't re-specify it.

File: `config/expense/services/adda_settlement_service.py`

**Why exists:** paisa banane ka EK hi atomic, auditable, reversible event —
Adda settle karna. settlement ≠ payment (Model A): yahan earnings book hote
hain + advances recover hote hain; cash alag.

**Owns / writes:** `AddaSettlement` + `AddaSettlementItem` (frozen snapshots) +
era-B `StageWorkAssignment` earning lines; calls ledger_service for credits/
debits; stamps `WSC.settlement_line` (provenance). CI gates **[4b/4]** (ADST)
+ **[4c/4]** (SWA).

**Who can call:** management settlement UI only (`_ensure_management`).

**Key functions:** `create_draft` (recomputable scratchpad, no money) ·
`finalize_adda_settlement` (THE write; **R7 `only_worker=` — F&F leaver-scoped
filter on the funnel OUTPUT, guards untouched; partial settlements are legal
§11.8, and the resulting mixed settled/unsettled-lines-on-one-SR state was
verified safe 2026-07-05: line-granular consumers, conservative reopen-armor
and per-(SR,role) rate lock until reverse**) · `reverse_adda_settlement`
(compensating rows + supersede chain) · `settlement_queue`/`preview_lines`/
`discard_draft`.

**Invariants protected:** a contribution line is paid AT MOST ONCE (era-A +
era-B skip guards, both directions) · **R4 (PDD §27-D4): a MONTHLY worker's
lines are structurally excluded at `_settleable_lines` (4th skip class
`skip_monthly`, one funnel = preview/queue/finalize; basis read at settlement
time; `set_pay_basis` joins advisory 5374 so a basis flip can't race
finalize)** · full provenance loop item↔SWA↔ledger↔WSC
· **lock ORDER** advisory 5374 → ADST → stage records → **WSC rows (PA-11-3: `verified_quantity` lives here, not on AddaStageRecord — locked `of=self` so a racing `set_verified_quantity` can't lost-update the settled qty)** → profiles → advances
(deadlock-safe) · recovery ≤ remaining · frozen snapshots never recomputed ·
**PA-11-2: the grouped→0 `effective_pay_rate` guard is applied at the preview surfaces
(`settlement_queue` + `_line_dict`) too, not just at finalize — preview == money-write.**

**What breaks if bypassed:** double-pay, deadlocks, unauditable money, and the
V2-3 holes (reopen/void touching settled lines — now guarded).

Lessons: [../../LEARNING/06_FINANCIAL_TRUTH_AND_SETTLEMENT.md](../../LEARNING/06_FINANCIAL_TRUTH_AND_SETTLEMENT.md) ·
ADR [0005](../../adr/0005-production-truth-vs-financial-truth-option-b.md)/[0007](../../adr/0007-allocation-era-ledger-cutover.md).
Journey: [../REQUEST_JOURNEYS/settlement_finalize.md](../REQUEST_JOURNEYS/settlement_finalize.md).

---
## v2 — VERIFIED execution trace (finalize)

Traced from `config/expense/services/adda_settlement_service.py:finalize_adda_settlement`
(, read 2026-06-12).

**Files in execution order:**
1. `expense/views.py:AddaSettlementDetailView.post` (action=finalize, parse inputs, gate)
2. `expense/services/adda_settlement_service.py:finalize_adda_settlement` (the atomic body)
3. `expense/services/ledger_service.py:log_credit/log_debit` (money rows)
4. `tracking/services/history_service` via `tracking.services.log_adda` (timeline)

**Transaction boundary + lock order (verified,:**
```
@transaction.atomic pg_advisory_xact_lock(5374) # global settlement lock AddaSettlement.select_for_update # this ADST row AddaStageRecord.select_for_update # freeze stage records WorkerStageContribution.select_for_update(of=self) # PA-11-3: freeze verified_quantity (the settled qty lives HERE) WorkerProfile.select_for_update # per settled worker WorkerAdvance.select_for_update # advances
```

**Models touched, in order (verified:**
```
per contribution line: StageWorkAssignment.objects.create(...) INSERT (era-B earning line) c.settlement_line = swa ; c.save UPDATE WSC (provenance) ledger_service.log_credit(assignment=swa) INSERT ledger credit
per recovery: ledger_service.log_debit(...) INSERT ledger debit PayrollSettlementItem.objects.create(...) INSERT recovery line
per worker: AddaSettlementItem.objects.create(...) INSERT (frozen snapshot)
finally: settlement.status = FINALIZED ; save UPDATE log_adda(SETTLEMENT_FINALIZED) INSERT AddaHistory
```

**DB state change (before → after):** see the full row dump in
[../REQUEST_JOURNEYS/settlement_finalize.md](../REQUEST_JOURNEYS/settlement_finalize.md) §12 (verified consistent with this trace).

**Common mistakes (observed in this session's work):** RunPython placed in
`dependencies` not `operations` (migration crash); `select_for_update` on a
nullable-FK `select_related` (Postgres refuses → use `of=("self",)`); summing
processing_cost + settled labor (double-count, ADR-0009).

### Verification Sources
- Read: `expense/services/adda_settlement_service.py` (finalize.
- Models inspected: `expense/models.py` (AddaSettlement, Item, SWA, PSI).
- ADRs: 0002, 0005, 0007, 0009.
- Confidence: **High** — verified against commit f067daf0 (2026-06-12); re-verify the cited file if it changed (line-level trace from current code).
