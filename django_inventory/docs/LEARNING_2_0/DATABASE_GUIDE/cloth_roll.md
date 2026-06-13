# DB: ClothRoll (+ RemainingCloth) — cloth stock

## TL;DR
What: one physical roll + its leftover. Why: material input fact (future G1 cost).
Writes: roll_service (intake/assign/consume_leftover). Reads: raw-material dashboards,
costing (unpriced count). Breaks if removed: no material truth. ADRs: 0009 §5.
File: `config/raw_materials/models.py` + leftover in `production/models/layering.py`.

## ClothRoll fields (key)
roll_id (CR-seq, global, editable=False), cloth_type/cloth_color/storage_location FKs,
purchased_date, **cost_per_kg** (Decimal, null — PURCHASE fact, honest-NULL), **adda** FK
(1 roll→1 adda), status (not_used/used/…).

## RemainingCloth fields
roll FK, source_adda FK, remaining_weight_kg, remaining_length_meters, is_consumed,
consumed_in_adda FK(null).

## Example
`CR-000142, Cotton/Red, ₹200/kg, adda=3-PATTI-001, status=used`; leftover `3.10kg, is_consumed=False`.

## FK chain
`ClothRoll → ClothType/ClothColor/StorageLocation` + `→ Adda`; `RemainingCloth → ClothRoll` + `→ Adda(source/consumed)`.

## How data reaches / leaves
IN: bulk_create_rolls (intake) → assign_roll_to_adda (bind+weight) → leftover at
layering complete → consume_leftover (reuse). OUT: PROTECT; cost edits history-logged.

## SQL
```sql
SELECT roll_id,cost_per_kg,status FROM raw_materials_clothroll WHERE adda_id=<id>;
SELECT COUNT(*) FROM raw_materials_clothroll WHERE adda_id IS NOT NULL AND cost_per_kg IS NULL; -- unpriced
```

## Debug in production
Unpriced roll → NULL price (honest-NULL banner). Off-book leftover reuse →
consume_leftover not called → next Adda understated (unrecoverable).

### Verification Sources
raw_materials/models.py (ClothRoll+) + roll_service + layering.py leftover. **Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed).** ADR-0009 §5.
