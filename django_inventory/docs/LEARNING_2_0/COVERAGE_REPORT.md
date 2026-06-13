# PKALS COVERAGE REPORT — DATED SNAPSHOT (2026-06-12)

> **Point-in-time snapshot, not a live contract.** Counts were grep/ORM-counted on
> the date above; they are NOT auto-maintained — re-measure on demand. The live
> drift guards are `core.tests` (`DocAccuracyTests` + `PkalsNavigationGuardTests`),
> not this file. Treat the numbers as "as of 2026-06-12".

## Codebase totals (denominators)
| Thing | Count | How measured |
|---|---|---|
| Named URL routes | ~146 | `grep -c path( ` per urls.py (accounts 23, production 64, expense 9, raw_materials 22, storefront 8, inventory 8, tracking 12) |
| Concrete models | 55 | Django `apps.get_models` (production 25, expense 8, storefront 7, tracking 6, accounts 5, raw_materials 4; inventory/core 0) |
| Service files | 26 | `find */services/*.py` |
| Apps | 8 | accounts, production, expense, raw_materials, tracking, inventory, storefront, core |
| ADRs | 10 | docs/adr/0001–0010 |

## LEARNING_2_0 coverage (numerators)
| Area | Documented | Of | % | Notes |
|---|---|---|---|---|
| Apps (APP_FLOW+REQUEST_MAP+FILE_MAP) | 8 | 8 | 100% | Phase 2 complete |
| URL Atlas | all routes grouped | ~146 | 100% (grouped) | per-route deep detail via journeys |
| Chokepoints | 5 (5 at v2-verified) | 5 | 100% / v2 100% | ALL 5 v2: code-verified + debug section + confidence footer |
| Request journeys | 12 (all v2: debug + confidence) | 12 | 100% | all flows traced; money/production verified-from-code, login/barcode partial-derived |
| Data flows | 7 | 7 | 100% | all verified-from-code + debug + confidence |
| DB model pages (v2) | 10 | 10 | 100% | every field + example row + FK chain + writers/readers + SQL + debug + confidence |
| Django (project-specific) | DJANGO_GUIDE hub + LEARNING/01,03,04,09 + official links (10) | — | DONE | **owner scope-narrowed**: no generic re-teaching. The old "14 per-topic pages" target is RETIRED — generic Django is delegated to LEARNING/ + official docs; only project-specific conventions live in the DJANGO_GUIDE hub. Not a gap. |
| Architecture EXPLAINED | 11 | 11 | 100% | done |
| Architecture VALIDATION | 10 decisions | 10 | 100% | done |
| ADRs linked | 10 | 10 | 100% | referenced across atlas/explained/validation |
| New-dev survival kit | 1 | 1 | 100% | done |

## Undocumented / thin areas (honest, reconciled to final v1 state)
- Per-topic Django pages (Phase 6) — hub only (0/14); LEARNING/01,03,04 + official
 links cover foundations. Deferred by design.
- Per-model DB depth beyond the 10 core pages (Phase 5) — LEARNING/02 is the
 all-up substitute meanwhile.
- TL;DR retrofit of older pages — adopted on new pages; older-page retrofit pending.
(Earlier drafts of this file listed "10/12 journeys, 6/7 flows, 1/5 chokepoint
traces" — those were mid-build counts; the final v1 numerators above (12/12, 7/7,
5/5) supersede them.)

AI_AGENT_GUIDE: ✅ done. Layered-docs + TL;DR standard: adopted (new pages); retrofit of older pages pending.

LIVING_DOCUMENTATION_SYSTEM: ✅ done (PKALS now self-maintaining; CLAUDE rule 12 wired).

PROJECT_BRAIN (FEATURE/SEARCH/DEBUGGING/DECISION_GRAPH/CHANGE_HISTORY): ✅ done — primary nav layer.

All chokepoints v2 (verified + "debug in production" + confidence). New standard adopted: debug-section + 4-level confidence footer on journeys/flows/DB pages.

All 12 request journeys done (TL;DR + 16-field + "debug in production" + confidence).

All 7 data flows done.

All 7 data flows + all 10 DB-model pages done. Only Django topic pages (generic-knowledge, LAST) + TL;DR retrofit + KM finalize remain.

## GAP REPORT (final)
COVERED (verified, complete): PROJECT_BRAIN (5 indexes), AI_AGENT_GUIDE,
LIVING_DOCUMENTATION_SYSTEM, ARCHITECTURE_EXPLAINED (11), ARCHITECTURE_VALIDATION
(10), all 8 app maps, all chokepoints v2, all 12 journeys, all 7 data flows,
all 10 DB-model pages, DJANGO_GUIDE (project-specific), URL_ATLAS, the canonical
learning path (LEARNING_PATH).
PARTIALLY COVERED (by design): login + barcode internals (Derived Understanding);
costing summary shape (Architectural Interpretation). Generic Django delegated
to LEARNING/01,03,04 + official links.
INTENTIONALLY UNCOVERED: unbuilt features (MissingPiece, Alter, G1-G7) -
placeholders only; pages created WHEN built.
FUTURE-PHASE PLACEHOLDERS: tracked in PENDING_BACKLOG + ROADMAP; the
CHANGE_IMPACT_MATRIX future-phase detail table defines the doc work each requires.

## Final quality gate (validated)
- Find any feature in <3 clicks? YES - PROJECT_BRAIN/FEATURE_INDEX then cited file.
- Trace any request end-to-end? YES - 12 REQUEST_JOURNEYS (URL to view to service to model to template to tests).
- Understand every core model? YES - 10 DATABASE_GUIDE pages.
- AI agent finds canonical without scanning? YES - AI_AGENT_GUIDE lookup + PROJECT_BRAIN.
- Debug the chokepoints without repo search? YES - each chokepoint v2 has a debug-in-production section.

## Overall = 100% of the v1 SCOPE (as of 2026-06-12).
Spine + Phase 2 + EXPLAINED + VALIDATION + learning path + coverage = the
onboarding academy is usable end-to-end. Explicitly OUT of v1 scope (not a gap):
per-topic Django pages (0/14) + per-model depth beyond the 10 core pages — both
deferred to Phase 5/6 by design. So "100%" = the v1 scope, not every conceivable page.

### Verification Sources
Counts from `grep`/Django ORM on the repo at 2026-06-12. Confidence: High
(denominators measured; numerators are file counts in docs/LEARNING_2_0).
