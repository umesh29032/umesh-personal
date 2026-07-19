---
id: readme-apps
type: system
verified: 2026-07-19
---

# Apps — app-first navigation (the daily-development layer)

*(Part of the [KOS](../README.md). Discoverability pass, owner-ordered 2026-07-19.)*

## Teacher's note

Features teach WHAT the system does; this layer answers the question you
ask at 9 AM with your editor open: *"I'm working in THIS app — which URL,
which handler, which model, which service, which file?"* Seconds-to-code
navigation, verified against source *(subah sabse pehle yahi kholna hai —
wahi acceptance test hai)*.

Every app gets the same four-page shape + a map README:
**README** (owns / doesn't own / census / laws) · **urls.md** (every route:
why → handler → what changes → where it ends) · **views.md** (handler
knowledge: gates, calls, side effects) · **models.md** (who writes, what
protects) · **services.md** (responsibilities, callers, failure modes).

## The apps

| App | Status | One line |
|---|---|---|
| [expense/](expense/README.md) | ✅ LOS | ALL worker money — settlement, ledger, advances, cash, factory expenses |
| [production/](production/README.md) | ✅ LOS | the factory floor: Adda, stages, worker tasks, cutting, pools — 80 URLs |
| [accounts/](accounts/README.md) | ✅ LOS | the foundation: identity, OTP login, permission brain, the S2/S3 absences |
| [inventory/](inventory/README.md) | ✅ LOS | the shell: sidebar pair (menu=gate), dashboards, /tracking/ surface |
| [raw_materials/](raw_materials/README.md) | ✅ LOS | LESSON: inventory consistency + reservations — the cloakroom |
| [tracking/](tracking/README.md) | ✅ LOS | pure data app: piece identity + THE history pen (zero URLs, by design) |
| [machines/](machines/README.md) | ✅ LOS | LESSON: capability vs unit vs possession — the tool crib |
| [storefront/](storefront/README.md) | ✅ LOS | LESSON: trust boundaries — the shop window (one anonymous face) |
| [core/](core/README.md) | ✅ LOS | THE CONCLUSION: 89 lines + five values — why the project feels the way it does |

*(devseed/verification/bod = dev-infra apps; covered if the pass reaches them.)*

## How this layer relates to the rest

App pages are NAVIGATION — the WHY lives in [features](../features/README.md)
and [concepts](../concepts/README.md); the structural per-URL chain lives in
generated [docs/features/ cards](../../docs/features/HUMAN_GUIDE.md); history
lives in docs/. App pages point at all three and at source paths directly —
they never re-teach *(rasta batao, sabak nahi dohrao)*.
