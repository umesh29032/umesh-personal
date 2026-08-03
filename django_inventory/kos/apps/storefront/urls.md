---
id: app-storefront-urls
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "storefront's 9 URLs — one anonymous face + eight listing-team lanes, individually."
related: [app-storefront]
---

# storefront — URL Learning Pages (all 9, individually)

> 📂 [storefront app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)
> Source: `config/storefront/urls.py` (public root mounted by config/urls.py;
> /storefront/ = listing_team lane). The file's own docstring marks the G2
> seam: *"order capture lands HERE — never in production."*

> 💡 **Samjho aise** — URLs = **address book**
>
> Yeh file batati hai kaunsa web address (jaise `/production/addas/`) kis view pe jaata hai. Jab aapko pata na ho ki koi page kis code se banta hai — **hamesha yahin se shuru karo**.
>
> *(`storefront` app ka kaam: public website — featured products aur categories jo bahar dikhte hain.)*

**Reading Strategy** — *Beginner:* §1. *Intermediate:* §§2–9.
*Senior:* §1's error-contract note + the absences at the bottom.

### 1. `/` — `public_home` ⭐ THE ANONYMOUS FACE
**Purpose:** the public homepage — hero, cards, featured products, links.
**Trust tier:** ANONYMOUS — no login, and (the law) **no writes, no
business queries**: the view composes CONFIG rows (HomePageConfig +
card/link models) into `public_home.html`.
**Method:** GET → `public_home` (function, `views/public_views.py:22` —
docstring: *"commerce boundary's public face"*).
**Error contract (public pages have one!):** unknown paths → the styled
404; the page renders even with EMPTY config (missing rows degrade to
absent sections, never 500 — the street never sees a stack trace).
**Performance:** a handful of small config reads; cacheable by nature.
**Security:** nothing personal rendered · CSRF irrelevant (no forms) ·
the app's entire attack surface for the street is THIS read.
**Why simple (and why that's the whole point):** an anonymous surface is
exactly as safe as it is boring — every capability you add to the street
is a capability you must defend.

## The listing_team lane (§§2–9 — all LoginRequired + ListingTeamMixin)

*Shared context (once): the dresser's CRUD over REPLICA rows; the role's
walls are certified (listing_team reaches nothing else). Every POST is
CSRF-protected; uploads route through `image_service`.*

### 2. `products/` — `product_list`
GET → `ProductListView` (`listing_views.py:32`). The display-products
board. **Misconception guard on the page itself:** these are
`FeaturedProduct` replicas — NOT manufacturing products.

### 3. `products/add/` — `product_add`
GET+POST → `ProductCreateView` (:61). New display item: content + images
(→ [services.md](services.md) upload boundary). Failure modes: form
validation; oversized/wrong-type images refused at processing.

### 4. `products/<pk>/edit/` — `product_edit`
GET+POST → `ProductUpdateView` (:80). Re-dress the window; replicas edit
freely BECAUSE they're replicas (no business truth at stake — the
ownership decision paying off).

### 5. `products/<pk>/delete/` — `product_delete`
POST → `ProductDeleteView` (:98). Real delete is LEGAL here — presentation
rows carry no history obligations (contrast: money/history apps have no
delete routes — learn from the CONTRAST).

### 6. `categories/` — `category_list`
GET → `CategoryListView` (:115). Display grouping for the window.

### 7. `categories/add/` — `category_add`
GET+POST → `CategoryCreateView` (:138).

### 8. `categories/<pk>/edit/` — `category_edit`
GET+POST → `CategoryUpdateView` (:155).

### 9. `categories/<pk>/delete/` — `category_delete`
POST → `CategoryDeleteView` (:172). Guarded only by usage (a category in
use by display rows protects itself via FK).

## THE HONEST ABSENCES (the senior section)

- **No REST API / no versioning:** there are no external programmatic
  callers — a version contract with nobody is ceremony. The DAY an API
  exists, versioning + error contracts become real requirements (the G2
  project's checklist).
- **No idempotency keys:** nothing anonymous can WRITE yet. Order capture
  (G2) makes double-submit real — idempotency arrives WITH the first
  public write, not before.
- **No public forms at all:** the strongest validation is the absent
  input. *(Sabse mazboot deewar wo darwaza hai jo hai hi nahi.)*

## Learning Graph (this page)

**Before:** README Mental Model. **After:** [models.md](models.md)
(replica ownership) → [views.md](views.md) → the G2 REQ in README.
