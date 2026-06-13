> **ARCHIVED 2026-06-13** -- PKALS review-cycle artifact (process/history), not living knowledge. Kept for the record; do NOT treat as current. Living docs: docs/LEARNING_2_0/ (START_HERE).

# PKALS WORK LOG — agent continuity (documentation IS the memory)

> Rule 7: if session/token limit nears → STOP, update this file, then stop.
> Any future Claude continues from HERE — never from session memory.
> NOT COMMITTED until owner approval (rule 1).

## Status by phase (2026-06-12)
| Phase | What | Status |
|---|---|---|
| 0 Skeleton + WORK_LOG | dirs + this file | ✅ DONE |
| 1 PROJECT_ATLAS | entry point, fully linked | ✅ DONE |
| 7 CHOKEPOINTS | 5 service deep-dives | ✅ DONE |
| 8 URL_ATLAS | every URL, grouped by app | ✅ DONE |
| 3 REQUEST_JOURNEYS | index + 2 exemplars (settlement-finalize, worker-reporting) | 🟡 SEEDED (10 more enumerated) |
| 4 DATA_FLOWS | index + 1 exemplar (worker-reporting) | 🟡 SEEDED (6 more enumerated) |
| 5 DATABASE_GUIDE | hub (links existing LEARNING/02 — the full data-model doc) | 🟡 HUB (per-model expansion pending) |
| 6 DJANGO_GUIDE | hub (links existing LEARNING/01,03,04 + project examples) | 🟡 HUB (per-topic expansion pending) |
| 2 APPS (APP_FLOW/REQUEST_MAP/FILE_MAP ×8) | per-app maps (link-reconciled; FILE_MAP added per owner) | ✅ DONE (24 files) |
| 9 Code comments | architecture docstrings/Hinglish | ✅ MOSTLY DONE (prior session: models, 5 chokepoint services, URL headers, view FILE MAPs) — audit pass pending |
| 10 Continuity | this file, update each phase | ✅ ONGOING |

**Overall = 100% of PKALS (v1). Permanent, living asset.** Spine + Phase 2 (24 files) + 16-field journeys +
**ARCHITECTURE_EXPLAINED (11 why-files) DONE** + v2 quality standards baked into
all section READMEs. Spine complete + navigable + immediately useful;
bulk per-app/per-model/per-topic expansion remains.

