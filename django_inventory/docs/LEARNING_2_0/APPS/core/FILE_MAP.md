---
id: l2-apps-core-file-map
type: topic-canonical
status: active
owner: handwritten
scope: core
anchors: config/core/
verified: 2026-07-13
---

# core — FILE_MAP

## TL;DR (1 min)
FILE_MAP: every important file in this app and how they connect.

## models.py — **TimeStampedModel** (abstract: created_at auto_now_add / updated_at
auto_now — columns COPY into each child table, no JOIN) · **ActiveManager**
(`.active` opt-in manager filtering is_active; default `.objects` untouched so
rows never hide accidentally).
## observability.py — logging helpers (shared infra).
## tests.py ★ — DocAccuracyTests (machine-checks SYSTEM_DESIGN + PROJECT_KNOWLEDGE_MAP:
Django version, no debunked claims, karigar=historical) + foundation-purity (core+accounts
import no domain app). Architecture-as-test.
## Junior note: core SAVES nothing. It's abstract base + managers + guards. If a
thing knows what an Adda is, it does NOT belong here.

---
*Depth: [config/core/README.md](../../../../config/core/README.md) (business) ·
[docs/apps/core/GUIDE.md](../../../apps/core/GUIDE.md) (file-by-file). This = navigation/flow only.*
