---
id: app-tracking-views
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Why is tracking/views/ empty, and where do its handlers live?"
related: [app-tracking, app-tracking-urls]
---

# tracking — handler knowledge (an empty package, on purpose)

> 📂 [tracking app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

`config/tracking/views/` contains only `__pycache__` — the husk left by the
P4.2 view relocation. It stays as the boundary's receipt (and so nobody
"restores" views here by habit).

**The handlers:** [inventory views.md](../inventory/views.md) §tracking_*
modules (dashboard · barcodes · history · exports — groups, gates,
templates all documented there).

**Rule of thumb:** a new tracking-related SCREEN = an inventory view
calling THIS app's services. A new tracking CAPABILITY = a service verb
here ([services.md](services.md)) — screens later.

## Learning Graph

**Before:** [urls.md](urls.md) (the absence story). **After:** [inventory views.md](../inventory/views.md) §tracking modules.
