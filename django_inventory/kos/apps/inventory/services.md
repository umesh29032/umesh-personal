---
id: app-inventory-services
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "What is inventory's runtime machinery — the sidebar trio that touches every request?"
related: [app-inventory, feature-rbac-access]
---

# inventory — service knowledge (the sidebar trio + the tombstone)

> 📂 [inventory app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

> 💡 **Samjho aise** — Services = **counter ke peeche baitha clerk**
>
> **Asli kaam yahin hota hai** — database mein likhna, hisaab lagana, rules lagana. Is project ka sabse bada niyam: *har likhne ka kaam service mein hoga, view mein kabhi nahi*. Isi wajah se paisa surakshit rehta hai — har table ka **ek hi** likhne wala hota hai.
>
> *(`inventory` app ka kaam: admin ka hissa — roles, sidebar access, dashboards.)*

## The trio that makes the pair real

One `SidebarItemRule` row produces BOTH effects through three cooperating
pieces — change any one, re-test all three:

| Piece | File | Job | Runs |
|---|---|---|---|
| **Writer** — `sidebar_service.save_sidebar_rules(assignments)` | `config/inventory/services/sidebar_service.py` | the sole writer of rule assignments (from the SA editor) | on save |
| **Renderer** — `sidebar(request)` context processor | `config/inventory/context_processors.py` | builds each user's menu from the rules (registered in settings TEMPLATES) | every template render |
| **Enforcer** — `SidebarAccessMiddleware` | `config/inventory/middleware.py` | blocks managed URLs by the SAME decision (`accounts.can_access_url_name`) | every request |

Failure modes by piece: writer (bad assignment shape → loud validation) ·
renderer (menu drift = usually a stale/missing rule row, check
`test_sidebar_order`) · enforcer (redirect loops = touched the exempt
list; JSON paths return 403 JSON, don't redirect).

## Decision logic lives ELSEWHERE (on purpose)

`can_access_url_name` + role/skill checks = `accounts.permission_service`.
Inventory consumes decisions; it never makes them — that's why the models
moved ([models.md](models.md)). Cross-app direction: inventory → accounts,
never the reverse.

## Tracking surface services

The /tracking/ views call `tracking.services` (`config/tracking/services/barcode_service.py` for scan
resolution + status transitions, history_service timelines — sole writer
of `*History`, ADR-0002) and the export pipeline (manifest rows; refuses
until barcode-gen stage completes). Data ownership stays with the
`tracking` app — inventory owns only the SURFACES (P4.2 D1: so tracking
imports no production).

## The tombstone — `signals.py`

Not machinery: a documented GRAVE. It records WHY signals were removed
(fire outside caller's transaction · undefined order · invisible writers)
and instructs: new triggered operations = explicit service calls. Its
comment still names the long-removed `StockService` — historical text,
not a live pointer. **Never revive this file** (ADR-0001;
[service-layer §4](../../concepts/architecture/service-layer.md)).

## Adding/changing here — the checklist

Rule edits are SECURITY edits (menu = gate) → middleware changes re-test
the four pass-through lanes + loop exemptions → renderer changes stay
query-lean (every page pays) → export changes preserve manifest history
(re-download > regenerate) → kos-sync this file + [rbac-access](../../features/rbac-access.md).

## Engineering Decision (the middleware)

*Problem:* menu visibility and URL access must never drift. *Options:*
(A) per-view decorators mirroring menu config — two artifacts, guaranteed
drift; (B) hide menus only — security theater; (C) ONE rule row read by
both the renderer and a middleware enforcer. *Chosen:* C. *Trade-offs:*
every request pays a rule lookup; exempt-lane care (loops). *Still today?*
**Yes** — the certifications' "0 hidden-but-reachable" result is this
decision's receipt.

## Required Knowledge (this page)

- [ ] Middleware + context processors → [settings](../../concepts/django/settings.md) · [request-through-stack](../../flows/request-through-stack.md)
- [ ] Where decisions live (accounts) vs surfaces (here) → [models.md](models.md)

## Learning Graph

**Before:** [views.md](views.md). **After:** `accounts.permission_service`
(the brain this trio consults) → [auth-hardening](../../concepts/security/auth-hardening.md).
