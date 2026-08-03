---
id: l2-data-flows-material-flow
type: data-flow
status: active
owner: handwritten
scope: material_flow (data-flow)
anchors: —
verified: 2026-07-13
---

# Data flow: Material (roll → Adda → leftover)

## TL;DR
Cloth intake → bind to one Adda at layering (weight) → mandatory leftover weigh-in
at completion → optional reuse via consume_leftover. These facts feed future G1 costing.

```
intake (BulkRollForm) → financial role for price → roll_service.bulk_create_rolls INSERT ClothRoll (status=not_used, price optional)
assign (layering) → layering stage only → roll_service.assign_roll_to_adda UPDATE roll.adda + status=used
complete layering → leftover weigh-in REQUIRED → RemainingClothOfClothRoll INSERT (weight/length)
reuse in Adda B → management, whole-piece → roll_service.consume_leftover UPDATE is_consumed/consumed_in_adda
```
**Reads:** ClothRoll, RemainingCloth. **Writes:** raw_materials_clothroll,
production_remainingclothofclothroll (+ ClothRollHistory on edits). **Tx:** atomic.
**Net consumed** = attach weight − Σ leftover (derivable retroactively for G1).

### Debug entry points
`raw_materials/services/roll_service.py` (bulk_create / assign / consume_leftover);
query `raw_materials_clothroll WHERE adda_id=` + `production_remainingclothofclothroll`;
log roll service logs. Failure: unpriced roll (honest-NULL banner); off-book reuse
(leftover not consumed → next Adda's cloth cost understated — UNRECOVERABLE).
Recovery: cost_per_kg edits are history-logged; leftover consumption is append-style.

### Period reads (P17 RMX, 2026-07-18 — READ-ONLY, no new writers)
The same writes above now feed two period aggregates: purchases =
`roll_service.material_purchases_in_period` (rolls created in month; damaged
INCLUDED per RMX-D9) · consumption = `cost_service.material_consumption_in_period`
(the derive law time-sliced: +entries −remnants +leftover-ins at source price).
Separate LABELLED bases — never blended; one-rupee-once pinned
(`test_rmx_read_paths.py`). Consumer: `/expense/material-spend/`.

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (roll_service bulk/assign/consume_leftover; RemainingCloth model). ADR-0009 §5. **P17 period-reads note verified from code 2026-07-18.**
