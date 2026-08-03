---
id: app-storefront-views
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "storefront's two view modules — the anonymous read and the listing lane."
related: [app-storefront, app-storefront-urls]
---

# storefront — handler knowledge (2 modules)

> 📂 [storefront app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

> 💡 **Samjho aise** — Views = **reception counter**
>
> Browser se request aati hai to sabse pehle yahin aati hai. View ka kaam sirf teen cheezein hai: **request padho → permission check karo → service ko bhej do**. View khud database mein likhta **nahi** — isiliye yeh files patli hoti hain. Moti view = design ki galti.
>
> *(`storefront` app ka kaam: public website — featured products aur categories jo bahar dikhte hain.)*

## Handler groups at a glance

- **PUBLIC READ (1):** `public_home` (function, `public_views.py`) — the
  ONLY anonymous handler in the entire system
- **WRITE (8, listing_team):** Product ×4 + Category ×4 CRUD
  (`listing_views.py`, all LoginRequired + `ListingTeamMixin` :24)
- **ADMIN / ASYNC:** none · **DELETE:** real deletes, legal here (replicas)

## The two boundaries in code

**`public_views.py`** — reads config rows, renders, nothing else; its
module docstring IS the law ("never write anything — commerce boundary's
public face"). Any diff adding a write/business-query here = boundary
violation, full stop. The template it renders (`templates/public_home.html`)
also carries a **static About/Our-Story section (`#about`, 2026-07-20)** —
hardcoded public company story + process timeline, deliberately NOT
model-driven (no config rows to leak, nothing for the view to fetch).
Its motion layer (GSAP 3.13 + Lenis, vendored under
`static/storefront/vendor/`, choreography in
`static/storefront/js/home-motion.js`, plus the vanilla canvas particle
engine `ke-particles.js` shared with the login brand panel) is
presentation-only JS — degrade path is plain IntersectionObserver reveals,
so the page works with the libs absent and under `prefers-reduced-motion`.
Storefront ↔ login navigation uses cross-document View Transitions (both
pages opt in via `@view-transition`; the brand mark morphs into the login
monogram on supporting browsers, plain navigation elsewhere).

**`ListingTeamMixin`** — the trust-tier gate: one role, one lane, zero
reach elsewhere (certified). Pattern echo: a role-scoped mixin exactly like
expense's `_ManagementOnly` — different tier, same shape.

## Rules of thumb

1. New public capability = a boundary decision, not a view (README REQ #1).
2. Listing forms: uploads through `image_service`, always.
3. Keep the anonymous handler BORING — its simplicity is the security.

## Required Knowledge (this page)

- [ ] Trust tiers → [people-and-roles](../../project/people-and-roles.md)
- [ ] Validation chain → [pattern](../../concepts/patterns/validation-chain.md)

## Learning Graph

**Before:** [urls.md](urls.md). **After:** [services.md](services.md) →
`public_views.py` (a 60-line masterclass in doing nothing dangerous).
