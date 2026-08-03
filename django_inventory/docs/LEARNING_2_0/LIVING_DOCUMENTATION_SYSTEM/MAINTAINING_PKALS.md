---
id: l2-living-documentation-system-maintaining-pkals
type: topic-canonical
status: active
owner: handwritten
scope: documentation system (PKALS-LIVE)
anchors: —
verified: 2026-07-13
---

# MAINTAINING PKALS — surviving years of development

## TL;DR
PKALS stays alive because updating it is part of "done" (PKALS-LIVE rule = CLAUDE
rule 12), the update path is mechanical (CHANGE_IMPACT_MATRIX), and drift is
machine-detected (doc-accuracy guard). No tribal knowledge required.

## How a future DEVELOPER maintains it
1. Make the change via a service + tests. 2. Open CHANGE_IMPACT_MATRIX, update
each listed doc. 3. `scripts/check.sh` green. 4. Commit code + docs together.
New standing rule? → add to CLAUDE.md + memory. New design decision? → new ADR
(never edit a locked one) → then update ARCHITECTURE_VALIDATION + KNOWLEDGE_MAP §9.

## How a future AI AGENT maintains it
Run FUTURE_AGENT_WORKFLOW every session. Docs are the memory: read them instead
of scanning; if you had to scan, the doc was stale → fix it. Update per
CHANGE_IMPACT_MATRIX. This is enforced by CLAUDE rule 12 (loads every session).

## How DOCUMENTATION updates happen
Same session as the code, same commit. The CHANGE_IMPACT_MATRIX maps file→docs;
the OWNERSHIP_MATRIX maps doc→trigger. Together they make "which docs?" answerable
without thinking.

## How ARCHITECTURE / ADR updates happen
Architecture change = new ADR (binding) FIRST → then the explanation/validation/
map docs follow it. ADRs are append-only decisions; supersede, never edit.

## How STALE docs are detected
`core.tests` CI guards (build fails): `DocAccuracyTests` (version/app/relocation
claims) + `PkalsNavigationGuardTests` (PKALS link integrity, ADR contiguity,
chokepoint-service existence, front-door chain — C-1 hardening). Plus the
CHANGE_IMPACT checklist · COVERAGE_REPORT gaps · archive banners. See
DRIFT_PREVENTION. (Prose accuracy still needs human review — the guards cover
references/counts/navigation, not wording.)

## Maintenance triage — what MUST stay true vs what may lag (H-D)
PKALS is ~98 files; a solo maintainer cannot keep all of them perfectly current,
and "update all or none" leads to "none". So maintain in two tiers:

**LOAD-BEARING CORE — must stay true every change (never allowed to drift):**
PROJECT_KNOWLEDGE_MAP · START_HERE · AI_AGENT_GUIDE · ARCHITECTURE_V2 + the ADRs ·
CHOKEPOINTS/ canonicals · CHANGE_IMPACT_MATRIX + OWNERSHIP_MATRIX · DOCUMENTATION_INDEX.
These are what a new dev / AI agent / owner rely on first; a wrong line here
mis-routes everything downstream. The `core.tests.PkalsNavigationGuardTests` guard
backs the references in this tier (links resolve, ADRs contiguous, chokepoint
services exist, front-door chain intact) — a break fails CI.

**VERIFY-ON-TOUCH PERIPHERY — re-derive from code when you touch the area; may lag
between touches (mark it, don't pretend it's live):**
APPS/<app>/{APP_FLOW,REQUEST_MAP,FILE_MAP} · URL_ATLAS · COVERAGE_REPORT counts ·
per-model DATABASE_GUIDE · per-flow DATA_FLOWS / REQUEST_JOURNEYS · DJANGO_GUIDE.
These restate code that changes often; treat them as caches, not contracts —
trust code over a stale periphery page, and refresh the page while you are in
that code (rule 12), not on a schedule.

**Fan-out cap (keeps growth linear, not super-linear):** a NEW app/model/stage gets
ONE periphery page first (a FILE_MAP or a DATABASE_GUIDE entry) — add the full
triplet / journey / data-flow only once it is load-bearing and stable. Do not
auto-generate three files per new entity; that is how the periphery becomes
unmaintainable under G1–G7. Counts live as self-counting tables/lists, never as a
hard-coded number (H-B); the canonical list is the source.

## The promise
A developer, the owner, and a future Claude can understand, debug, extend, and
PRESERVE this system using LEARNING_2_0 — without the original architect in the room.
