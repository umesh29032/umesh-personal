---
id: start-here
type: entry-index
status: active
owner: handwritten
scope: all — navigation/state
anchors: —
verified: 2026-07-13
---

# START HERE — the one front door

> Single entry point for the whole repository. You do **not** need to know any
> other filename to begin. Find your row, read exactly what it says, stop there.
> Everything else is reachable from those files. (Lost later? Come back here.)

---

## Who are you?

| You are… | Read exactly this, in order | Then stop |
|---|---|---|
| **A — new developer** (will touch code) | 1. [PROJECT_KNOWLEDGE_MAP.md](PROJECT_KNOWLEDGE_MAP.md) (the whole picture) → 2. [LEARNING_PATH.md](LEARNING_PATH.md) (the canonical ordered route — includes the 7-day pacing + common beginner mistakes) → for ANY UI work: [../UI_COMPONENTS.md](../UI_COMPONENTS.md) (**the certified component library** — compose from its canon table, never invent) → for dev data / seeding questions: [DEV_DATASET_ARCHITECTURE.md](DEV_DATASET_ARCHITECTURE.md) (🔒 the frozen dataset spec — handles, scenarios, service-path seeding law) | You now know where every layer lives. Open the app GUIDE for whatever you touch. |
| **B — owner / learner** (understand, not code) | 1. [../GLOSSARY.md](../GLOSSARY.md) (the words) → 2. [PROJECT_KNOWLEDGE_MAP.md](PROJECT_KNOWLEDGE_MAP.md) §1–§4 (business + the two truths) → 3. [PRODUCT_DESIGN_DOCUMENT.md](PRODUCT_DESIGN_DOCUMENT.md) (product truth) + [FACTORY_OPERATIONS_MASTER.md](FACTORY_OPERATIONS_MASTER.md) (operations truth: rates, rulings, settled journeys) → 4. [LEARNING/](LEARNING/README.md) lessons in number order | You understand the business, the product intent, and how money/work are kept honest. |
| **C — AI agent** (zero context, about to act) | 1. [LEARNING_2_0/AI_AGENT_GUIDE/README.md](LEARNING_2_0/AI_AGENT_GUIDE/README.md) (canonical_manifest routing + canonical lookup + never-modify) → 2. then the canonical doc for your task from that guide | You can act without scanning the repo. Obey the never-modify list. |
| **Just need one answer** (any of the above) | [LEARNING_2_0/PROJECT_BRAIN/README.md](LEARNING_2_0/PROJECT_BRAIN/README.md) — feature→code, term→file, symptom→fix, ADR deps, phase→files | Fastest path to a single fact. |

---

## The map of maps (so you never wonder "which overview?")

There is **one** project overview and **one** PKALS navigation index. They do not overlap:

- **[PROJECT_KNOWLEDGE_MAP.md](PROJECT_KNOWLEDGE_MAP.md)** — THE overview. Business → architecture → database → code, in one file. This is the canonical big picture; if two docs ever disagree on the overview, this wins.
- **[LEARNING_2_0/PROJECT_ATLAS.md](LEARNING_2_0/PROJECT_ATLAS.md)** — the **index of the PKALS learning system** (docs/LEARNING_2_0/): which subdir holds data-flows, request-journeys, chokepoints, the AI guide, the living-doc system. It does **not** re-explain the project — it points into PKALS.

Everything active is also listed in [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md). Working rules for any change: [../CLAUDE.md](../CLAUDE.md). Writing or changing ANY documentation (naming, metadata, lifecycle, linking, ownership): **[DOC_STANDARDS.md](DOC_STANDARDS.md)** — the frozen documentation constitution (🔒 `frozen-v1` 2026-07-13).

Route-level structural lookup (which view serves a URL, which feature owns it, per-feature member routes/models): **[features/README.md](features/README.md)** — the ⚙️ generated features/URL-card layer (528 cards + 28 feature pages, rendered from the knowledge graph; an index, not truth — never hand-edit; fix the source, rebuild the graph, regenerate).

---

## Not a reader front door (operational / meta — ignore unless that's your job)

[PENDING_BACKLOG.md](PENDING_BACKLOG.md) (open work) ·
[IMPLEMENTATION_ROADMAP_PDD_V1.md](IMPLEMENTATION_ROADMAP_PDD_V1.md) (THE roadmap) ·
[MANUFACTURING_V1_FREEZE.md](MANUFACTURING_V1_FREEZE.md) (🔒 the V1 freeze package).
These are work-tracking, not learning routes. New readers skip them. PKALS's own
build log + review cycle (WORK_LOG, the PKALS_*REVIEW/SCORECARD set) and the past
consolidation audit are archived under [archive/](archive/) — history, not current.
