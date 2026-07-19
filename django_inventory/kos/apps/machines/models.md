---
id: app-machines-models
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Machine + MachineAssignment (and why MachineType is NOT here) — the three-way capability split in schema."
related: [app-machines, feature-machines]
---

# machines — model knowledge (`models.py`, 101 lines · 2 models + 1 guest)

> 📂 [machines app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

## The three-way split (the lesson in schema form)

| Concept | Model | Lives | Referenced by |
|---|---|---|---|
| **Capability (KIND)** | `MachineType` | **production** core.py (guest here) | Stage requirements (`work_type=Machine ⇒ machine_type`, DB CHECK) + units |
| **Unit** | `Machine` (20) | here | possession windows |
| **Possession** | `MachineAssignment` (62) | here | nothing — it's the leaf/history |

**Why MachineType lives in production:** custody follows the CONSUMER —
requirements (stages) reference types constantly; this app only points at
them. Same custody logic as Role→accounts ([inventory models](../inventory/models.md)).

## `Machine` (line 20)

`code` unique · name · `machine_type` FK (PROTECT — a kind can't vanish
under units) · `Status` (active/…): retirement = status, no delete route.

## `MachineAssignment` (62)

machine FK · worker FK · optional adda FK (context) · `start_at` /
`end_at` (NULL = OPEN) · **the crown constraint: partial unique on
(machine) WHERE end_at IS NULL** — one open holder, race-proof, Django
5.0.1 `condition=` flavor ([constraints — the pg_indexes gotcha](../../concepts/postgresql/constraints.md)).
DateTime grain → same-day sharing = sequential windows.

## Cross-model laws

Availability derived (open-window query) · windows append-only ·
requirement never references a unit · unit never references a stage.

## Required Knowledge (this page)

- [ ] Partial uniques as referees → [constraints](../../concepts/postgresql/constraints.md)
- [ ] Interval thinking → [feature §DSA](../../features/machines.md)

## Learning Graph

**Before:** README. **After:** [services.md](services.md).
