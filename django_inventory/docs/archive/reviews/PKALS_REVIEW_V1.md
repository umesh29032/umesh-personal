> **ARCHIVED 2026-06-13** -- PKALS review-cycle artifact (process/history), not living knowledge. Kept for the record; do NOT treat as current. Living docs: docs/LEARNING_2_0/ (START_HERE).

# PKALS v1 — HOSTILE REVIEW (independent architect)

> Adversarial audit. No praise. Findings are evidence-backed (grep counts from
> the live tree, 2026-06-12). High-impact first. This file critiques PKALS; it
> is NOT part of the academy.

## TOP FINDINGS (high-impact, ranked)

### H1 — DRIFT BOMB: 138 hard-coded line-number citations stamped "Verified: High"
Journeys + chokepoints cite exact lines (`finalize`, `SWA create`,
`set_verified`…). Count: **138 `Lxxx` references.** The moment ANY of those
files changes, the citation is wrong but the footer still reads "Verified from
code — High." This is worse than no citation: it manufactures false confidence
and there is **no automation** that catches it (the doc-accuracy guard checks
only 2 files). **Highest drift risk in the whole system.**

### H2 — Settlement lock-order / "advisory 5374" duplicated across 17 files
`grep` finds the finalize lock-order or advisory lock restated in **17 docs**
(KNOWLEDGE_MAP, ARCHITECTURE_V2, chokepoint, 3 settlement journeys, data flow,
DB page, 2 FILE_MAPs, DEBUGGING_INDEX, SEARCH_INDEX, DJANGO_GUIDE, LEARNING 02/03/09,
ADR-0002). Change the lock order once → 17 edits. CHANGE_IMPACT_MATRIX lists
*some* but not all; the rest drift silently. The "one canonical per topic"
claim is **false** for the most important invariant in the system.

### H3 — 10 competing entry points; the actual repo README has ZERO PKALS links
"start here / first read / read N files" appears in **10 docs**
(PROJECT_KNOWLEDGE_MAP, PROJECT_ATLAS, AI_AGENT_GUIDE, PROJECT_BRAIN,
DOCUMENTATION_INDEX, NEW_DEVELOPER_FIRST_7_DAYS, LEARNING_PATH, WORK_LOG, …).
A newcomer cannot tell which is THE door. Worse: the repo root `README.md`
contains **0** references to LEARNING_2_0/PROJECT_BRAIN/ATLAS — the front door
of the repository doesn't point at the knowledge system at all. Discoverability
fails at step 0.

### H4 — Two knowledge maps with overlapping content
`docs/PROJECT_KNOWLEDGE_MAP.md` (§3 production flow, §4 settlement, §6 ER, §7
chokepoints) and `docs/LEARNING_2_0/PROJECT_ATLAS.md` both claim to be the
orienting map and both restate the same flows/ER/chokepoint table. Two
canonicals for "the overview." A reader who finds one never knows the other
exists or which is current.

### H5 — Maintenance depends on human discipline + a hand-maintained matrix
PKALS-LIVE is a *rule*, not a *mechanism*. CHANGE_IMPACT_MATRIX is a hand-typed
table: add a new service and forget to add its row → the safety net has a hole
and nothing complains. Only `core/tests.py` doc-accuracy guard is automated, and
it validates **2 files** (SYSTEM_DESIGN, KNOWLEDGE_MAP) for version/keyword
drift only — it cannot detect a stale journey, a wrong line number, or a missing
matrix row. Drift resistance is **mostly aspirational.**

### H6 — PROJECT_ATLAS is a 55-link hub, not a "5-minute view"
ATLAS has **55 outbound links**. Layer-1 ("5-minute understanding") is supposed
to be readable and conclusive on its own; instead it's a switchboard that fans
to everything. A junior opening it faces 55 choices, not an answer.

## DUPLICATION / DOCS THAT SHOULD NOT EXIST (as reader-facing knowledge)
- **WORK_LOG.md** — build-process scaffolding. Now that v1 is "done," it is
 token-waste for any reader and a *third* "where to start" voice. Should be
 demoted out of the reader surface.
- **DOC_AUDIT_2026_06_12.md** — a one-time process artifact, still in active docs/.
- **COVERAGE_REPORT.md vs FINAL_PKALS_REVIEW.md** — overlap (both inventory what
 exists / gaps). Two docs, one job.
- **ARCHITECTURE_EXPLAINED (11) vs ARCHITECTURE_VALIDATION (10)** — 7 topics
 appear in both ("why settlement≠payment", "why append-only", "why two truths",
 "why open-closed"…). The junior "why" and the senior "why" are 80% the same
 prose in two trees.
- **DB pages vs LEARNING/02 vs KNOWLEDGE_MAP §6** — the ER + per-model story told
 three times at three depths; the FK chains are copy-pasted.
