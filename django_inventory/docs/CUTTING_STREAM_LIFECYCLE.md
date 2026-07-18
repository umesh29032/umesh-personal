---
id: docs-cutting-stream-lifecycle
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# CUTTING STREAM LIFECYCLE — additional lanes (sequence > 1)
(2026-07-11 · business workflow freeze · companion to
PRE_PRODUCTION_ARCHITECTURE_FINAL_REVIEW.md · SHORT by design ·
no code — these rules bind the implementation)

## The one sentence

> A sequence-1 lane is DERIVED (the Blueprint speaks); every later lane
> is a DECLARED management act with a mandatory reason — appended,
> never edited, and it never rewrites anything that already happened.

## 1 · Who may create one

**Manager or super-admin only.** Same authority class as Adda creation
and roster edits. Workers and skill-holders never create streams —
they only ever see tasks.

## 2 · When it may be created

Any time between Adda creation and Adda completion, **including after
the pre-production join** — with the frozen late-cycle semantics:
- **Before the join:** the new lane simply becomes one more
  join-blocking participant (if its group holds mandatory pieces).
- **After the join:** the Adda NEVER regresses (the join gate has no
  memory). The late lane walks its own lay → pattern → cut; its output
  APPENDS to the ops pool via the existing Σ-over-streams read.
- Never on a completed or settlement-closed Adda (recuts there = a new
  Adda — a business decision, not a lane).

## 3 · Valid reasons (mandatory, recorded — data, not code)

The creation form requires a reason; suggested picks, free text
allowed (reasons are DATA — adding a new reason is never a code
change):
- **Fabric shortage** — first lay came up short.
- **Recut** — pieces failed checking / damaged downstream.
- **Additional production** — order quantity increased.
- **Split lay** — fabric arriving in parts / planned multi-day lay.
- **New color lot** — same group, different color lot laid separately.
The reason is stamped on the stream row and into the Adda history
event (`stream_added`) — append-only, like void and reopen reasons.

## 4 · What happens to the original stream

**Nothing.** Its layering, pattern record, cutting record, frozen
cost, worker earnings and verifications stand untouched — history
never lies. The new lane is a sibling, not a revision. (If the OLD
lane's numbers were WRONG, that is what the existing correction tools
are for — reopen/void with their heavy, audited semantics. Wrong
numbers = correction; more work = new lane. The two never mix.)

## 5 · Sequence assignment

`Max(sequence) + 1` for that (adda, fabric_group), taken under the
adda_service lock — frozen in the final review. Sequence numbers are
never reused, never renumbered.

## 6 · Fabric group constraint

A new lane may only be opened for a fabric group that EXISTS in the
Adda's derived streams (i.e., in the Blueprint snapshot at creation).
You cannot invent a group on the fly — if the product genuinely gained
a new fabric group, that is a Blueprint change, and it applies to
FUTURE Addas (creation-time snapshot law).

## 7 · A360 appearance

Each additional lane = one more lane card, labelled by fabric + lane
number with its reason visible:
```
● Panel fabric · lane 2 — recut (12 pieces failed checking)
  Layering ⏳ · Pattern — · Cutting —
```
Post-join lanes appear under the pre-production section with a small
"added after join" tag; the Adda's main timeline position is
unaffected. Cancelled lanes (see §9) render greyed with their reason.

## 8 · What operators see

Workers: exactly a task — "Layering — Panel fabric (lane 2)". No
stream vocabulary, no lane management, no difference from any other
assignment. Crews are rostered per lane through the same stage start
forms; every floor law (skill gate, assignment gate, report lock,
helper completion) applies unchanged per lane.

## 9 · Safeguards against accidental duplicates

1. **Confirm-with-context:** the creation dialog lists the group's
   existing lanes and their live state ("Panel fabric already has
   lane 1 — Cutting complete, 148 pieces") before confirming.
2. **Mandatory reason** (§3) — no silent second lanes.
3. **Management-only** (§1).
4. **Cancel-if-empty escape:** a mistakenly created lane may be
   CANCELLED (soft, reason required, management-only) **only while it
   has zero started stage records**. This is the single permitted
   mutation on a stream row (`cancelled_at` + reason); once any work
   starts, the lane is history and lives forever. Cancelled lanes are
   excluded from the join predicate and greyed in A360.
   Sequence-1 DERIVED lanes can never be cancelled — the Blueprint put
   them there; if the Blueprint is wrong, fix the Blueprint (future
   Addas) — never erase a derived fact mid-flight.
5. **Audit events:** `stream_added` / `stream_cancelled` in
   AddaHistory with actor + reason, alongside the existing event
   vocabulary.

## 10 · v1 shipping note

The SCHEMA and these rules freeze now. The "Add lane" button itself
may ship with the redesign or immediately after — it is one small
management form implementing §1–§9 verbatim; nothing in v1 depends on
it existing, and nothing may ship a different behavior for it later.

**Pre-production architecture: FROZEN. Implementation may begin per
IMPLEMENTATION_READINESS_PRE_PRODUCTION.md (with the final review's
two modifications). STOP.**
