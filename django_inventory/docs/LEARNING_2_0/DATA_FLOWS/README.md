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

Full data-model + write-flow already documented: [../../LEARNING/02_DATABASE_RELATIONSHIPS.md](../../LEARNING/02_DATABASE_RELATIONSHIPS.md).
