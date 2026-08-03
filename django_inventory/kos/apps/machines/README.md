---
id: app-machines
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "I'm touching machines, possession, or stage machine-requirements — and what does this app teach about capability modeling?"
related: [feature-machines, app-production, pattern-configuration-over-code]
---

# machines — the complete app map

> 📂 [Apps](../README.md) · [LOS home](../../README.md) — *andar:
> [URLs](urls.md) · [Views](views.md) · [Models](models.md) · [Services](services.md)*
> **This app's engineering lesson: CAPABILITY MODELING + RESOURCE
> CONSTRAINTS** — the difference between what a task NEEDS (a capability),
> what the floor HAS (units), and who HOLDS one right now (availability).

## Mental Model — read this before anything

> **A tool crib with a signboard.** The signboard (MachineType) says what
> KINDS of tools exist — that's what job-plans reference ("this stage needs
> an overlock"). The crib holds UNITS (Machine) — that's what workers
> check OUT and back IN (MachineAssignment windows, one holder at a time).
> **Requirement points at the sign; possession points at the unit; NEVER
> cross them.** Availability = an empty hook, computed by looking, not by
> a ledger someone forgot to update. *(Board par KISM, hook par UNIT.)*

## Common Misconceptions

- **"Stages need machine #3."** Stages need a TYPE (capability). Which
  UNIT satisfies it is a floor-time decision — that split IS the lesson.
- **"Assignment is a field on Machine."** It's a time WINDOW (append-only
  row); the current holder is DERIVED (the open window) — evidence over
  state, again.
- **"Two people can't hold one machine because the UI prevents it."** The
  DB prevents it — partial unique on the open window (race-proof).
- **"This app schedules work."** It records POSSESSION. Scheduling
  (booking future windows) is a documented FUTURE, not a hidden feature.

## Real Engineering Questions

**PM: "Show which stages are BLOCKED because no machine of their type is free."**
Think: requirement (stage → type) ∩ availability (units of type with no
open window) → a derived join, zero new state → where: production stage
panels read `machines_with_holder`/counts → the lesson: constraint
VISIBILITY is a read problem when the model is right.

**PM: "Book the overlock for tomorrow's Adda."**
Scheduling = FUTURE windows → overlap prevention becomes real (today's
invariant is 'one OPEN window'; booked windows need interval-overlap
guards — PG `EXCLUDE USING gist` is the escalation, [feature §DSA](../../features/machines.md))
→ new states + release semantics + no-show handling. A real project, not a field.

**PM: "A machine broke mid-shift."**
Status flip (active→inactive-class) + release the open window with a note
→ requirement-bearing stages show the constraint (question #1's view).

## Reading Strategy

- **Beginner:** Mental Model → [urls.md](urls.md) §§4–5 (checkout/checkin) →
  [feature: machines](../../features/machines.md).
- **Intermediate:** [models.md](models.md) (the three-way split) → [services.md](services.md).
- **Senior:** the capability-vs-availability REQs above → the scheduling ED
  in [urls.md](urls.md) §4 → production's work-type constraint ([production models](../production/models.md) Stage row).

## Start Here — common tasks

| Need to… | Go to |
|---|---|
| Register/edit machines | [urls.md](urls.md) §§1–3 |
| Hand a machine to a worker / take it back | §§4–5 (assign/release) |
| Machine KINDS (types) | production's masters — [production urls-core §machine-types](../production/urls-core.md) (custody there: types live beside stage requirements) |
| Stage says "needs a machine" | `Stage.work_type=Machine ⇒ MachineType` (DB CHECK) — [production models](../production/models.md) |
| Who holds what right now | [services.md](services.md) `machines_with_holder` (derived) |
| History of possession | windows themselves = the history ([feature](../../features/machines.md)) |

## What this app owns

Machine UNITS (code-unique registry, status) · possession WINDOWS
(assign/release, one open holder — DB-enforced) · the availability reads.

## What it does NOT own

Machine TYPES (production's master — they live beside the stage
requirements that reference them; custody follows the consumer) · stage
REQUIREMENTS (production's `Stage.work_type`/`machine_type`) · scheduling
(future — honestly absent).

## The census

- **URLs:** 5 (`config/machines/urls.py`, 14 lines) — [urls.md](urls.md)
- **Views:** 5 + a form + a gate mixin, one `views.py` — [views.md](views.md)
- **Models:** 2 here (`Machine`, `MachineAssignment`, `models.py` 101 lines; `MachineType` lives in production) — [models.md](models.md)
- **Services:** `machine_service.py` (8 verbs) — [services.md](services.md)
- **Tests:** `test_r10a.py`

## The laws to carry in (the lesson, condensed)

1. **Requirement → TYPE; possession → UNIT** — never let a plan reference
   a unit or a checkout reference a type.
2. **Availability is derived** (open-window query), never stored.
3. **One open holder = a DB partial unique**, not an app promise.
4. Windows are append-only — release CLOSES, never deletes.

## Engineering Checklist — pre-flight

- [ ] New constraint on machines? Express it at the right layer: capability
      (type/stage), unit (status), or possession (window guards)
- [ ] Possession changes ONLY via `assign`/`release` (the two verbs)
- [ ] Anything time-based (booking) = new states + overlap strategy — an
      owner conversation, not a quick field
- [ ] kos-sync: this app + [feature: machines](../../features/machines.md) together

## Change Impact — touching this app affects

Stage panels showing machine context (production) · worker report context
(`_resolve_machine_code`) · the Stage work-type DB CHECK's meaning ·
R10-A tests · the machines feature page.

## Learning Graph

**Before:** [feature: machines](../../features/machines.md) (the WHY) →
[people-and-roles](../../project/people-and-roles.md).
**After:** [production urls-core masters](../production/urls-core.md) →
[pattern: append-only-ledger](../../concepts/patterns/append-only-ledger.md)
(windows = the pattern on physical assets).
