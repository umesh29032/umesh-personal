---
id: apps-readme
type: entry-index
status: active
owner: handwritten
scope: all apps
anchors: —
verified: 2026-07-13
---

# docs/apps — per-app deep-dive guides (file-by-file)

App README (config/<app>/README.md) = business view, code ke paas.
YEH folder = developer's file-by-file map: kaunsi file kya hai, kis pattern
pe likhi hai, dots kaise connect hote hain, aur har topic online kahan padhe.

| App | Guide |
|---|---|
| production | [production/GUIDE.md](production/GUIDE.md) — the factory floor (biggest app) |
| expense | [expense/GUIDE.md](expense/GUIDE.md) — all the money |
| accounts | [accounts/GUIDE.md](accounts/GUIDE.md) — identity + RBAC |
| inventory | [inventory/GUIDE.md](inventory/GUIDE.md) — dashboards/access glue |
| raw_materials | [raw_materials/GUIDE.md](raw_materials/GUIDE.md) — cloth stock |
| tracking | [tracking/GUIDE.md](tracking/GUIDE.md) — history + identity |
| storefront | [storefront/GUIDE.md](storefront/GUIDE.md) — public site |
| machines | [machines/GUIDE.md](machines/GUIDE.md) — physical machine assets + operator possession windows (R10-A LIVE 2026-07-05; owner-certified OWN-F/MGT-F) |
| patterns_ai | [patterns_ai/GUIDE.md](patterns_ai/GUIDE.md) — pattern layout tool, photo→geometry→marker (Vision V2 🔒; Foundation v1.0 STABLE, phases 1–5 frozen; blurbs refreshed 2026-07-13 Q-A9) |
| core | [core/GUIDE.md](core/GUIDE.md) — shared kernel |

**WINDOW / infra apps** (read-only or dev-only by shape — they own no business truth):

| App | Guide |
|---|---|
| learning | [learning/GUIDE.md](learning/GUIDE.md) — the in-app engineering academy `/learn/`; renders `docs/*_course/*.md`, zero content models, per-user progress only |
| bod | [bod/GUIDE.md](bod/GUIDE.md) — owner command center; read-only, zero models |
| verification | [verification/GUIDE.md](verification/GUIDE.md) — release/production verification checks |
| devseed | [devseed/GUIDE.md](devseed/GUIDE.md) — dev seeding + the knowledge_sync drift detectors |

Read order for a fresher: PROJECT_KNOWLEDGE_MAP → LEARNING_PATH → app README
→ THIS guide jab us app ki file kholni ho.
