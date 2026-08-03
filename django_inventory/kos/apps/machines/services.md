---
id: app-machines-services
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "machine_service's 8 verbs — registry, checkout/checkin, derived availability."
related: [app-machines, concept-single-writer]
---

# machines — service knowledge (`services/machine_service.py`)

> 📂 [machines app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)
> Sole writer of Machine + MachineAssignment (+ `create_machine_type` as
> the service-side door to production's master).

> 💡 **Samjho aise** — Services = **counter ke peeche baitha clerk**
>
> **Asli kaam yahin hota hai** — database mein likhna, hisaab lagana, rules lagana. Is project ka sabse bada niyam: *har likhne ka kaam service mein hoga, view mein kabhi nahi*. Isi wajah se paisa surakshit rehta hai — har table ka **ek hi** likhne wala hota hai.
>
> *(`machines` app ka kaam: factory ki machinein aur kis worker ke paas kaunsi machine hai.)*

| Verb (line) | Job |
|---|---|
| `machines_with_holder` (21) | the board read: units + DERIVED current holder (open-window join) |
| `open_assignment_for` (33) | one unit's open window (the "now" question) |
| `register_counts` (42) | crib totals — derived, never stored |
| `create_machine_type` (57) | kind creation (writes production's master through one door) |
| `create_machine` (73) / `update_machine` (88) | unit registry |
| `assign` (121) ⭐ | THE checkout: active-unit + no-open-window guards → window INSERT; DB partial unique backs the race |
| `release` (150) ⭐ | THE checkin: stamps `end_at`; refuses re-release |

**Failure modes = designed refusals:** held (names holder) · inactive ·
already released. **The lesson stated once:** capability questions
(can this stage run?) are JOINS over requirement×unit×window — model the
three cleanly and every "scheduling" feature starts as a read.

## Adding/changing — checklist

Possession semantics → these two verbs only · booking/scheduling = new
states + overlap plan (owner conversation) · counts stay derived ·
kos-sync with [feature: machines](../../features/machines.md).

## Required Knowledge (this page)

- [ ] Evidence-over-state → [append-only-tables](../../concepts/database-design/append-only-tables.md)

## Learning Graph

**Before:** [models.md](models.md). **After:** [production models](../production/models.md)
(Stage requirements — the capability consumer).
