# LEARNING_2_0 — PKALS (the project's knowledge system)

**Purpose.** PKALS = the permanent knowledge layer over the codebase: onboarding
academy, architecture atlas, debugging handbook, and AI-agent navigation. It
routes you to code/tests/ADRs — it is not the source of truth, it is the map.

**Audience.** New developers, the owner learning the system, and AI agents.

**When to read.** Any time you need to understand, navigate, debug, or extend the
project without scanning the repo.

**Start here (don't guess the entry):**
- **Front door for everyone:** [../START_HERE.md](../START_HERE.md) — routes you by who you are.
- **The one overview:** [../PROJECT_KNOWLEDGE_MAP.md](../PROJECT_KNOWLEDGE_MAP.md).
- **This folder's section-index:** [PROJECT_ATLAS.md](PROJECT_ATLAS.md) — what lives in each subdir.
- **AI agents:** [AI_AGENT_GUIDE/](AI_AGENT_GUIDE/README.md) + the machine-readable [AI_AGENT_GUIDE/canonical_manifest.json](AI_AGENT_GUIDE/canonical_manifest.json) (route a task in one read).
- **Learning route (ordered):** [../LEARNING_PATH.md](../LEARNING_PATH.md) (sequences both the [../LEARNING/](../LEARNING/README.md) topic lessons and this academy).

**Subdirs:** PROJECT_BRAIN (fast-answer indexes) · ARCHITECTURE_EXPLAINED (why) ·
ARCHITECTURE_VALIDATION (senior review) · CHOKEPOINTS (single-writer services) ·
REQUEST_JOURNEYS (call chains) · DATA_FLOWS (write paths) · DATABASE_GUIDE
(per-model) · APPS (per-app nav) · DJANGO_GUIDE (project-specific Django) ·
LIVING_DOCUMENTATION_SYSTEM (how PKALS stays true — PKALS-LIVE).

**When NOT to read.** Generic Django (use [../LEARNING/](../LEARNING/README.md) +
official docs); the live source of truth (that's the code + ADRs — PKALS points to them).

**Maintenance.** Drift = a bug (CLAUDE rule 12). Reference/route integrity is
CI-guarded (`core.tests.PkalsNavigationGuardTests`). History/review cycle is under
[../archive/reviews/](../archive/reviews/).