- **Per-app REQUEST_MAP vs URL_ATLAS** — the same URL→view→service rows, sliced
 two ways. Two places to update when a route changes.

## DUAL/CONFLICTING LEARNING ORDERS
`LEARNING_PATH.md` and `NEW_DEVELOPER_FIRST_7_DAYS.md` both prescribe a starting
order, and they differ (LEARNING_PATH = 9 steps + SQL; FIRST_7_DAYS = day-by-day).
A junior following both gets two different "read X first." Pick one; the other is noise.

## CIRCULAR / DEAD-END NAVIGATION
- AI_AGENT_GUIDE → PROJECT_BRAIN/README → "AI agents: this + AI_AGENT_GUIDE" → loop.
- ATLAS → PROJECT_BRAIN → DEBUGGING_INDEX → CHOKEPOINT → ARCHITECTURE_EXPLAINED →
 ADR → (no clear "back to your task") — the reader can descend forever with no
 "you now have your answer, stop" signal.
- Several pages end with "see [canonical]" pointing UP to a doc that points back
 DOWN to them (KNOWLEDGE_MAP §7 ⇄ CHOKEPOINTS ⇄ ARCHITECTURE_EXPLAINED).

---

## PERSONA A — Junior dev (basic Django)
- **Easy:** ARCHITECTURE_EXPLAINED "why" files; the worker_reporting journey.
- **Difficult:** choosing an entry point (10 doors); the 55-link atlas; knowing
 which of two learning orders to trust.
- **Too many clicks:** repo README (no PKALS link) → has to be *told* LEARNING_2_0
 exists → ATLAS → BRAIN → INDEX → file. The "<3 clicks" claim assumes you
 already start inside PROJECT_BRAIN.
- **Confusion:** two knowledge maps; EXPLAINED vs VALIDATION feeling redundant.
- **Would skip:** WORK_LOG, COVERAGE_REPORT, DOC_AUDIT, VALIDATION (looks like a repeat).
- **Missing:** a single "I am a junior — read exactly these 5, in this order, stop."
- **Over-documented:** the "why" layer (twice). **Under-documented:** how to run
 the project locally + seed data to actually *try* a journey (no setup page in PKALS).

## PERSONA B — Senior joining after 2 years
- **Easy:** ARCHITECTURE_VALIDATION (rejected alternatives) + DECISION_GRAPH.
- **Difficult:** trusting line-cited traces that are 2 years stale (H1); telling
 canonical from echo across 17 settlement docs.
- **Confusion:** is PROJECT_KNOWLEDGE_MAP or PROJECT_ATLAS current? Both look maintained.
- **Would skip:** journeys (assumes they've rotted); goes straight to code — which
 defeats PKALS's purpose.
- **Missing:** a "what changed since the docs were written" signal (last-verified-
 against-commit stamp). Confidence footers give a level, not a date/commit.
- **Over-documented:** generic data-flow ASCII that restates the journey.

## PERSONA C — AI agent, zero memory
- **Easy:** AI_AGENT_GUIDE canonical-lookup table; PROJECT_BRAIN indexes.
- **Difficult:** the "read 5 files" budget is unmeasured — those 5 carry 55+16+6
 outbound links; a literal agent could pull 20+ files. No token ceiling, no
 "you may stop after the lookup row."
- **Too many clicks:** none if it obeys the lookup table; many if it doesn't.
- **Confusion:** line-number citations that no longer match → the agent edits the
 wrong place or distrusts all docs and re-scans (the exact cost PKALS exists to avoid).
- **Would skip:** ARCHITECTURE_VALIDATION/EXPLAINED prose (low signal-per-token for a task agent).
- **Missing:** a machine-readable index (the indexes are prose tables; an agent
 must parse markdown). No `manifest.json` / structured canonical map.
- **Token-wasting:** 95 files / ~3,000 lines — if an agent mis-judges and reads
 broadly, PKALS is *more* to read than several source files.

## DOCS THAT SHOULD EXIST BUT DO NOT
- A single **ROUTER** ("you are A/B/C → read exactly this short list → stop") to
 collapse the 10 doors.
- A **local-setup / try-it** page (run server, seed, log in, walk one journey).
- A **test → doc** reverse map (journeys cite tests; tests don't point back; no
 way to know which doc a failing test should update).
- A **machine-readable canonical manifest** for agents (vs prose tables).
- A **"last verified against commit ___"** stamp mechanism instead of bare "High".

## WHAT IS GENUINELY HARD TO BREAK (stated for fairness, not praise)
The single-writer / chokepoint conceptual model and the per-chokepoint debug
sections are specific and useful. The defects above are about STRUCTURE,
DUPLICATION, and DRIFT — not the correctness of the captured knowledge.
