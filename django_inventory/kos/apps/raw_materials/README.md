---
id: app-raw-materials
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "I'm touching rolls, cloth masters, or storage — what does raw_materials own, and what does it teach about inventory consistency?"
related: [pattern-materialized-snapshot, app-production, feature-machines]
---

# raw_materials — the complete app map

> 📂 [Apps](../README.md) · [LOS home](../../README.md) — *andar:
> [URLs](urls.md) · [Views](views.md) · [Models](models.md) · [Services](services.md)*
> **This app's engineering lesson: INVENTORY CONSISTENCY + RESERVATION SYSTEMS** —
> how stock stays honest when the real world (damage, leftovers, assignment)
> keeps disagreeing with the database.

## Mental Model — read this before anything

> **A cloakroom.** Coats (rolls) check in with a numbered tag (`roll_id`,
> auto, unique). A coat is on the rack (NOT_USED), handed out (assigned to
> exactly ONE Adda — the reservation), or damaged (honestly OFF the rack,
> with a note). The rack count is never a number someone remembers — it's
> COUNTED from the tags. And a returned half-coat (leftover) goes back on
> the rack as reusable stock, not into a drawer nobody checks. *(Stock =
> tag gino, yaad nahi.)*

## Common Misconceptions

- **"Assignment happens at intake."** No — reservation happens at
  LAYERING-time (`assign_roll_to_adda`), and ONLY during the layering
  stage (service-guarded). Intake just shelves the coat.
- **"A roll can serve two Addas."** Never — 1 roll → 1 adda, enforced by
  status (`NOT_USED` required to assign) — the reservation invariant.
- **"Damage is an edit."** Damage is a STATUS with an audited reason —
  available stock must shrink honestly, never silently.
- **"Leftovers are waste bookkeeping."** Leftovers are RE-ISSUABLE stock
  (`consume_leftover` puts them back into a lay — V1.1 item-2).
- **"Stock counts are stored somewhere."** Derived — `stock_status_counts`
  / `stock_by_location` aggregate live from statuses (the derive-don't-store
  law, inventory edition).

## Real Engineering Questions

**PM: "Reserve rolls for next week's Adda in advance."**
Think: the current reservation = status flip at layering (binding, not
booking). A BOOKING is a new state (RESERVED?) → FSM extension → who may
book/release → what happens at damage-while-reserved → counts must split
available/booked → tests for every transition. The lesson: adding a
reservation TIER = adding states, not a boolean.

**PM: "Why does available stock differ from the purchase register?"**
Chain: purchases (`material_purchases_in_period`) count INTAKE; available
counts CURRENT status — damage + assignment sit between them. Reconcile by
status timeline (roll history), not by staring at totals.

**PM: "Two managers assigned the same roll simultaneously?"**
The NOT_USED guard inside the service refuses the second (state-based
idempotency); if you ever see double-assignment, that's the alarm class —
check the service path was used.

## Reading Strategy

- **Beginner:** Mental Model → [urls.md](urls.md) §§3–8 (the roll story) →
  [cloth-to-garment](../../flows/cloth-to-garment.md) step 0.
- **Intermediate:** [services.md](services.md) (the reservation verbs) →
  [models.md](models.md).
- **Senior:** the reservation ED in [services.md](services.md) → damage/
  leftover consistency semantics → the booking-tier REQ above.

## Start Here — common tasks

| Need to… | Go to |
|---|---|
| Intake rolls | [urls.md](urls.md) §4 bulk-add (SA-only — master-data lockdown) |
| Assign/reserve a roll | §8 assign → `assign_roll_to_adda` guards |
| Record damage | §7 damage — status + audited reason |
| Cloth masters (types/colors/storage) | §§9–23 — archive-first CRUD |
| Financial fields (supplier, cost/kg) | FINANCIAL_ROLES only — [people-and-roles](../../project/people-and-roles.md) walls |
| Stock numbers look wrong | Real Engineering Question #2 above + [counts-mismatch](../../debugging/counts-mismatch.md) mindset |

## What this app owns

Cloth intake + the roll registry (identity `CR-…`/roll_id, statuses,
weights, financials) · the reservation act (roll→Adda binding) · damage
accounting · masters: ClothType, ClothColor, StorageLocation · stock
dashboards (derived).

## What it does NOT own

Leftover ROWS (production's `RemainingClothOfClothRoll` — born at
layering; this app re-issues them) · roll HISTORY timeline (tracking's
pen) · what happens to cloth after assignment (production's story).

## The census

- **URLs:** 23 (`config/raw_materials/urls.py`) — [urls.md](urls.md)
- **Views:** 31 classes in 5 modules — [views.md](views.md)
- **Models:** 4 (`models.py`: ClothType 23 · ClothColor 44 · StorageLocation 77 · ClothRoll 102) — [models.md](models.md)
- **Services:** `roll_service` (the reservation brain) + `master_service` — [services.md](services.md)
- **Tests:** `test_m9_roll_gates` · `test_master_gates` · `test_master_service` · `test_leftover_reissue`

## The laws to carry in (the lesson, condensed)

1. **Reservation = a guarded state transition**, not a flag: NOT_USED →
   assigned, one holder, service-only, stage-window-only (layering).
2. **Stock is derived** from statuses — no stored counts, ever.
3. **Negative events are first-class:** damage and leftovers are honest
   states with audit, or your "available" number lies.
4. Financial fields ride the four walls (form-strip + service re-gate, certified).

## Engineering Checklist — pre-flight

- [ ] Status changes ONLY via `roll_service` verbs (state machine, not field writes)
- [ ] New status? Every count/aggregate + picker + guard reviewed (the DAMAGED comment in models.py lists them)
- [ ] Assignment-adjacent change? The layering-stage window + NOT_USED guard stay intact
- [ ] Masters: archive (`is_active`) over delete; `Model.active` pickers ([orm-and-managers](../../concepts/django/orm-and-managers.md))
- [ ] Supplier/cost-per-kg: FINANCIAL_ROLES walls re-verified (OFF-C class)
- [ ] kos-sync: this app + cloth-to-garment step 0 if intake/assignment semantics change

## Change Impact — touching this app affects

Layering (attach/quick-create call these services) · leftover re-issue ·
stock + purchase dashboards · material-spend window (expense reads) ·
roll history timelines · master pickers across production · M9/master
gate tests.

## Learning Graph

**Before:** [business-story](../../project/business-story.md) →
[cloth-to-garment](../../flows/cloth-to-garment.md).
**After:** [production Part 3](../production/urls-layering-pattern.md)
(where reserved rolls get consumed) → [pattern: materialized-snapshot](../../concepts/patterns/materialized-snapshot.md)
(weights frozen at verification).
