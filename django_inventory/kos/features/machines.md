---
id: feature-machines
type: feature
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "How does the factory know which operator holds which machine right now — and who held it last Tuesday?"
related: [feature-stage-tracking, project-people-and-roles]
---

# Machines — possession windows, not assignments

> 📂 [Features](README.md) · [KOS home](../README.md) — *pehle yeh page, phir code.*

## Business Purpose

Machines are expensive, shared, and mobile ("kal Raju ke paas thi, aaj
kiske paas hai?"). The business needs two answers at all times: *who holds
this machine NOW* and *who held it at any past moment* — for accountability
(damage, output quality) and planning. R10-A models exactly that, nothing more.

## Mental Model

> Model **possession as time windows, not a pointer.** A `current_holder`
> FK answers "now" but destroys history every reassignment. An append-only
> window (holder, from, to) answers now (open window) AND any past instant
> (window containing t). Same evidence-over-state law as the ledger — this
> time for physical assets.

## 💡 Samjho Aise

Library ki register-entry jaisa: kitab (machine) issue hui — entry khuli;
wapas aayi — entry band. "Abhi kiske paas?" = jiski entry khuli hai.
"Pichhle mangalwar kiske paas thi?" = us din ki entry padho. Register mein
kabhi cutting nahi — nayi entry hi hoti hai.

## Technical Deep Dive

**Three models** (machines app, R10-A):
- `MachineType` — the KIND (e.g. overlock). **Stages point at TYPES, never
  instances** — a workflow needs "an overlock", not "overlock #3".
- `Machine` — the physical asset: unique `code`, status, its type.
- `MachineAssignment` — the possession window: machine · worker · (optional
  adda context) · started/ended DateTimes. **One OPEN window per machine**,
  enforced by a partial unique (Django 5.0.1 `condition=` — the same
  partial-unique species as the ledger's one-reversal rule; see
  [pg/constraints](../concepts/postgresql/constraints.md) for why the DB
  owns this race). DateTime grain means same-day sharing = sequential
  windows, no overlap ambiguity.

**Stage Work Type:** a stage is Manual or Machine; Machine ⇒ `MachineType`
mandatory (DB constraint). So the flow editor declares WHAT KIND of machine
a stage needs; the floor decides WHICH physical unit via possession.

**What this feature deliberately is NOT:** no utilization analytics, no
maintenance scheduling, no per-machine costing — Project-Anchor Law applied
to scope: model what the factory asked ("kiske paas hai"), leave seams for
the rest.

## Debugging Guide

| Symptom | Start |
|---|---|
| "Machine dikha nahi raha available" | Open window exists — find it (ended IS NULL), close/reassign |
| Two people claim one machine | Impossible in data (partial unique) — one of them holds a CLOSED window; read the timeline |
| Stage refuses machine selection | Stage's work type/MachineType vs the machine's type |

## Change Impact

Operator possession UI · stage panels showing machine context ·
worker_task_service `_resolve_machine_code` (report lines carry machine
context) · machines tests.

## AI Implementation Pitfalls

- ❌ Adding `current_holder` to Machine — derived from the open window, never stored (state-vs-evidence again).
- ❌ Closing windows by UPDATE-ing start times or deleting rows — append-only citizenship.
- ❌ Pointing a WorkflowStage at a Machine instance — types at design time, instances at floor time.
- ✅ Always verify: one-open-window negative probe stays green after any assignment-flow change.

## Interview Notes

*Interview Signal: 🟡 Mid — temporal modeling appears in mid-level data-design rounds.*

**Q. "Track custody of shared physical assets."**
- *Short:* Append-only possession windows; "current" = the open window; uniqueness of the open window enforced by a partial unique index.
- *Senior:* Custody is a temporal relation — model the interval, derive the pointer. The race (two simultaneous check-outs) is settled at the DB by a conditional unique, the one tier no code path can bypass. Separate the TYPE needed (planning) from the UNIT held (operations).
- *Project example:* `MachineAssignment` one-open-holder partial unique; stages → MachineType; DateTime grain for same-day sequential sharing.
- *Follow-ups:* "Overlapping bookings/reservations?" (windows generalize; add exclusion constraints — PG `EXCLUDE USING gist` is the escalation) · "Utilization reports?" (fold over windows — the log/fold pattern again).

## 🧠 Remember This

"Kiske paas hai" ek pointer nahi, ek khuli entry hai. Register append-only,
ek machine ki ek hi khuli entry (DB ka partial unique), stage ko KISM
chahiye, floor ko UNIT. Ledger wala hi kanoon — is baar lohe par.

## 30-Second Revision

- MachineType (kind, stages point here) · Machine (unit) · MachineAssignment (window)
- One OPEN window per machine — partial unique (`condition=` on 5.0.1)
- Current holder = derived; history = read windows; never UPDATE/DELETE
- Machine stages: work type Machine ⇒ MachineType mandatory (DB constraint)

## DSA & Complexity

Possession windows form an **interval set per machine**; the two queries
are classic interval problems: "who holds it NOW" = the open interval
(indexed lookup on `ended IS NULL`, O(log n)); "who held it at time t" =
**interval stabbing** (find the window containing t). The one-open-window
partial unique is the invariant that keeps intervals non-overlapping
WITHOUT comparing intervals — cheaper than overlap checks because the
domain rule ("a machine has one holder") collapses the problem. Interview
framing: "temporal data = intervals, not pointers; and look for the domain
invariant that makes the general interval problem trivial before reaching
for `EXCLUDE USING gist`."

## Implementation References

- Design: R10-A in [docs/PRODUCT_DESIGN_DOCUMENT.md](../../docs/PRODUCT_DESIGN_DOCUMENT.md) amendments · vocabulary: [GLOSSARY](../../GLOSSARY.md)

## Code References
- `config/machines/models.py` · possession flows in machines services/views

## Related Concepts

[append-only-tables](../concepts/database-design/append-only-tables.md) ·
[pg/constraints](../concepts/postgresql/constraints.md) · [stage-tracking](stage-tracking.md)
