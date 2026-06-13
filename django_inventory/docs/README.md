# docs/ — documentation map (start here if you're lost)

> **New here? → [START_HERE.md](START_HERE.md).** It routes you (new dev / owner /
> AI agent) to exactly what to read. This file is just the *map of the folder* —
> what each area is, and which of several similar-looking places is the real one.

## Doc-type legend (what kind of doc is this?)
| Type | Where it lives |
|---|---|
| **Entry / navigation** | [START_HERE.md](START_HERE.md) · [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) · [LEARNING_2_0/PROJECT_ATLAS.md](LEARNING_2_0/PROJECT_ATLAS.md) |
| **Overview** | [PROJECT_KNOWLEDGE_MAP.md](PROJECT_KNOWLEDGE_MAP.md) (the ONE overview) · [../GLOSSARY.md](../GLOSSARY.md) |
| **Architecture (current)** | [../SYSTEM_DESIGN.md](../SYSTEM_DESIGN.md) · [ARCHITECTURE_V2.md](ARCHITECTURE_V2.md) (worker-truth + settlement; §11 binding) |
| **Decisions (binding)** | [adr/](adr/) (ADR-0001…0010) |
| **Learning** | [LEARNING/](LEARNING/README.md) (lessons) + [LEARNING_2_0/](LEARNING_2_0/README.md) (the PKALS academy) — see note below |
| **Per-app** | [apps/<app>/GUIDE.md](apps/README.md) + `config/<app>/README.md` + [LEARNING_2_0/APPS/<app>/](LEARNING_2_0/APPS/README.md) — see note below |
| **Reference / flows** | [LEARNING_2_0/CHOKEPOINTS](LEARNING_2_0/CHOKEPOINTS/README.md) · [REQUEST_JOURNEYS](LEARNING_2_0/REQUEST_JOURNEYS/README.md) · [DATA_FLOWS](LEARNING_2_0/DATA_FLOWS/README.md) · [DATABASE_GUIDE](LEARNING_2_0/DATABASE_GUIDE/README.md) · [URL_ATLAS](LEARNING_2_0/URL_ATLAS.md) |
| **Debugging** | [LEARNING_2_0/PROJECT_BRAIN/DEBUGGING_INDEX.md](LEARNING_2_0/PROJECT_BRAIN/DEBUGGING_INDEX.md) |
| **Subsystem deep-dive** | [production/](production/OVERVIEW.md) (cloth → stages → cutting → barcode) |
| **Planning / operations** | [ROADMAP_REVIEW_POST_C1_2026_06_11.md](ROADMAP_REVIEW_POST_C1_2026_06_11.md) · [PENDING_BACKLOG.md](PENDING_BACKLOG.md) · [SOAK_TRACKER.md](SOAK_TRACKER.md) · [ARCH_READINESS_REVIEW_2026_06_12.md](ARCH_READINESS_REVIEW_2026_06_12.md) · [REMEDIATION_PLAN.md](REMEDIATION_PLAN.md) + [TARGET_ARCHITECTURE.md](TARGET_ARCHITECTURE.md) (parked) |
| **AI-agent layer** | [LEARNING_2_0/AI_AGENT_GUIDE/](LEARNING_2_0/AI_AGENT_GUIDE/README.md) + `canonical_manifest.json` |
| **Maintenance (PKALS-LIVE)** | [LEARNING_2_0/LIVING_DOCUMENTATION_SYSTEM/](LEARNING_2_0/LIVING_DOCUMENTATION_SYSTEM/README.md) |
| **History (never current)** | [archive/](archive/) |
| **Rendered snapshots** | [pdf/](pdf/) (md is the live truth) |

## Three things that look similar — which is the real one?

**1. `LEARNING/` vs `LEARNING_2_0/` — both active, NOT versions of each other.**
- `LEARNING/` = **topic lessons** (Django, locks, SQL, the truths, costing, lifecycle) — *teaching* material, read in order.
- `LEARNING_2_0/` = the **PKALS academy** — project-specific reference + navigation (chokepoints, journeys, flows, per-model, the "why" essays, the AI layer).
- `LEARNING_2_0` is **not** "a newer LEARNING that replaces it." Both are current; the ordered route through both is [LEARNING_PATH.md](LEARNING_PATH.md). *(The name is historical; a future rename is deferred.)*

**2. Per-app docs live in THREE intentional layers — pick by need:**
| You want… | Read | Path |
|---|---|---|
| Business view, next to the code | the app README | `config/<app>/README.md` |
| Deep file-by-file dev map | the app GUIDE | [apps/<app>/GUIDE.md](apps/README.md) |
| Fast orientation (flow / request-map / file-list) | the nav lenses | [LEARNING_2_0/APPS/<app>/](LEARNING_2_0/APPS/README.md) |

**3. Some canonical docs live at the REPO ROOT, not in `docs/`:**
[../README.md](../README.md) · [../CLAUDE.md](../CLAUDE.md) (working rules) ·
[../SYSTEM_DESIGN.md](../SYSTEM_DESIGN.md) · [../GLOSSARY.md](../GLOSSARY.md) ·
[../ABOUT_THIS_PROJECT.md](../ABOUT_THIS_PROJECT.md) · [../UI_COMPONENTS.md](../UI_COMPONENTS.md) ·
[../CHANGELOG.md](../CHANGELOG.md). If two architecture docs seem to disagree,
**ARCHITECTURE_V2 + the ADRs win** for worker-truth/settlement; SYSTEM_DESIGN is the
full current-state design.

## Conventions
- Doc drift is a bug (CLAUDE rule 12). The PKALS tree's links/routes/counts are
  CI-guarded (`config/core/tests.py`). `archive/` is history — never treat it as current.
- The complete catalogue of every active doc is [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md);
  this file is the quick map.
