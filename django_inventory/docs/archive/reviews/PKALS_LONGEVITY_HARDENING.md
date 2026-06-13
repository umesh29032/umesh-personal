> **ARCHIVED 2026-06-13** -- PKALS review-cycle artifact (process/history), not living knowledge. Kept for the record; do NOT treat as current. Living docs: docs/LEARNING_2_0/ (START_HERE).

# PKALS — LONGEVITY HARDENING (Phase-2 findings applied)

> What was implemented for the five accepted Phase-2 findings (C-1, H-A, H-B,
> H-C, H-D) from [PKALS_FINAL_REVIEW.md](PKALS_FINAL_REVIEW.md). Bounded by:
> **no new systems, no docs website, no architectural redesign, no EXPLAINED/
> VALIDATION merge, no cosmetic rewrites, PKALS structure preserved.** Goal:
> long-term survivability only. Verified against commit `f067daf0`, 2026-06-13.
> Reassessment + before/after metrics: [PKALS_FINAL_SCORECARD.md](PKALS_FINAL_SCORECARD.md).

---

## C-1 — Drift hardening by EXTENDING the one existing guard (not a new system)

Added one test class, `PkalsNavigationGuardTests`, to the existing
`config/core/tests.py` (same `SimpleTestCase`, stdlib-only framework as
`DocAccuracyTests`; it runs in `scripts/check.sh` via the normal test gate). It
validates **references, counts, and navigation integrity** — the silent failure
modes — not prose. Four cheap checks:

| Test method | What it fails the build on | Why it is high-leverage |
|---|---|---|
| `test_pkals_internal_links_resolve` | any dangling relative `.md`/dir link across **all of `docs/LEARNING_2_0` + `START_HERE.md`** (skips http/anchors/`<placeholder>`) | a renamed/moved/deleted doc instantly breaks every referrer — this was the #1 unguarded surface; **it already caught a real dead link on first run** |
| `test_adr_sequence_is_contiguous` | a gap/dupe in `docs/adr/0001..N` | every "read the ADRs" instruction depends on the set being intact |
| `test_canonical_chokepoint_services_exist` | a rename of any of the 7 canonical single-writer service modules | the CHOKEPOINTS pages + AI_AGENT_GUIDE never-modify list point at code; a rename silently invalidates the most load-bearing docs |
| `test_front_door_navigation_chain_is_intact` | README no longer links `START_HERE`, or START_HERE no longer routes to the overview + AI guide | locks in the H3/H4 baseline so the entry path can't re-fragment |

**Coverage moved from 2 files (content) → 2 files (content) + 100 PKALS files
(link integrity) + ADR contiguity + 7 code references + the front-door chain.**
All filesystem-cheap (full class runs in ~15 ms, no DB). Honest limit: prose
accuracy is still human review — the guard covers references/counts/navigation,
which is exactly where cheap+effective lives.

## H-A — AI entry routing fixed + entry docs aligned

`AI_AGENT_GUIDE/README.md` step-1 pointed at `PROJECT_ATLAS.md` — the doc H4 had
just demoted to a non-overview index. Repointed step-1 to
`PROJECT_KNOWLEDGE_MAP.md` (the one overview), with ATLAS named as the secondary
section-index. START_HERE, AI_AGENT_GUIDE, and FUTURE_AGENT_WORKFLOW now agree on
"overview first". The front-door chain is held by the C-1 guard.

## H-B — brittle counts removed / single-sourced

Hard-coded counts drift the moment a phase lands and were duplicated across many
files. Established the **canonical list, not a number**: `PROJECT_KNOWLEDGE_MAP §7`
is the single source for the chokepoint services (a self-counting table, headed
"The chokepoint services", backed by the C-1 service-existence guard). De-numbered
the peripheral live docs to "the chokepoint services" + a link to §7:

- `PROJECT_KNOWLEDGE_MAP §7` — heading de-numbered; removed the contradictory
 "history_service = sixth" ordinal (the canonical itself said "five" in the
 heading and "sixth" in the body).
- `AI_AGENT_GUIDE` (footer + ADR line), `ARCHITECTURE_VALIDATION` (sources),
 `PROJECT_ATLAS` (chokepoint line + "App index (8 apps)" heading),
 `NEW_DEVELOPER_FIRST_7_DAYS` (heading), `PROJECT_BRAIN/DECISION_GRAPH`
 ("The 10 ADRs" + "0001–0010") — all de-numbered, pointing at the canonical.

