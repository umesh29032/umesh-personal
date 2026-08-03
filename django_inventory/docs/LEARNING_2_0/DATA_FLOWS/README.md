---
id: l2-data-flows-readme
type: entry-index
status: active
owner: handwritten
scope: documentation system
anchors: —
verified: 2026-07-13
---

# DATA FLOWS — input → validation → writes → constraints → future

> Per-flow data view (complements REQUEST_JOURNEYS' call-chain view). ASCII
> diagrams. Exemplar: [worker_reporting_flow.md](worker_reporting_flow.md).

| Flow | File | Status |
|---|---|---|
| Worker reporting | [worker_reporting_flow.md](worker_reporting_flow.md) | ✅ exemplar |
| Adda settlement | [adda_settlement_flow.md](adda_settlement_flow.md) | ✅ |
| Advance | [advance_flow.md](advance_flow.md) | ✅ |
| Payment | [payment_flow.md](payment_flow.md) | ✅ |
| Allocation (era-A) | [allocation_flow.md](allocation_flow.md) | ✅ |
| Costing | [costing_flow.md](costing_flow.md) | ✅ |
| Material (roll→leftover) | [material_flow.md](material_flow.md) | ✅ |
| **Stage earnings — GENERIC lifecycle (every earning stage references this, never re-documents it)** | [stage_earnings_flow.md](stage_earnings_flow.md) | ✅ R2 2026-07-04 |
| **Full & Final — the ONE worker-exit flow (incl. monthly path, ADR-0011)** | [fnf_business_flow.md](fnf_business_flow.md) | ✅ R7 2026-07-05 |

Full data-model + write-flow already documented: [../../LEARNING/02_DATABASE_RELATIONSHIPS.md](../../LEARNING/02_DATABASE_RELATIONSHIPS.md).
