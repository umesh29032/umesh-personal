---
id: app-raw-materials-models
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "raw_materials' 4 models — the roll FSM, the reservation binding, and the three masters."
related: [app-raw-materials]
---

# raw_materials — model knowledge (`models.py`, 4 models)

> 📂 [raw_materials app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

## `ClothRoll` (line 102) — the star

- **Identity:** `roll_id` unique, auto, non-editable (`_next_roll_id`) —
  the cloakroom tag.
- **The FSM (the lesson):** `NOT_USED` → assigned-to-Adda (the reservation:
  `adda` FK set at layering-time, 1→1) · `DAMAGED` (honest removal; the
  in-code comment enumerates every consumer that must respect it — read
  it, it's the checklist).
- **Verified-at-hand-out:** `weight_kg`/width recorded at ASSIGNMENT, not
  intake — the number that matters is the number when cloth leaves the rack
  ([pattern: materialized-snapshot](../../concepts/patterns/materialized-snapshot.md)).
- **Financial fields:** supplier / cost-per-kg — FINANCIAL_ROLES walls.
- **PROTECT FKs** to type/color (masters can't vanish under rolls).
- Writers: `roll_service` only. History: tracking's `ClothRollHistory`.

## The masters (3)

**`ClothType` (23)** · **`ClothColor` (44)** · **`StorageLocation` (77)** —
archive-first (`is_active` + `active` manager), PROTECT-referenced,
rows-not-code ([pattern](../../concepts/patterns/configuration-over-code.md)).
Colors deserve respect: they key production breakups downstream.

## Where the leftover lives (not here — on purpose)

`RemainingClothOfClothRoll` is a PRODUCTION model (born at layering,
re-issued via `consume_leftover`) — the remainder is a production FACT
about a lay, not intake stock. Cross-app custody drawn where the truth is
born.

## Cross-model laws

Stock = derived from statuses · reservation = state transition ·
negative events = first-class states · masters archive, never vanish.

## Required Knowledge (this page)

- [ ] FSM thinking → [stage-tracking §DSA](../../features/stage-tracking.md)
- [ ] Soft-archive → [orm-and-managers](../../concepts/django/orm-and-managers.md)

## Learning Graph

**Before:** README. **After:** [services.md](services.md) — the only pen.