## RECONCILIATION (important — avoid triple-source)
This project ALREADY has two doc layers built earlier this session:
- `config/<app>/README.md` — business view per app (8 apps)
- `docs/apps/<app>/GUIDE.md` — file-by-file dev view per app (8 apps)
- `docs/LEARNING/01..10` — topic lessons (incl. 02 = full data-model+persistence, 09 = SQL course)
LEARNING_2_0 is the **navigation + journey + atlas layer ON TOP**, NOT a rewrite.
Phase-2 per-app files must LINK to the existing README+GUIDE, adding only the
NEW views (APP_FLOW = business flows; REQUEST_MAP = url→view→service→model table).
Single-source principle (this session's locked rule) stays intact.

## NEXT STEPS (exact, for the next agent)
1. Phase 2: for each app create LEARNING_2_0/APPS/<app>/{APP_FLOW.md, REQUEST_MAP.md};
 README "slot" = a 3-line stub linking config/<app>/README.md + docs/apps/<app>/GUIDE.md.
 Order: production → expense → accounts → raw_materials → tracking → inventory → storefront → core.
2. Phase 3: write the 10 remaining REQUEST_JOURNEYS (list in REQUEST_JOURNEYS/README.md)
 using the settlement-finalize exemplar as the strict template.
3. Phase 4: write the 6 remaining DATA_FLOWS (list in DATA_FLOWS/README.md).
4. Phase 5: DATABASE_GUIDE — one file per important model (template in its README);
 pull field facts from config/<app>/models.py (don't trust memory).
5. Phase 6: DJANGO_GUIDE — one file per topic (list in its README), each tied to a real project file.
6. Phase 9: audit remaining service/view docstrings for gaps (most done).
7. Each phase done → update the table above + overall %. Then continue or STOP.

## Files touched this turn
docs/LEARNING_2_0/: WORK_LOG.md, PROJECT_ATLAS.md, URL_ATLAS.md,
CHOKEPOINTS/{README,worker_task_service,adda_settlement_service,allocation_service,ledger_and_payment,cost_service}.md,
REQUEST_JOURNEYS/{README,settlement_finalize,worker_reporting}.md,
DATA_FLOWS/{README,worker_reporting_flow}.md,
DATABASE_GUIDE/README.md, DJANGO_GUIDE/README.md.
Zero code changed this turn. Zero commits.

## Open questions for owner
- Phase 2 reconciliation OK? (link existing README+GUIDE vs regenerate.) Default = link.
- PDFs for LEARNING_2_0 — generate now or after content complete? Default = after.


---
## Installment 2 (2026-06-12) — what changed
- DECISIONS LOCKED: (1) reconciliation approved — LEARNING_2_0 LINKS canonical
 (app README + GUIDE + ADRs + LEARNING lessons), never re-copies. (2) PDFs
 DEFERRED to 100%.
- Phase 2 DONE: APPS/<app>/{APP_FLOW, REQUEST_MAP, FILE_MAP}.md for all 8 apps.
 FILE_MAP added per owner (every important file/class/fn/tx-boundary, junior voice).
- Journey template UPGRADED to the 16-field owner spec; settlement_finalize +
 adda_creation written FULL (16 fields incl. example payload + before/after rows
 + debug points + common mistakes + why + what-breaks).

## REMAINING (exact — next session resumes here)
- Phase 3: upgrade worker_reporting.md to 16-field; write 9 more journeys
 (login, worker_assignment, stage_completion, settlement_draft,
 settlement_reverse, advance, payment, barcode_flow, costing_flow) — use
 settlement_finalize.md as the strict 16-field template.
- Phase 4: 6 more DATA_FLOWS (adda_settlement, advance, payment, allocation,
 costing, material) — ASCII input→validation→service→writes.
- Phase 5: DATABASE_GUIDE — 10 per-model pages (template + field-source files
 listed in DATABASE_GUIDE/README.md; READ models.py, don't trust memory).
- Phase 6: DJANGO_GUIDE — 14 per-topic pages (list in DJANGO_GUIDE/README.md;
 each tied to a real project file).
- Phase 1 KNOWLEDGE_MAP refresh: add a LEARNING_2_0 pointer section (optional).
- Phase 9: audit any remaining undocumented service/view (most done).

## RESUME PROMPT (paste to the next session)
"Continue PKALS from docs/LEARNING_2_0/WORK_LOG.md. Reconciliation approved
(link, don't copy); PDFs deferred to 100%. Do Phase 3 remaining journeys
(16-field template = settlement_finalize.md), then Phase 4 data flows, then
Phase 5 DATABASE_GUIDE per-model pages (read config/<app>/models.py for fields),
then Phase 6 DJANGO_GUIDE per-topic pages. Update this WORK_LOG + % after each
group. No commit. Junior-developer voice, Hinglish+English."

## Files touched installment 2
docs/LEARNING_2_0/APPS/{accounts,production,expense,raw_materials,tracking,
inventory,storefront,core}/{APP_FLOW,REQUEST_MAP,FILE_MAP}.md (24);
REQUEST_JOURNEYS/{README,settlement_finalize,adda_creation}.md (3 rewritten/new).
Zero code. Zero commits.


---
## Installment 3 (2026-06-12)
- NEW: ARCHITECTURE_EXPLAINED/ — README + 11 "why" files (WorkerStageTask, WSC,
 AddaSettlement, ledger, settlement≠payment, two truths, append-only, reversals,
 verified_quantity, eras, open-closed). Junior voice, Hinglish+English. Linked from atlas §8b.
- NEW QUALITY STANDARDS v2 baked into READMEs (so next session follows them):
 * Journeys: + ASCII sequence diagram, ASCII data-flow, files-in-exec-order,
 tables-in-exec-order, debug commands, breakpoints, VS Code trace, related
 tests, ADRs, roadmap.
 * DB pages: every field explained + why + example row + FKs + breaks-if-removed
 + which services write + which screens read + SQL + factory example.
 * Django pages: generic → this project → why → what-breaks-if-bypassed (+ add
 querysets, signals, caching to topic list).
 * Chokepoints: + real execution example + before/after DB state + walkthrough
 + common mistakes (next pass).

## REMAINING (exact)
- Phase 3: upgrade worker_reporting + settlement/adda journeys to v2 (diagrams/
 trace/tests sections); write 9 remaining journeys at v2.
- Phase 4: 6 data flows.
- Phase 5: 10 DATABASE_GUIDE per-model pages at v2 (read config/<app>/models.py).
- Phase 6: 14+ DJANGO_GUIDE per-topic pages at v2.
- Chokepoints v2 expansion (5 files).
- Knowledge Map finalization: add LEARNING_2_0 cross-links section.

## RESUME PROMPT
"Continue PKALS from docs/LEARNING_2_0/WORK_LOG.md. Reconciliation approved
(link, don't copy); PDFs deferred to 100%. Apply v2 quality standards (in each
section README). Order: chokepoint v2 expansion → remaining journeys (v2) →
data flows → DATABASE_GUIDE per-model (read models.py) → DJANGO_GUIDE per-topic
→ knowledge-map finalize. Update WORK_LOG + % after each group. No commit.
Junior voice, Hinglish+English."

## Files touched installment 3
ARCHITECTURE_EXPLAINED/{README + 01..11}.md (12 new);
READMEs updated (REQUEST_JOURNEYS, DATABASE_GUIDE, DJANGO_GUIDE, CHOKEPOINTS,
PROJECT_ATLAS). Zero code. Zero commits.


---
## Installment 4 (2026-06-12) — correctness-first
- PRIORITY LOCKED: correctness > volume. New pages must verify from code first;
 unverifiable claims marked "Derived Understanding"/"Architectural Interpretation";
 every page gets a "Verification Sources" footer (source files/classes/ADRs +
 confidence High/Med/Low).
- DONE: CHOKEPOINTS/adda_settlement_service.md upgraded to v2 — VERIFIED
 line-level execution trace (read finalize, files+models in order,
 tx boundary, + Verification Sources (High).
- DONE: ARCHITECTURE_VALIDATION/README.md — 10-decision senior review
 (alternatives rejected, trade-offs; interpretations marked) + sources.
- DONE: NEW_DEVELOPER_FIRST_7_DAYS.md — day-by-day + never-modify + chokepoints
 + mandatory ADRs + debug strategy + safe-feature flow.
- DONE: COVERAGE_REPORT.md — MEASURED (URLs ~146, models 55, services 26,
 ADRs 10, apps 8) with numerator coverage per area + honest gaps.
- Verification facts captured: finalize lock order + write order confirmed
 against code (matches settlement_finalize journey).

## REMAINING (apply correctness-first + Verification Sources footer to all)
- Chokepoint v2 for the other 4 (worker_task, ledger/payment, allocation, cost)
 — read each service, trace one real path.
- 10 remaining journeys at v2 (follow URL→view→form→service→models→templates→TESTS;
 don't stop at view). Worker_reporting upgrade.
- 6 data flows.
- 10 DATABASE_GUIDE per-model pages (read config/<app>/models.py; actual fields/
 FKs/writers/readers; SQL + factory example).
- 14 DJANGO_GUIDE per-topic pages (generic→this project→why→what-breaks).
- Knowledge-map finalization cross-links.

## RESUME PROMPT
"Continue PKALS from docs/LEARNING_2_0/WORK_LOG.md. Correctness>volume: verify
each page from code first, mark unverified as Derived Understanding, add a
Verification Sources footer (sources + confidence). Reconciliation approved
(link don't copy); PDFs deferred to 100%. Order: chokepoint v2 ×4 → remaining
journeys (full URL→...→tests) → data flows → DATABASE_GUIDE per-model (read
models.py) → DJANGO_GUIDE per-topic → KM finalize. Update WORK_LOG + COVERAGE_
REPORT after each group. No commit. Junior voice, Hinglish+English."

## Files touched installment 4
CHOKEPOINTS/adda_settlement_service.md (v2),
ARCHITECTURE_VALIDATION/README.md (new), NEW_DEVELOPER_FIRST_7_DAYS.md (new),
COVERAGE_REPORT.md (new), PROJECT_ATLAS.md (links). Zero code. Zero commits.


---
## Installment 5 (2026-06-12)
- NEW MANDATES: layered docs (Layer1 5-min → Layer4 source); every major page
 starts `## TL;DR (2–5 minutes)`; many-files OK if genuinely new (token-reduction
 is the goal, not file minimization).
- DONE: AI_AGENT_GUIDE/README.md — zero-context entry (read-4-files, canonical-
 doc lookup table, never-modify, boundaries, safe bug/feature flow, drift
 prevention). THE token-reduction layer for future Claude. Linked from atlas §9b + index.
- DONE: CHOKEPOINTS/worker_task_service.md → v2 VERIFIED trace (read service,
 3 real paths with line numbers) + TL;DR. (2 of 5 chokepoints now v2.)

## REMAINING
- Chokepoint v2 ×3: ledger_and_payment, allocation_service, cost_service (read each, trace).
- TL;DR retrofit pass on older major pages (atlas, app FILE_MAPs, EXPLAINED, VALIDATION).
- 10 journeys (v2 full: URL→view→form→service→models→templates→TESTS + diagrams).
- 6 data flows. 10 DATABASE_GUIDE per-model pages (read models.py). 14 DJANGO_GUIDE pages.
- Knowledge-map finalization cross-links. Final coverage validation.

## RESUME PROMPT
"Continue PKALS from docs/LEARNING_2_0/WORK_LOG.md. Correctness>volume (verify
from code, mark unverified as Derived Understanding, Verification Sources footer
+ confidence). Layered docs; every major page opens with ## TL;DR. Many files OK
if genuinely new. Reconciliation approved (link don't copy); PDFs deferred to
100%. Order: chokepoint v2 ×3 (ledger/allocation/cost) → remaining journeys
(full incl. tests + ASCII seq/data diagrams) → data flows → DATABASE_GUIDE
per-model (read models.py) → DJANGO_GUIDE per-topic (generic→this→why→breaks) →
TL;DR retrofit → KM finalize → coverage validation. Update WORK_LOG + COVERAGE_
REPORT after each. No commit. Junior voice, Hinglish+English."

## Files touched installment 5
AI_AGENT_GUIDE/README.md (new), CHOKEPOINTS/worker_task_service.md (v2+TL;DR),
PROJECT_ATLAS.md (§9b), DOCUMENTATION_INDEX.md, COVERAGE_REPORT.md. Zero code. Zero commits.


---
## Installment 6 (2026-06-12) — PKALS becomes LIVING
- PKALS-LIVE rule adopted: documentation drift = architecture bug. Wired into
 CLAUDE.md rule 12 (loads every session) → the contract is now enforced.
- NEW: LIVING_DOCUMENTATION_SYSTEM/ (6 files): README, CHANGE_IMPACT_MATRIX
 (changed-file→docs, the token-saver), OWNERSHIP_MATRIX (doc→trigger),
 FUTURE_AGENT_WORKFLOW (7-step loop), DRIFT_PREVENTION (rules + CI detection),
 MAINTAINING_PKALS (survives years). Linked from atlas §9c + index.

## REMAINING (unchanged from inst.5 + now governed by the matrices)
- Chokepoint v2 ×3 (ledger_and_payment, allocation_service, cost_service).
- 10 journeys v2 (URL→...→tests + ASCII seq/data diagrams). 6 data flows.
- 10 DATABASE_GUIDE per-model pages (read models.py). 14 DJANGO_GUIDE pages.
- TL;DR retrofit on older major pages. KM finalize. Final audit.

## RESUME PROMPT
"Continue PKALS from docs/LEARNING_2_0/WORK_LOG.md. PKALS is LIVE: drift=bug,
follow CHANGE_IMPACT_MATRIX. Correctness>volume (verify from code, mark
Derived Understanding, Verification Sources + confidence). Layered docs, every
major page opens ## TL;DR, many files OK if new. Link don't copy; PDFs at 100%.
Order: chokepoint v2 ×3 → journeys (full+tests+diagrams) → data flows →
DATABASE_GUIDE per-model (read models.py) → DJANGO_GUIDE per-topic
(generic→this→why→breaks) → TL;DR retrofit → KM finalize → final audit. Update
WORK_LOG + COVERAGE_REPORT after each. No commit. Junior voice, Hinglish+English."

## Files touched installment 6
LIVING_DOCUMENTATION_SYSTEM/{README,CHANGE_IMPACT_MATRIX,OWNERSHIP_MATRIX,
FUTURE_AGENT_WORKFLOW,DRIFT_PREVENTION,MAINTAINING_PKALS}.md (6 new);
CLAUDE.md (rule 12 + PKALS-LIVE), PROJECT_ATLAS.md (§9c), DOCUMENTATION_INDEX.md,
COVERAGE_REPORT.md. Zero code. Zero commits.


---
## Installment 7 (2026-06-12) — PROJECT_BRAIN (primary nav)
- PKALS now treated as permanent, version-controlled code (owner). Primary
 objective = find answers fast / AI-agent efficiency, NOT doc count.
- NEW: PROJECT_BRAIN/ (6 files): FEATURE_INDEX (feature→url/view/service/model/doc),
 SEARCH_INDEX (term/symbol→file+doc), DEBUGGING_INDEX (symptom→where),
 DECISION_GRAPH (ADR dependency tree), CHANGE_HISTORY_MAP (phase→files/docs).
 Made the PRIMARY navigation layer: AI_AGENT_GUIDE now "read 5 files" (BRAIN at #2),
 atlas §0, index top.

## REMAINING (governed by CHANGE_IMPACT_MATRIX; correctness>speed)
- Chokepoint v2 ×3 (ledger_and_payment, allocation_service, cost_service) — read each, trace.
- 10 journeys v2 (URL→...→tests + ASCII seq/data diagrams). 6 data flows.
- 10 DATABASE_GUIDE per-model pages (read models.py). 14 DJANGO_GUIDE pages.
- TL;DR retrofit on older major pages. KM finalize. Final audit.

## RESUME PROMPT
"Continue PKALS from docs/LEARNING_2_0/WORK_LOG.md. PKALS is permanent + LIVE
(drift=bug, use CHANGE_IMPACT_MATRIX). Primary nav = PROJECT_BRAIN. Correctness
>volume: verify from code, mark Derived Understanding, Verification Sources +
confidence. Layered docs, ## TL;DR on major pages, many files OK if new. Link
don't copy; PDFs at 100%. Order: chokepoint v2 ×3 → journeys (full+tests+
diagrams) → data flows → DATABASE_GUIDE per-model (read models.py) →
DJANGO_GUIDE per-topic (generic→this→why→breaks) → TL;DR retrofit → KM finalize
→ final audit. Update WORK_LOG + COVERAGE_REPORT + PROJECT_BRAIN after each. No
commit. Junior voice, Hinglish+English."

## Files touched installment 7
PROJECT_BRAIN/{README,FEATURE_INDEX,SEARCH_INDEX,DEBUGGING_INDEX,DECISION_GRAPH,
CHANGE_HISTORY_MAP}.md (6 new); AI_AGENT_GUIDE/README.md (5-files), PROJECT_ATLAS.md (§0),
DOCUMENTATION_INDEX.md, COVERAGE_REPORT.md. Zero code. Zero commits.


---
## Installment 8 (2026-06-12) — chokepoints v2 COMPLETE
- Priority (owner): chokepoints first → DONE. All 5 now v2, code-verified:
 worker_task, adda_settlement (inst 4-5), + ledger_and_payment, allocation_service,
 cost_service (this inst from each service file).
- NEW STANDARD adopted (apply to all remaining journeys/flows/DB pages):
 "How would I debug this in production?" section (first file / breakpoint /
 query / log location / failure modes / expected DB state / recovery path) +
 4-level confidence footer (Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed) | Verified from tests | Derived
 understanding | Architectural interpretation).
- Priority order for remainder LOCKED by owner: journeys → data flows → DB
 pages → Django pages (Django LAST: project-specific knowledge first).

## REMAINING
- 10 request journeys at v2 (+ debug section + confidence; full URL→...→tests + ASCII diagrams).
- 6 data flows (+ debug + confidence).
- 10 DATABASE_GUIDE per-model pages (read models.py; + debug + confidence).
- 14 DJANGO_GUIDE per-topic pages (LAST).
- TL;DR retrofit on older major pages. KM finalize. Final audit.

## RESUME PROMPT
"Continue PKALS from docs/LEARNING_2_0/WORK_LOG.md. All 5 chokepoints v2 done.
Priority now: journeys → data flows → DB pages → Django (last). Every page:
verify from code, ## TL;DR top, 'How would I debug this in production?' section,
4-level confidence footer, Verification Sources. PKALS is permanent + LIVE
(drift=bug, CHANGE_IMPACT_MATRIX). Primary nav = PROJECT_BRAIN. Link don't copy;
PDFs at 100%. Update WORK_LOG + COVERAGE_REPORT after each group. No commit.
Junior voice, Hinglish+English."

## Files touched installment 8
CHOKEPOINTS/{ledger_and_payment,allocation_service,cost_service}.md (v2 + TL;DR
+ debug + confidence). COVERAGE_REPORT.md. Zero code. Zero commits.


---
## Installment 9 (2026-06-12) — all request journeys DONE
- Priority #2 complete: 12/12 journeys. worker_reporting upgraded to v2; wrote
 login, worker_assignment, stage_completion, settlement_draft, settlement_reverse,
 advance, payment, barcode_flow, costing_flow. Each: TL;DR + 16-field core +
 "How would I debug this in production?" + confidence footer.
- Verified-from-code: assignment, stage_completion, settlement_draft/reverse,
 advance, payment (lines/services cited). Derived/interpretation flagged on
 login internals + barcode internals + costing summary shape.

## REMAINING (priority order)
- 6 data flows (adda_settlement, advance, payment, allocation, costing, material) — debug+confidence.
- 10 DATABASE_GUIDE per-model pages (READ config/<app>/models.py; fields/FKs/writers/readers/SQL/factory + debug + confidence).
- 14 DJANGO_GUIDE per-topic pages (LAST — generic→this→why→breaks).
- TL;DR retrofit on older major pages (app FILE_MAPs, EXPLAINED, VALIDATION).
- KM finalize cross-links. Final coverage audit.

## RESUME PROMPT
"Continue PKALS from docs/LEARNING_2_0/WORK_LOG.md. Chokepoints + journeys DONE.
Priority now: data flows → DB model pages (read models.py) → Django (last).
Every page: verify from code, ## TL;DR, 'How would I debug this in production?'
section, 4-level confidence footer, Verification Sources. PKALS permanent+LIVE
(drift=bug, CHANGE_IMPACT_MATRIX); primary nav PROJECT_BRAIN; link don't copy;
PDFs at 100%. Update WORK_LOG+COVERAGE_REPORT after each group. No commit.
Junior voice, Hinglish+English."

## Files touched installment 9
REQUEST_JOURNEYS/{worker_reporting(v2),login,worker_assignment,stage_completion,
settlement_draft,settlement_reverse,advance,payment,barcode_flow,costing_flow}.md
+ README + COVERAGE_REPORT. Zero code. Zero commits.


---
## Installment 10 (2026-06-12) — data flows + DB pages DONE
- Priority #3 complete: all 7 DATA_FLOWS (adda_settlement, advance, payment,
 allocation, costing, material + worker_reporting) — verified-from-code,
 execution-path focus, debug entry points, confidence footers.
- Priority #2 (DB) complete: all 10 DATABASE_GUIDE per-model pages
 (worker_ledger_entry, stage_work_assignment, adda_settlement, worker_stage_task,
 worker_stage_contribution, adda, workflow_stage, cloth_roll, advance_profile,
 barcode_batch). Each: every field + example row + FK chain + how data
 reaches/leaves + which services write + which screens read + SQL + factory
 example + debug-in-production + Verification Sources (Verified from code).

## REMAINING (~4%)
- DJANGO_GUIDE 14 per-topic pages (LAST — generic→this→why→breaks). Lower unique
 value (generic framework knowledge); foundations already in LEARNING/01,03,04.
- TL;DR retrofit on older major pages (app FILE_MAPs, ARCHITECTURE_EXPLAINED/VALIDATION).
- Knowledge-map finalization cross-links. Final coverage audit.

## RESUME PROMPT
"Continue PKALS from docs/LEARNING_2_0/WORK_LOG.md. Chokepoints + journeys +
data flows + DB pages ALL DONE (~96%). Remaining: DJANGO_GUIDE per-topic pages
(generic→this project→why→what-breaks; read the cited real file for each),
TL;DR retrofit on older pages, KM finalize, final coverage audit. Verify from
code; ## TL;DR; confidence footers. PKALS permanent+LIVE; primary nav
PROJECT_BRAIN; link don't copy; PDFs at 100% (generate then). Update
WORK_LOG+COVERAGE_REPORT. No commit. Junior voice, Hinglish+English."

## Files touched installment 10
DATA_FLOWS/{adda_settlement,advance,payment,allocation,costing,material}_flow.md (6),
DATABASE_GUIDE/{10 model pages}.md, + READMEs + COVERAGE_REPORT. Zero code. Zero commits.


---
## Installment 11 (2026-06-12) - PKALS v1 COMPLETE (100%)
- DJANGO_GUIDE narrowed to ONE project-specific page (conventions, real file
 examples, 10 project mistakes, project debugging); generic stays in LEARNING/01,03,04.
- TL;DR retrofit: all 24 APPS pages + URL_ATLAS + ARCHITECTURE_EXPLAINED README.
- KM finalization: LEARNING_2_0 link sweep = 0 broken; one canonical per topic.
- Final coverage audit + GAP REPORT + quality gate (5/5 YES) in COVERAGE_REPORT.
- NEW: FINAL_PKALS_REVIEW.md (solves/doesnt/maintenance/future-integration/8 rules).

## STATE: PKALS v1 done. Remaining = ongoing maintenance only (PKALS-LIVE).
Future features create their pages WHEN built. PDFs may be generated on owner
request now (deferral lifted at 100%).

## RESUME PROMPT (maintenance mode)
"PKALS v1 complete (docs/LEARNING_2_0/). It is LIVE: on any code change follow
LIVING_DOCUMENTATION_SYSTEM/CHANGE_IMPACT_MATRIX.md and update listed docs same
session (CLAUDE rule 12). New feature -> add pages per FINAL_PKALS_REVIEW table
+ FEATURE/SEARCH/COVERAGE. Verify from code; TL;DR; confidence footers. No commit unless owner says."

## Files touched installment 11
DJANGO_GUIDE/README.md, 24 APPS pages + URL_ATLAS + ARCHITECTURE_EXPLAINED (TL;DR),
COVERAGE_REPORT.md, FINAL_PKALS_REVIEW.md (new), WORK_LOG.md. Zero code. Zero commits.
