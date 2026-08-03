---
id: docs-pkals-v2-pkals-v2-architecture
type: topic-canonical
status: active
owner: handwritten
scope: docs
anchors: —
verified: 2026-07-18
---

# PKALS v2 — ARCHITECTURE (Discovery, design-only)

> **PROPOSAL. Nothing implemented.** v2 = three thin layers ON TOP of frozen v1.
> v1 artifacts are the source of truth; v2 only READS them (single-source extends
> to v2). Companion: PKALS_V2_REQUIREMENTS.

## How v2 sits on v1 (layering)
```
            ┌─────────────────── PKALS v2 (automation + assist) ───────────────────┐
            │                                                                       │
  HUMAN ───▶│  B. AI SKILLS (Claude)        C. AUTOMATION (local, AI-free)          │
  / AGENT   │   /find-canonical  /impact     route-map · model-map · change-impact  │
            │   /trace-request  /update-docs  dead-doc · canonical · CHANGE_IMPACT  │
            │        │                              │                               │
            │        └──────────┬───────────────────┘  (both only READ v1)          │
            │              D. KNOWLEDGE-SYNC: git diff → matrix → "touch these docs" │
            │              E. SELF-HEALING (detect+report only)                      │
            └──────────────────────────────┬────────────────────────────────────────┘
                                            │ reads
   ════════════════ PKALS v1 (FROZEN — source of truth) ═══════════════════════════
   canonical_manifest.json · CHANGE_IMPACT_MATRIX · OWNERSHIP_MATRIX · CHOKEPOINTS ·
   REQUEST_JOURNEYS · DATABASE_GUIDE · URL_ATLAS · core.tests guard · the code itself
```
**Invariant:** v2 never writes v1 docs automatically; it points the human/agent at
WHICH v1 docs to edit. The code + v1 docs remain the truth.

## C. Automation layer (the load-bearing half — local, deterministic, CI-friendly)
Each is a small Python module (reuses Django introspection, not regex) that the v1
guard framework (`config/core/tests.py`) can host, or a standalone `scripts/` CLI.

| Tool | Input | Output | Mechanism |
|---|---|---|---|
| **route-map drift** | URL_ATLAS.md + Django URL resolver | routes in atlas but not resolver (and vice-versa) | `django.urls.get_resolver()` walk vs atlas route names |
| **model-map drift** | DATABASE_GUIDE pages + `apps.get_models()` | documented model/field names that no longer exist | introspect `_meta.get_fields()`; compare to doc mentions |
| **change-impact** | `git diff --name-only base..HEAD` | the CHANGE_IMPACT_MATRIX rows for those files | parse the matrix table once, key by path glob |
| **dead-doc** | a doc's `config/...py:symbol` references | references whose symbol is gone | AST-check the cited module for the symbol |
| **canonical-validation** | canonical_manifest.json | dead routes (already a v1 guard; v2 adds code-symbol depth) | extend the existing manifest guard |

**Why introspection, not regex:** Django's resolver + `apps.get_models` give the
*real* routes/models; regex over `urls.py`/`models.py` is brittle (decorators,
includes, abstract bases). Introspection = robust, low false-positive (ADR-V2-004).

## B. AI skills layer (thin wrappers over v1 — Claude `SKILL.md` files)
Each skill is a small markdown skill that tells Claude to read a v1 artifact and
return a focused answer. They do NOT embed knowledge (ADR-V2-003).

| Skill | Input | Output | Reads | Maint. cost |
|---|---|---|---|---|
| **/find-canonical** | a topic/keyword | the ONE canonical doc (+ also-links) | `canonical_manifest.json` | ~0 (manifest is CI-guarded) |
| **/impact** | changed file(s) | docs to update this session | CHANGE_IMPACT_MATRIX (+ C. change-impact tool) | low (matrix is core, guarded) |
| **/trace-request** | a URL/route/feature | the call chain + debug points | REQUEST_JOURNEYS + URL_ATLAS | low |
| **/update-docs** | a finished code change | a guided doc-sync checklist (runs /impact, opens each doc) | matrix + manifest | low |
| **/debug-flow** | a symptom | where to look + the flow's debug section | PROJECT_BRAIN/DEBUGGING_INDEX + journeys | low |
| **/architecture-review** | a diff/design | a checklist pass (ADRs touched, single-writer respected, mobile-first) | ADRs + CHOKEPOINTS + rules | medium (judgment; checklist only, not a verdict) |

**Skill design rule:** a skill's body is *instructions to read X and synthesize*,
never a copy of X. When v1 changes, the skill keeps working because it re-reads the
(CI-guarded) source. `/architecture-review` is the weakest (review is judgment, not
lookup) — it can checklist but cannot replace the adversarial review process.

## D. Knowledge-sync layer
Built on the C. change-impact tool + a git hook:
- `pre-commit` / `pre-push` (or CI on a PR): `git diff --name-only` → change-impact
  → print "you touched X; the matrix says review: [docs]. Update them or state N/A."
- **Automatable:** *which* docs to review (deterministic from the matrix).
- **Human/agent-only:** *what* to write in them (prose). The hook never edits docs;
  it can be advisory (warn) or, for matrix-keyed truth files, blocking on a PR.

## E. Self-healing documentation (detection only — "healing" = surfacing, not rewriting)
Composed entirely from C.'s detectors, run as report-only checks + one CI gate:
- stale route → route-map drift (R-E1)
- stale model/field → model-map drift (R-E2)
- broken canonical/route path → existing v1 guard + canonical-validation depth (R-E3)
- missing CHANGE_IMPACT on a commit → change-impact diff vs files-actually-changed (R-E4)
- **No auto-rewrite** (R-E5): output is a report / a generated checklist / a failing
  CI line — a human or agent does the edit. "Self-healing" is a detection+notify loop,
  not autonomous prose generation (ADR-V2-002).

## What stays human-reviewed (hard boundary)
Prose correctness · whether a "why" is still true · whether a derived/interpretation
section still holds · curatorial calls (which service is a "chokepoint", which doc is
canonical). Machines verify structure + references; humans/agents own meaning.

## Reuse map (v2 → v1, zero duplication)
manifest → /find-canonical, canonical-validation · CHANGE_IMPACT_MATRIX → /impact,
change-impact, knowledge-sync, R-E4 · REQUEST_JOURNEYS/DEBUGGING_INDEX →
/trace-request, /debug-flow · URL_ATLAS + resolver → route-map · DATABASE_GUIDE +
`apps.get_models` → model-map · `core.tests` guard → host for new blocking checks.