**Result: 0 brittle counts in the live navigation/teaching surface.**
Deliberately NOT touched: `WORK_LOG` (dated history — immutable per the
work-is-history rule), `COVERAGE_REPORT` (a counts-by-nature meta doc; its
self-contradiction is finding M-A, out of this batch), and the review/scorecard
docs (they quote counts as findings).

## H-C — future phases wired into the binding matrices

Previously only TM-1 had a (partial) row; MissingPiece / Alter / G1–G7 lived only
as unenforced prose in FINAL_PKALS_REVIEW. Added explicit rows so the mechanical
"which docs do I update when this lands?" answer now exists:

- `CHANGE_IMPACT_MATRIX` — **+4 rows** (TM-1 lands · MissingPiece lands · Alter/
 Rework lands · G1–G7 growth ships), each listing the docs to touch and pointing
 at the FINAL_PKALS_REVIEW per-phase table.
- `OWNERSHIP_MATRIX` — **+4 rows** (the per-phase table as owner + one row each for
 MissingPiece / Alter / G-phase docs-when-built, with their trigger events).

A table extension of the maintainer's existing lookup — no new system.

## H-D — maintenance triage (core vs periphery) + fan-out cap

Added a "Maintenance triage" section to `MAINTAINING_PKALS.md` so a solo
maintainer of ~100 files can triage instead of facing all-or-nothing:

- **Load-bearing core** (must stay true every change, and is C-1-guarded):
 KNOWLEDGE_MAP · START_HERE · AI_AGENT_GUIDE · ARCHITECTURE_V2 + ADRs ·
 CHOKEPOINTS canonicals · the two matrices · DOCUMENTATION_INDEX.
- **Verify-on-touch periphery** (caches, not contracts; may lag, trust code):
 APPS/<app>/×3 · URL_ATLAS · COVERAGE_REPORT counts · per-model DATABASE_GUIDE ·
 per-flow DATA_FLOWS/REQUEST_JOURNEYS · DJANGO_GUIDE.
- **Fan-out cap:** a new app/model/stage gets ONE periphery page first; the full
 triplet/journey/flow only once load-bearing — keeps growth linear under G1–G7.

Also updated `DRIFT_PREVENTION.md` + `MAINTAINING_PKALS` "how stale docs are
detected" to record that the link sweep is now **automated** (the C-1 guard),
not a periodic manual chore (docs-sync, rule 12).

---

## Before / after metrics (commit f067daf0)

| Metric | Before | After |
|---|---|---|
| PKALS files under any CI guard | **0** (only 2 non-PKALS source docs) | **100** (link integrity) + ADR contiguity + 7 service refs + front-door chain |
| Doc-guard test methods | 5 (`DocAccuracyTests`) | 5 + **4** (`PkalsNavigationGuardTests`) = 9 |
| Link-integrity sweep | manual / periodic ("run periodically") | **automated, fails the build** |
| Brittle hard-coded counts in live nav surface | "5 chokepoints" (5 live files) · "10 ADRs/0001–0010" (3 live files) · "8 apps" heading | **0** (single self-counting canonical + links) |
| AI entry-doc first instruction | points at demoted PROJECT_ATLAS | points at PROJECT_KNOWLEDGE_MAP (overview); 3 entry docs aligned |
| Future phases in binding matrices | TM-1 only (1 partial row) | TM-1 + MissingPiece + Alter + G1–G7 — **+4 CHANGE_IMPACT rows, +4 OWNERSHIP rows** |
| Maintenance model for a solo owner | all-or-nothing (98 files, no triage) | core-vs-periphery tiers + fan-out cap (documented) |
| Real defects caught while hardening | — | 1 (dead `../PROJECT_ATLAS.md` link in PKALS_FINAL_REVIEW) |
| Core test suite | 13 green | **17 green** (no regressions) |

## Out of scope (left as flagged debt, per constraints)
- M-A reconcile/neuter COVERAGE_REPORT self-contradiction (counts-meta doc).
- M-B single-source "no ledger until settlement" across 7 files (lower probability).
- L-A renumber PROJECT_ATLAS §2/3/4 gap (cosmetic).
- EXPLAINED/VALIDATION twin merge (explicitly excluded).
- Any prose-accuracy automation, doc pipeline, or docs website (new systems).

### Verification Sources
config/core/tests.py (new `PkalsNavigationGuardTests`, run green: 4/4 + full core
17/17), the edited docs (read+edit), grep sweeps confirming 0 brittle counts in
the live nav surface. Commit f067daf0, 2026-06-13. Confidence: High (every change
re-verified by test run or grep).
