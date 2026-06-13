# PKALS v2 — REQUIREMENTS (Discovery, design-only)

> **Status: PROPOSAL. Nothing implemented.** PKALS v1 is frozen + released
> (docs/PKALS_RELEASE_v1.md). v2 is a SEPARATE initiative layered on top — it must
> not modify v1 architecture, canonicals, navigation, the CI guard, or the
> maintenance contract except normal maintenance-mode updates. This package decides
> whether v2 should exist and what its scope is. Audience: solo developer running a
> large ERP with AI-assisted development.

## The problem v2 addresses (and the problem it does NOT)
v1 made the documentation **correct, single-sourced, navigable, and structurally
guarded** (10 CI checks fail the build on reference/route/count/navigation drift).
v1's residual ceiling (~8.5/10, stated in the release) is exactly two things:
1. **Periphery drift is human-caught, not machine-caught.** v1 marks APPS/×3,
   URL_ATLAS, per-model DATABASE_GUIDE, per-flow pages "verify-on-touch, may lag."
   Nothing detects when a route/model/field they describe diverges from code.
2. **PKALS-LIVE is discipline, not tooling.** "Run CHANGE_IMPACT_MATRIX, update the
   listed docs" is a manual habit; a solo dev under load will skip it.

**v2's job = convert that manual discipline into cheap, deterministic tooling + a
thin AI-skills layer that makes the v1 structure callable.** v2 is NOT a content
initiative — more learning pages would re-bloat exactly what v1 spent five sessions
removing.

## Scope (in)
- **C. Automation layer** — local scripts (no AI required) that DETECT doc/code drift.
- **B. AI skills layer** — thin Claude skills that wrap v1's manifest + matrices.
- **D. Knowledge-sync layer** — map a code diff to the docs it should touch (notify).
- **E. Self-healing (detection only)** — flag stale routes/models/canonicals/missing
  CHANGE_IMPACT; never auto-rewrite prose.

## Scope (out — explicit non-goals)
- **A. Heavy online-learning system** — v1 already has `LEARNING/` lessons +
  `LEARNING/10_ONLINE_RESOURCES` (official links mapped to project usage) +
  `DJANGO_GUIDE`. A new learning system would duplicate them and re-teach generic
  content the owner explicitly scope-rejected. (Thin curation only, if anything.)
- **Auto-rewriting docs** — prose accuracy is the irreducible human/AI-judgment part
  (v1 release "known limitations"); machines detect, humans/agents write.
- **Docs website / static-site generator / doc auto-generation from code** — bloat
  for a solo dev; the md tree + `canonical_manifest.json` already serve humans + AI.
- **Any change to v1 canonicals, guard, or contract** beyond maintenance.

## Requirements by area

### A. Online Learning System (minimal / mostly satisfied by v1)
- R-A1: External learning stays **referenced, not copied** — extend `LEARNING/10_ONLINE_RESOURCES` if a genuinely missing topic appears; do not create parallel learning trees. *(Most of A is already done; see Cost/Benefit — recommended NOT-WORTH as a system.)*
- R-A2: Any external link added must map to "where it is used in THIS project" (the existing LEARNING/10 contract). No generic re-teaching.

### B. AI Skills Layer
- R-B1: Each skill **reads v1 canonicals** (manifest, matrices, journeys) — never embeds a copy (single-source extends to skills; a skill that duplicates drifts).
- R-B2: Skills must degrade gracefully — if a doc is missing, say so, don't fabricate.
- R-B3: Candidate skills + their I/O + maintenance cost are specified in ARCHITECTURE §B.

### C. Automation Layer (local, AI-free)
- R-C1: All checks run **without an AI agent** (plain `python`/`bash`), CI-friendly, and reuse Django introspection (URL resolver, `apps.get_models`) — **not regex** — for robustness.
- R-C2: Checks are **report-or-fail**, never auto-edit. New blocking checks join `scripts/check.sh`; noisy/heuristic checks are report-only.
- R-C3: Reuse the existing `core.tests` guard framework where a check is deterministic enough to block.

### D. Knowledge-Sync Layer
- R-D1: Given a set of changed files (e.g. `git diff --name-only`), output the docs the CHANGE_IMPACT_MATRIX says to review — deterministically.
- R-D2: Distinguish **automatable** (which docs to touch) from **human-only** (what to write). Never claim to have updated content.

### E. Self-Healing Documentation (detection)
- R-E1: Detect stale routes (a route named in URL_ATLAS absent from the resolver, or vice-versa).
- R-E2: Detect stale model references (a doc cites a model/field that no longer exists).
- R-E3: Detect broken canonicals (manifest/route path gone — already covered by the v1 guard; v2 extends to code symbols).
- R-E4: Detect missing CHANGE_IMPACT (a commit touched a matrix-keyed file but none of its listed docs changed) — report on the diff.
- R-E5: All E checks are **detect + report** (optionally open a checklist); zero auto-rewrite.

## Success criterion
v2 succeeds if, after it ships, the solo dev's **per-change doc-maintenance effort
drops** (the matrix lookup + drift check is automatic) and **periphery drift is
caught by CI instead of by a future reader** — with **no increase in file count of
the v1 knowledge tree** and no new prose to maintain.

See: PKALS_V2_ARCHITECTURE · PKALS_V2_ROADMAP · PKALS_V2_ADR_PROPOSALS · PKALS_V2_EFFORT_ESTIMATE.
