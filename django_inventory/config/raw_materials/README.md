# `raw_materials` app — Cloth Inventory (the factory's input side)

> Dual-register guide (developer + owner). Canonical production-subsystem doc:
> [docs/production/RAW_MATERIALS.md](../../docs/production/RAW_MATERIALS.md) ·
> material price/valuation rules: [ADR-0009 §5](../../docs/adr/0009-cost-truth.md).

## Purpose & business responsibility

Kapde ka stock: kaunsa roll aaya, kahan rakha hai, kis Adda mein use hua,
kitna bacha. **Owns: cloth identity + consumption facts.** Does NOT own
costing math (that's derived later, G1) or production progress.

## Models (business + database meaning)

| Model | Business | DB / lifecycle | Example row |
|---|---|---|---|
| `ClothType` | "Cotton", "Rib" | master row, soft `is_active` | `name='Cotton'` |
| `ClothColor` | "Red - 42 inch" | master row + hex swatch | `name='Red', hex='#c0392b'` |
| `StorageLocation` | rack/room | master row | `name='Rack A'` |
| `ClothRoll` | ONE physical roll | `roll_id='CR-000142'` (global sequence, ADR-0010); binds to exactly ONE Adda forever via `adda` FK; `cost_per_kg` = PURCHASE price, may be NULL (honest-NULL — never guess) | `CR-000142, Cotton/Red, 25.40kg, ₹200/kg, adda=3-PATTI-001, status=used` |

Related (lives in production app, written here-adjacent):
`LayeringRollEntry` (per-roll verify at attach) and
`RemainingClothOfClothRoll` (leftover with weight — MANDATORY at layering
completion; reuse recorded ONLY via `consume_leftover`).

## How data flows through this app

```
intake (BulkRollForm) ─▶ ClothRoll rows (status=not_used, price optional)
        │ assign_roll_to_adda (LAYERING stage only, weight required)
        ▼
 roll.adda set + status=used  ──▶ layering records weights/layers
        │ completion: leftover weigh-in MANDATORY per roll
        ▼
 RemainingClothOfClothRoll (provenance: roll + source_adda)
        │ physical reuse in another Adda?
        ▼
 consume_leftover (sole writer) → is_consumed + consumed_in_adda stamps
```

**What records are written & by whom:** roll INSERTs + detail edits →
`roll_service` (`bulk_create_rolls`, `update_roll_details` — edits are
history-logged via tracking) · adda binding → `assign_roll_to_adda` ·
leftover consumption → `consume_leftover` (C-1; management-only, row-locked).

**Why this design / what breaks if bypassed:** consumption is the raw fact
G1 material-costing will value retroactively. Off-book reuse (leftover used
without `consume_leftover`) is UNRECOVERABLE history — Adda B's cloth cost
stays understated forever (owner's backfill-known-facts rule forbids
inventing it later). Editing `cost_per_kg` as a "market price" silently
revalues every historical Adda — it is a purchase FACT (ADR-0009).

## Views

Dashboards + roll list (DataTables, stacked cards on phone — F1 fixed),
bulk intake form (price fields visible to financial roles only), roll detail.

## Common mistakes

1. Don't set `is_consumed`/`consumed_in_adda` by hand — only the service.
2. Don't "update" cost_per_kg to today's market rate — corrections only.
3. Unpriced roll ≠ free roll: NULL surfaces on the costing dashboard banner.
4. A roll never splits across Addas — leftovers are the split mechanism.

## Django Learning Notes

- **Sequence-generated IDs** (`CR-XXXXXX`): editable=False; globally unique
  forever (ADR-0010 §1 — factory #2 shares the sequence).
- **PROTECT on roll FKs**: a roll referenced by layering entries can't be
  deleted — physical history.
- **Role-gated form fields**: the intake form POPS `cost_per_kg` for
  non-financial users (`fields.pop`) — gating belongs in the form layer,
  display mein nahi.
- **Non-negative form guard (PA-08)**: `BulkRollForm.cost_per_kg` +
  `AssignRollForm.weight_kg` carry `min_value=0`. These are plain `forms.Form`
  (no model-constraint validation), so without it a negative slips past
  validation and only trips the DB CheckConstraint at INSERT → `IntegrityError`
  → 500. (`RollEditForm` is a ModelForm → Django validates the CheckConstraint in
  `full_clean`, so it is already graceful.)
- **Honest-NULL**: nullable Decimal + dashboard surfacing instead of
  default-0 — "pata nahi" aur "zero" alag cheez hai.

## Related ADRs: 0009 (price semantics, leftover write path) · 0010 (global IDs).

## Real factory example

20 rolls aaye Cotton Red ke. Intake → CR-000201..220 (accountant ne ₹190/kg
bhara). Layering pe 3 roll 3-PATTI-002 se bind hue (weight verify), complete
pe har roll ka bacha hua tukda weigh hua (RemainingCloth rows). Mahine baad
ek leftover 3-PATTI-005 mein lag gaya → manager ne consume_leftover se record
kiya. G1 aane par: 3-PATTI-002 ka cloth cost = (attach weight − leftovers) ×
₹190 — bina kisi backfill ke, kyunki facts pehle se sahi likhe the.
