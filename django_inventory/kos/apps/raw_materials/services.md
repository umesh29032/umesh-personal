---
id: app-raw-materials-services
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "roll_service + master_service — the reservation brain's verbs, guards, and failure modes."
related: [app-raw-materials, concept-single-writer]
---

# raw_materials — service knowledge

> 📂 [raw_materials app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

> 💡 **Samjho aise** — Services = **counter ke peeche baitha clerk**
>
> **Asli kaam yahin hota hai** — database mein likhna, hisaab lagana, rules lagana. Is project ka sabse bada niyam: *har likhne ka kaam service mein hoga, view mein kabhi nahi*. Isi wajah se paisa surakshit rehta hai — har table ka **ek hi** likhne wala hota hai.
>
> *(`raw_materials` app ka kaam: **kapda** — roll, cloth type, colour, storage.)*

## `roll_service.py` — the reservation brain 🔒 (sole writer of ClothRoll)

| Verb | Job · guards |
|---|---|
| `bulk_create_rolls` | intake [@atomic]: N rolls, serialized `_next_roll_id` |
| `update_roll_details` | edits with the financial re-gate (wall #3) |
| `assign_roll_to_adda` ⭐ | THE reservation: NOT_USED guard (one holder) + layering-stage window + verified weight/width at hand-out + history event — [urls §8](urls.md) has the full ED |
| `consume_leftover` | re-issue a production leftover into a new lay (V1.1) — stock honesty's second half |
| `stock_status_counts` / `stock_by_location` | the DERIVED boards (grouped aggregates — no stored counts) |
| `material_purchases_in_period` | the purchase view (feeds expense's material-spend window) |

**Failure modes = the curriculum:** already-used roll (state idempotency) ·
wrong-stage assignment (process-window) · both refuse with sentences that
teach.

## `master_service.py` — the three masters' pen

Create/update/archive/delete for types/colors/storage; delete refuses on
references (PROTECT surfaces as a clean message). Gates certified
(`test_master_gates`).

## The lesson, stated once (inventory consistency + reservations)

Consistency = (1) ONE pen per stock table, (2) state transitions with
guards instead of writable flags, (3) counts derived at read time,
(4) negative events (damage, leftovers) modeled as first-class states with
audit. Reservation = the guarded transition NOT_USED→bound, inside a
process window, with the contested resource re-checked UNDER the
transaction — the same check-then-act discipline as
[payroll's races](../expense/urls.md), applied to cloth instead of cash.

## Adding/changing here — the checklist

New status → sweep every consumer the DAMAGED comment lists → new
transition = verb + guards + refusal pin → counts stay derived → kos-sync.

## Required Knowledge (this page)

- [ ] check-then-act + state guards → [locks](../../concepts/postgresql/locks.md) · [transactions](../../concepts/django/transactions.md)
- [ ] single-writer → [single-writer](../../concepts/architecture/single-writer.md)

## Learning Graph

**Before:** [models.md](models.md). **After:**
[production Part 3](../production/urls-layering-pattern.md) (attach-roll =
this service consumed) → the booking-tier REQ in [README](README.md).
