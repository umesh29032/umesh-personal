---
id: app-storefront
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "I'm touching the public site or listing surfaces — what does storefront own, and what does it teach about trust boundaries?"
related: [app-accounts, pattern-validation-chain, project-people-and-roles]
---

# storefront — the complete app map

> 📂 [Apps](../README.md) · [LOS home](../../README.md) — *andar:
> [URLs](urls.md) · [Views](views.md) · [Models](models.md) · [Services](services.md)*
> **This app's engineering lesson: TRUST BOUNDARIES** — the system's only
> anonymous-facing surface, and the walls that keep the outside OUT.

## Mental Model — read this before anything

> **The shop window.** The street (anonymous internet) may LOOK — never
> touch. The window-dresser (listing_team) may arrange the DISPLAY — never
> enter the workshop. And the display is made of REPLICAS (presentation
> rows), not the workshop's real inventory — so nothing the street sees,
> and nothing the dresser breaks, can ever reach manufacturing or money.
> *(Sadak dekhe, sajaane-wala sajaye, karkhana alag hi rahe.)*

## Common Misconceptions

- **"Storefront products ARE the factory's products."** No — `FeaturedProduct`
  etc. are PRESENTATION rows, deliberately decoupled from
  `production.Product` (the manufacturing master). Data ownership IS the
  boundary: the display owns its replicas.
- **"The public page reads live business data."** It composes CONFIG rows
  (HomePageConfig, cards, links) — zero business queries cross to the street.
- **"listing_team is like manager-lite."** It's a different TRUST TIER:
  full CRUD over display data, ZERO reach into any other app (certified
  role walls).
- **"There's an API."** Not yet — no REST surface, no versioning, no
  idempotency keys, because there are no external CALLERS yet. Honest
  absences, with the G2 seam already marked (order capture lands HERE,
  never in production — the boundary's future, written in urls.py).

## Real Engineering Questions

**PM: "Let customers place orders."**
The G2 project — think boundary-first: order = EXTERNAL input → its own
models HERE (never writing production/expense directly) → validation
chain hardens (anonymous input!) → idempotency keys become REAL (double-
submit = double order) → rate limiting → error contracts for the public
form → then an INTERNAL handoff (an owner-reviewed bridge) into
manufacturing. The lesson: extending a trust boundary = new models + new
guards on THIS side, never a hole through it.

**PM: "Show real-time stock on the public site."**
Which side owns the number? Manufacturing. Crossing it raw = coupling the
street to the workshop. The boundary answer: a PUBLISHED projection
(explicitly exported display rows, refreshed by an internal act) — the
replica pattern this app already lives by.

**PM: "A listing user uploaded a 50MB 'image'."**
`image_service.process_and_attach` = the upload boundary: validate, process,
constrain BEFORE storage — the validation-chain pattern applied to files.

## Reading Strategy

- **Beginner:** Mental Model → [urls.md](urls.md) §1 (the public face) →
  §§2–5.
- **Intermediate:** [models.md](models.md) (replica ownership) →
  [views.md](views.md) gates.
- **Senior:** the G2 REQ above → the honest absences (versioning/
  idempotency) → [what-must-never-cross](models.md) list.

## Start Here — common tasks

| Need to… | Go to |
|---|---|
| Change the public homepage | [urls.md](urls.md) §1 → HomePageConfig + card models |
| Listing CRUD (products/categories) | §§2–9 (listing_team lane) |
| Uploads/images | [services.md](services.md) `image_service` |
| Add anything ORDER-like | STOP → the G2 REQ (boundary project, owner conversation) |
| Role questions | [people-and-roles](../../project/people-and-roles.md) (listing_team walls certified) |

## What this app owns

The public homepage (config-composed, read-only) · presentation data
(FeaturedProduct, Category, HeroShowcaseCard, WhyUsCard, FooterLink,
NavLink, HomePageConfig) · the listing_team editing lane · upload
processing.

## What it does NOT own — and WHAT MUST NEVER CROSS

Manufacturing truth (production.Product et al.) · money (expense) · piece
identity (tracking) · user identity (accounts). **The never-cross list:**
no write path from ANY storefront surface into another app's tables; no
business query on the anonymous page; no manufacturing FK on presentation
rows (replicas reference by content, not by coupling).

## The census

- **URLs:** 9 (1 public root + 8 listing CRUD, `config/storefront/urls.py`) — [urls.md](urls.md)
- **Views:** `public_views.py` (the no-auth read) + `listing_views.py` (8 CRUD + `ListingTeamMixin`) — [views.md](views.md)
- **Models:** 7 presentation models (`models.py`, 317 lines) — [models.md](models.md)
- **Services:** `image_service.py` (the upload boundary) — [services.md](services.md)
- **Tests:** `tests.py` + certified listing-role walls

## The laws to carry in (the lesson, condensed)

1. **Anonymous = read-only, config-composed** — the street never triggers
   business logic.
2. **Trust tiers get their own data** — the display owns replicas;
   ownership IS the boundary.
3. **Every upload is hostile until processed** (image_service).
4. **Extending the boundary (G2) = new models + guards on THIS side** —
   never a write-hole through it.

## Engineering Checklist — pre-flight

- [ ] Does this change let the street TRIGGER anything? (it must not)
- [ ] Does any new field/FK couple presentation rows to another app's truth? (replicas stay replicas)
- [ ] Uploads: through `image_service`, size/type-constrained
- [ ] listing_team walls re-verified on any new surface (certified matrix mindset)
- [ ] Order-like features → G2 boundary project, owner-gated
- [ ] kos-sync: this app + people-and-roles if the role's reach changes

## Change Impact — touching this app affects

The public face (SEO/first impressions) · listing_team's entire world ·
homepage config composition · upload storage. NOT manufacturing/money —
if your change DOES affect them, you've crossed the boundary; stop.

## Learning Graph

**Before:** [people-and-roles](../../project/people-and-roles.md) →
[auth-hardening](../../concepts/security/auth-hardening.md) (the other
outside-facing wall). **After:** [pattern: validation-chain](../../concepts/patterns/validation-chain.md)
→ the G2 REQ (the boundary's future).
