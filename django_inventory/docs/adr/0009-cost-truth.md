---
id: docs-adr-0009-cost-truth
type: adr
status: active
owner: frozen
scope: architecture
anchors: —
verified: 2026-07-18
---

# ADR-0009 — Cost truth: the duality, the full-cost formula, and material price semantics

Status: **ACCEPTED** (owner, 2026-06-11 — C-1 pre-deploy hardening).
Source: docs/archive/audits/ARCH_AUDIT_FOUNDATION_2026_06_11.md (cost-duality CRITICAL finding).

## Decision 1 — THE COST DUALITY (never add the two labor numbers)

For `credits_workers=True` stages, the system holds TWO measurements of the
SAME labor money:

| Measurement | What | Rate | Quantity | Where |
|---|---|---|---|---|
| **Standard cost** | `AddaStageRecord.processing_cost` | `ws.cost_rate`, role-independent | handler quantity (lay count / bundles / pieces cut) | frozen at stage advance |
| **Actual pay** | settled worker earnings | role-aware frozen `expected_rate` | reported/verified quantities | SWA lines + ledger credits at settlement |

They diverge legitimately (role-rate overrides, quantity basis, grouping,
non-payable coverage). **They are NEVER additive.** Any report summing
`processing_cost + settled labor` double-counts labor.

## Decision 2 — The full-Adda-cost formula

```
Full Adda cost = material cost (G1, cloth-only until stated otherwise)
              + ACTUAL settled labor (Σ non-voided SWA snapshots, both eras)
              + processing_cost of NON-payable priced stages only
              + overhead (future; era-stamped when introduced)
```

Standard-vs-actual labor is a future **VARIANCE report** — the declared home
for handler-quantity vs reported-quantity drift — never a component of cost.

## Decision 3 — The labor-source rule

Per-Adda actual labor = **Σ non-voided `StageWorkAssignment` earning snapshots
(both eras)**. Never `WSC.expected_*` (drops era-A history). Never
Σ `AddaSettlement` totals (partial settlements + reversed/superseded chains
mis-sum). Reference implementation: costing_views earn_map.

## Decision 4 — Grouped members never pay twice (runtime, C-1)

A grouped MEMBER stage (`cost_billed_at` set) yields NO earning rate:
`role_rate_for` returns None and the expected-rate freeze pins 0 for member
contributions. The payer stage's grouped rate covers the whole group. Enforced
in cost_service + worker_task_service; tested in test_c1_hardening.

## Decision 5 — Material price semantics (owner-amended: honest-NULL, no blocking)

- `ClothRoll.cost_per_kg` = **PURCHASE price** — a fact; corrections only,
  never a market/replacement price. (Edits are history-audited.)
- It MAY remain NULL — **unknown is never silently treated as zero.** Intake is
  NOT blocked on price (owner decision: visibility over placeholder prices).
- Consumed-but-unpriced rolls are surfaced PROMINENTLY (costing dashboard
  banner + per-Adda counts); any costing report touching material must state
  "material costing incomplete" when unpriced rolls exist.
- Leftovers are valued at their SOURCE roll's `cost_per_kg` — never re-priced.
- Leftover consumption is written ONLY by `roll_service.consume_leftover`
  (whole-piece; partial use = weigh a child leftover first; append-only).

## Consequences

- The first full-cost/profitability implementation (Costing-2) has its formula
  fixed before any report exists; ADR-0008's margin formula is amended
  accordingly (see its addendum).
- Pre-G1 Addas are labelable: material cost NULL ≠ ₹0, same honest-NULL
  discipline as `processing_cost`.
- When overhead arrives, it gets its own era stamp — historical Addas never
  silently change cost.
