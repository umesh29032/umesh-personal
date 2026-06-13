> **ARCHIVED 2026-06-13** -- PKALS v1 self-review. Its load-bearing future-phase table was relocated to LIVING_DOCUMENTATION_SYSTEM/CHANGE_IMPACT_MATRIX.md (future-phase integration detail). Kept for history.

# FINAL PKALS REVIEW

## TL;DR (2 min)
PKALS = the project's permanent knowledge system: navigate fast (PROJECT_BRAIN),
enter safely (AI_AGENT_GUIDE), understand the why (ARCHITECTURE_EXPLAINED /
VALIDATION), trace any request (JOURNEYS), debug any of it (chokepoints + debug
sections), keep it true (LIVING_DOCUMENTATION_SYSTEM). Built verification-first,
code-cited. It does NOT replace code, tests, or ADRs — it routes you to them.

## What PKALS solves
- Onboarding: a junior follows NEW_DEVELOPER_FIRST_7_DAYS + ARCHITECTURE_EXPLAINED
 and is productive without tribal knowledge.
- Navigation / token reduction: PROJECT_BRAIN (feature/search/debugging/decision/
 change indexes) + AI_AGENT_GUIDE canonical lookup find the right file without
 scanning the repo (the explicit AI-efficiency goal).
- Architecture preservation: ARCHITECTURE_EXPLAINED (why) + VALIDATION (rejected
 alternatives) + ADRs (binding) keep the reasoning permanent.
- Debugging: every journey + chokepoint has a "debug in production" playbook;
 DEBUGGING_INDEX maps symptom to place.
- Owner learning: business + technical + DB + architecture reasoning, Hinglish+English.
- Drift prevention: PKALS-LIVE (CLAUDE rule 12) + CHANGE_IMPACT_MATRIX make doc
 updates part of "done"; the doc-accuracy CI guard catches drift.

## What PKALS does NOT solve
- NOT the source of truth — code + tests + ADRs are. PKALS routes to them.
- Does NOT auto-update — a human/agent follows PKALS-LIVE (matrices make it
 mechanical; the CI guard catches the worst drift; most updates are discipline).
- Does NOT cover unbuilt features beyond placeholders (MissingPiece, Alter,
 G1-G7) — pages created WHEN built.
- Does NOT teach generic Django (LEARNING/01,03,04 + official links do);
 DJANGO_GUIDE is project-specific only.
- Confidence varies: most pages Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed); some internals marked
 Derived Understanding / Architectural Interpretation — trust the footer.

## How it must be maintained
Follow LIVING_DOCUMENTATION_SYSTEM/: on any change, open CHANGE_IMPACT_MATRIX,
update the listed docs the same session (or state N/A). Architecture change =
new ADR first, then EXPLAINED/VALIDATION/KM follow. Run scripts/check.sh
(doc-accuracy guard included). Drift is a bug.

## How future phases MUST integrate with PKALS
| Phase | PKALS work required when built |
|---|---|
| TM-1 (Tracking Mode) | WorkflowStage DB page + flow-editor journey + REQUIREMENT_REVIEW link; CHANGE_IMPACT already anticipates the field |
| MissingPiece | production additions + a REQUEST_JOURNEY + DATA_FLOW + DB page (MissingPieceCase) + EXPLAINED "why" + DEBUGGING_INDEX rows; settlement pre-fill note |
| Alter/Rework | AlterCase DB page + journey + rework-pay decision (ADR-0010 sec.4) + chokepoint note (case-scoped, WSC untouched) |
| G1 material costing | DATABASE_GUIDE/cloth_roll + costing journey/flow + ADR-0009 + costing-era stamp |
| G3 variance valuation | new journey/flow + DB note; consumes MissingPiece counts |
| G6 SKU / G5 stock / G2 orders | new APPS sections + DB pages (SKU, FinishedGood, Order) + journeys + ADR-0008/0010 fences + AI_AGENT_GUIDE canonical rows |
| G7 planning | new section when built |
Every one: add to FEATURE_INDEX + SEARCH_INDEX + COVERAGE_REPORT; drop its
"future placeholder" status; update KNOWLEDGE_MAP sec.10.

## Mandatory rules for future contributors
1. Documentation drift = an architecture bug (CLAUDE rule 12 / PKALS-LIVE).
2. Verify from code before documenting; mark unverified; add Verification Sources + confidence.
3. One canonical source per topic (DOCUMENTATION_INDEX); others LINK, never copy.
4. Every major page opens with `## TL;DR` (under-2-min purpose).
5. Code change => run CHANGE_IMPACT_MATRIX => update listed docs same session.
6. New decision => new ADR (never edit a locked one) => then EXPLAINED/VALIDATION/KM.
7. Archived => superseded-by banner; never delete history.
8. Mobile-first (rule 11) + single-writer gates stay green.

### Verification Sources
Synthesizes the full PKALS build (installments 1-11) + CLAUDE rules + ADRs. Confidence: High.
