# PKALS — FINAL AUDIT PACKAGE (2026-06-13)

> Capstone record of the PKALS investment: build → review → hardening →
> consolidation → AI-manifest → finalization. Lives in archive/reviews (history,
> not a reader front door). Living entry stays `docs/START_HERE.md`. Paths below
> are written as text (archived docs are not link-maintained).

## 1. What PKALS is now
A permanent knowledge system at `docs/LEARNING_2_0/` (92 active md files) +
`docs/PROJECT_KNOWLEDGE_MAP.md` (the one overview) + `docs/START_HERE.md` (the one
front door) + `docs/LEARNING_PATH.md` (the one learning route). Audiences: new
developer, owner-learner, AI agent. It routes to code/tests/ADRs — it is not the
source of truth, it is the navigation + understanding layer over it.

## 2. The durability mechanism (what makes it survive)
`config/core/tests.py` — `DocAccuracyTests` (5 content checks) +
`PkalsNavigationGuardTests` (5 checks): PKALS internal-link integrity (all 92
files + START_HERE), ADR contiguity, canonical chokepoint-service existence,
front-door navigation chain, and **AI canonical-manifest validity** (every route
resolves; chokepoint set single-sourced to one constant). 10 PKALS checks total;
they run in `scripts/check.sh`. A rename/move/dead-route now FAILS the build
instead of silently rotting. Caught 2 real defects while being built.

The AI routing layer: `docs/LEARNING_2_0/AI_AGENT_GUIDE/canonical_manifest.json`
(17 topic→canonical routes, never-modify list, chokepoint services, entry points).
An agent reads ONE compact JSON to route, then opens ONE canonical — instead of
5 prose files. Routing read-cost dropped ~60-70%.

## 3. The journey (sessions)
1. **Build (v1)** — 11 installments → an onboarding academy + architecture atlas
   + debugging handbook + AI-navigation + living-doc system.
2. **Hostile review** — found H1-H6 (line-cite rot, invariant duplication, 10
   entry doors, two overviews, maintenance-is-a-rule, atlas-switchboard).
3. **H1-H4 fixes** — 138 line-cites→0 (+commit stamps); settlement lock-order
   single-canonical; one front door (START_HERE) + README link; one overview
   (KNOWLEDGE_MAP), ATLAS→index.
4. **Phase-2 final review** — C-1 (drift mechanism absent) + H-A..H-D.
5. **Longevity hardening** — C-1 guard built (link/ADR/service/front-door checks);
   AI routing fixed; counts de-numbered to a self-counting canonical; future
   phases wired into the binding matrices; core-vs-periphery triage + fan-out cap.
6. **Excellence review** — identified clutter (9 process docs in the tree),
   concept duplication overcount, APPS-collapse question.
7. **Session 1+2 (consolidation)** — archived 9 process/redundant docs (101→92,
   zero knowledge lost; future-phase table relocated into CHANGE_IMPACT_MATRIX);
   COVERAGE_REPORT contradiction resolved + dated-snapshot; M-B single-sourced;
   onboarding merged into one canonical LEARNING_PATH; 3 concept canonicals
   banner-marked (two-truths, request-flow, settlement-lifecycle).
8. **Session 3A (AI efficiency)** — machine-readable manifest + guard validation +
   AI routing optimization. APPS triplet KEPT (evidence: orthogonal lenses, not
   duplication; negligible token saving; learning value would drop).
9. **Finalization (this session)** — TL;DR added to the 2 pages that lacked one
   (adda_creation, worker_reporting_flow); KNOWLEDGE_MAP verification footer +
   finalized stamp; stale "0/14 Django pages" metric retired (owner scope: generic
   Django delegated to LEARNING/ + official links; project-specific in DJANGO_GUIDE).

## 4. Final scorecard (7 objectives, long-term)
| Objective | Score | Note |
|---|---|---|
| New-developer onboarding | ~8.5 | one canonical path (7-day pacing + common mistakes), clean tree, START_HERE |
| Owner learning | ~8.5 | concept canonicals marked; Hinglish+English; learning path owner shortcut |
| AI-agent navigation | ~9.5 | machine-readable manifest, CI-validated, 1 file to route |
| Architecture preservation | ~8.5 | concepts + counts single-sourced; chokepoint refs guarded |
| Drift resistance | ~8.5 | 10 CI checks over references/counts/navigation; manual link sweep automated |
| Debugging efficiency | ~8 | DEBUGGING_INDEX + per-flow debug layers; 2 flows completed this session |
| Token reduction (AI) | ~9 | routing 5 files → 1 manifest; 9 non-knowledge docs removed from tree |

**Composite ~8.5 / 10. Practical maximum ~9** — the ceiling is irreducible:
prose-accuracy needs human review (guards cover references/counts/navigation, not
wording), and the verify-on-touch periphery (per-app/model/flow) inherently lags
code for a solo maintainer. PKALS is at the practical-excellence band.

## 5. Deliberately NOT done (evidence-backed decisions)
- **APPS triplet NOT collapsed** — orthogonal lenses, low duplication, negligible
  token saving, slight learning loss; manifest already solved AI routing.
- **14 generic Django pages NOT created** — owner scope-narrowed; generic Django
  delegated to LEARNING/01,03,04,09 + official links; project-specific in the
  DJANGO_GUIDE hub. The "0/14" was a stale target, not a gap.
- **EXPLAINED/VALIDATION not merged** — distinct audiences (junior why vs senior
  rejected-alternatives); merging risks losing framing.
- **No docs website / auto-generation / prose-accuracy linter** — new systems,
  out of scope; low ROI / high false positives.

## 6. Maintenance model going forward (PKALS-LIVE)
- Code change ⇒ docs change same session (CLAUDE rule 12). Use CHANGE_IMPACT_MATRIX
  (file→docs) + OWNERSHIP_MATRIX (doc→trigger); future phases are pre-wired.
- Load-bearing core (KNOWLEDGE_MAP, START_HERE, AI_AGENT_GUIDE + manifest,
  ARCHITECTURE_V2 + ADRs, CHOKEPOINTS, the two matrices, DOCUMENTATION_INDEX) must
  stay true and is CI-guarded. Periphery (APPS×3, URL_ATLAS, COVERAGE counts,
  per-model/flow pages) is verify-on-touch — trust code if it lags.
- New entity gets ONE periphery page first (fan-out cap); counts stay self-counting
  lists, never hard-coded numbers; one canonical per concept, others link.
- `bash scripts/check.sh` must stay green (incl. the 10 PKALS guard checks).

### Verification Sources
All claims re-verified this session by test runs (core 18/18 green; 10 PKALS guard
checks) + grep/read on the live tree. Commit f067daf0, 2026-06-13. Confidence: High.
