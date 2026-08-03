---
id: apps-core-guide
type: app-guide
status: active
owner: handwritten
scope: core
anchors: config/core/
verified: 2026-07-13
---

# core app — file-by-file GUIDE (shared kernel)


> **Date primitive (2026-08-01).** Every "today"/"this month" in this app uses `timezone.localdate()`, never `timezone.now().date()` (which returns a **UTC** date and is one day behind for 5.5h daily under `TIME_ZONE=Asia/Kolkata`). Enforced repo-wide by `core.tests.LocalDateGuardTests`. Background: [UTC_LOCAL_DATE_BUG_CLASS_2026_08_01.md](../../UTC_LOCAL_DATE_BUG_CLASS_2026_08_01.md). The pin itself lives in this app: `core.tests.LocalDateGuardTests`, beside the existing architecture guardrails.

> Business view: [config/core/README.md](../../../config/core/README.md).

| File | What |
|---|---|
| `models.py` | TimeStampedModel (abstract) · ActiveManager (.active opt-in) |
| `observability.py` | logging helpers |
| `tests.py` | ★ foundation-purity + DOC-ACCURACY guards (SYSTEM_DESIGN + KNOWLEDGE_MAP machine-checked!) |

Import pyramid ka basement: core kisiko import nahi karta (CI gate 1/4).

## Topics yahan use hote hain — kahan padhein
Har concept ka official link + "is project me kahan" mapping:
[../../LEARNING/10_ONLINE_RESOURCES.md](../../LEARNING/10_ONLINE_RESOURCES.md).
App ka business-view: README (code ke saath). Deep lessons: [docs/LEARNING/](../../LEARNING/README.md).
