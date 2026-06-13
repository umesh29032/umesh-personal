# LEARNING_2_0/APPS — per-app navigation layer

**Purpose.** A compact per-app *navigation* view: what each app does, its
URL→View→Service→Model wiring, and a quick file list. One folder per app, each
with the same three short lenses (kept intentionally separate — orthogonal views,
not duplicates; see Session-3A evidence):
- **APP_FLOW.md** — the app's business flows (what happens, in order).
- **REQUEST_MAP.md** — URL → View → Service → Model table.
- **FILE_MAP.md** — the quick file list (which file does what).

**Audience.** A developer or AI agent who needs to *orient* in an app fast.

**When to read.** Starting work in an app; deciding where a change goes; routing.

**When NOT to read.** For the *deep* file-by-file dev guide use
[../../apps/<app>/GUIDE.md](../../apps/README.md); for the *business* view use the
code-adjacent `config/<app>/README.md`; for *why* a design exists use
[../ARCHITECTURE_EXPLAINED/](../ARCHITECTURE_EXPLAINED/README.md).

**The three app-doc layers (which one do I want?).**
| Need | Read | Where |
|---|---|---|
| Orient fast / route a change | this folder (APP_FLOW · REQUEST_MAP · FILE_MAP) | `docs/LEARNING_2_0/APPS/<app>/` |
| Deep file-by-file dev map | the app GUIDE | `docs/apps/<app>/GUIDE.md` |
| Business view, next to the code | the app README | `config/<app>/README.md` |

**Apps:** accounts · production · expense · raw_materials · tracking · inventory ·
storefront · core. (Count is whatever INSTALLED_APPS has — not hard-coded.)

**Related folders:** [../CHOKEPOINTS/](../CHOKEPOINTS/README.md) (the single-writer
services these apps call) · [../REQUEST_JOURNEYS/](../REQUEST_JOURNEYS/README.md)
(full call chains) · [../DATABASE_GUIDE/](../DATABASE_GUIDE/README.md) (per-model).
Canonical overview of the whole system: [../../PROJECT_KNOWLEDGE_MAP.md](../../PROJECT_KNOWLEDGE_MAP.md).
