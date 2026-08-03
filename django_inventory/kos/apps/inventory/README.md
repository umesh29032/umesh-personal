---
id: app-inventory
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "I'm touching the UI shell, sidebar, dashboards, or the /tracking/ surface — what does inventory own and where do I go?"
related: [feature-rbac-access, project-system-map]
---

# inventory — the complete app map (the shell everything routes through)

> 📂 [Apps](../README.md) · [LOS home](../../README.md) — *andar:
> [URLs](urls.md) · [Views](views.md) · [Models](models.md) · [Services](services.md)*

## Mental Model — read this before anything

> **A library.** Books exist (domain apps' data). Readers exist (users).
> This app creates NO knowledge — it organizes ACCESS to it. The sidebar
> is the catalog; permissions decide which shelves you may see; the
> dashboards are the reading room's notice board; and the librarian's desk
> (middleware) checks every entry against the same catalog card that
> decided what you could see. *(Library gyaan nahi banati — raasta deti
> hai. Catalog hi guard hai.)*

## Common Misconceptions

- **"Inventory owns tracking."** Wrong — inventory owns the tracking
  SURFACE (views/URLs, P4.2); the tracking app owns the DATA (barcodes,
  history). Shelf vs books, again.
- **"Role and SidebarItemRule live here."** Not since 2026-06 — they moved
  to `accounts` (foundation); `inventory.models` is a 15-line re-export shim.
- **"Hiding a menu item is cosmetic."** It's a SECURITY act — the same row
  blocks the URL (middleware). There is no hide-without-block state.
- **"The middleware replaces view permissions."** Additive only — unmanaged
  URLs keep their mixins; the panel gate stacks on top.
- **"signals.py means this app uses signals."** It's a tombstone — the
  documented grave of the removed pattern (ADR-0001).

## Real Engineering Questions

**PM: "Hide the costing menu from managers."**
Chain: Sidebar Access editor → edit the `costing` rule row → menu hides AND
URL blocks in one act → verify BOTH effects (open the URL as a manager —
expect redirect+flash) → certification mindset: this was an access change,
note it. *One row, both walls — that's the whole app in one task.*

**PM: "Managers say the dashboard is slow on Mondays."**
→ [page-slow playbook](../../debugging/page-slow-or-erroring.md): count
queries first — dashboards are the classic template-N+1 breeding ground;
the fix ends with a count pin.

**PM: "Give the new supervisor role access to stalled-Addas."**
Think: is `stalled-addas` MANAGED (has a rule row)? → add role to the row →
unmanaged? then the view's mixin decides → and does the ROLE exist with the
right role-set membership (`accounts`)? Two systems, one answer path.

## Reading Strategy

- **Beginner:** Mental Model → [urls.md](urls.md) §my-dashboard + §scan →
  [request-through-stack](../../flows/request-through-stack.md).
- **Intermediate:** Start Here → [urls.md](urls.md) access-control sections
  → [views.md](views.md) middleware chapter.
- **Senior:** [services.md](services.md) (the trio + failure modes per
  piece) → [models.md](models.md) (the relocation story — an architecture
  lesson disguised as a shim) → Engineering Checklist.

## Start Here — common tasks

| Need to… | Go to |
|---|---|
| Add/edit a menu item (and its URL gate) | Sidebar Access page → `SidebarItemRule` — ONE row = menu + block ([services.md](services.md)) |
| Fix "menu visible but 403" / "hidden but reachable" | should be impossible — [middleware §pass-through](views.md) + [access playbook](../../debugging/access-denied-or-invisible.md) |
| Change base.html / shared CSS | **check [UI_COMPONENTS.md](../../../UI_COMPONENTS.md) FIRST** (canon + rule-of-3); page CSS scoped in `{% block extra_head %}` |
| Touch dashboards | [views.md](views.md) §dashboard — ONE live page (`my_dashboard`), two permanent redirects |
| Role CRUD / access matrices | [urls.md](urls.md) §roles + §hub (SA-only) |
| Barcode list/scan/exports (/tracking/) | [urls.md](urls.md) §tracking — inventory OWNS these views (P4.2) |
| Debug slow dashboard | [page-slow-or-erroring](../../debugging/page-slow-or-erroring.md) — template N+1 lane |

## Why a SEPARATE app (the senior question)

Every domain needs chrome, menus, and dashboards — putting them in ANY
domain app would make that app everyone's dependency. Inventory is the
**shell layer**: it depends on domains to RENDER them, while domains never
depend on it. The 2026-06 model relocation sharpened the line: decisions
(accounts) vs surfaces (here). It also absorbed the /tracking/ VIEWS
(P4.2) precisely to keep the tracking app dependency-clean — the shell
takes the coupling so data apps stay pure. Future: a redesign of the whole
UI = this app's problem alone.

## Technology Stack

| Layer | Used here | Learn it |
|---|---|---|
| Shell | `base.html` single-CSS-source canon · design tokens · FancySelect/data-fancy-date · DataTables patterns | [UI_COMPONENTS.md](../../../UI_COMPONENTS.md) (the certified canon) |
| Request plumbing | **middleware** (per-request gate) · **context processor** (per-render menu) | [services.md](services.md) · [request-through-stack](../../flows/request-through-stack.md) |
| Views | CBVs + shared mixins · function views for dashboards/scan | [views.md](views.md) |
| Data | reads everyone's aggregates (dashboards) — bulk queries, count-pinned mindset | [query-performance](../../concepts/postgresql/query-performance.md) |
| Testing | sidebar-order, error-handler, history-isolation suites | [testing-strategy](../../concepts/testing/testing-strategy.md) |

## Security

- **This app IS a security layer:** the sidebar pair (menu=gate, one row) + wall #4 (history strips for workers) — [rbac-access](../../features/rbac-access.md)
- Decisions delegated to `accounts.permission_service` — never made here
- **Threats defended:** hidden-but-reachable URLs (the pair) · privilege drift (read-only hub matrices for review) · redirect loops (exempt lanes)
- CSRF on all POSTs; scan endpoints JSON-aware 403s
- **Audit:** certifications treat this app's gates as the enforcement fabric — changes here = re-certification territory

## Required Knowledge — before working here

- [ ] Django: middleware lifecycle + context processors → [request-through-stack](../../flows/request-through-stack.md) · [settings](../../concepts/django/settings.md)
- [ ] The three-concept access model (role/skill/sidebar) → [people-and-roles](../../project/people-and-roles.md)
- [ ] The pair + ONE-predicate laws → [rbac-access](../../features/rbac-access.md)
- [ ] UI canon + rules 9/10/11 → [UI_COMPONENTS.md](../../../UI_COMPONENTS.md) · [tech-stack](../../project/tech-stack.md)
- [ ] DSA shape here: set algebra evaluated in bulk → [rbac-access §DSA](../../features/rbac-access.md)

## Learning Graph

**Before:** [system-map](../../project/system-map.md) →
[people-and-roles](../../project/people-and-roles.md) →
[rbac-access](../../features/rbac-access.md).
**After:** [access playbook](../../debugging/access-denied-or-invisible.md)
→ [auth-hardening](../../concepts/security/auth-hardening.md) → then
[apps/production](../production/README.md) (the surfaces this shell hosts).

## What this app owns

The **cross-domain shell**: role-aware dashboards · the Access-Control
admin surfaces (role editor, Sidebar Access editor, read-only hub matrices)
· `SidebarAccessMiddleware` (menu-hidden ⇒ URL-blocked, the PAIR) · the
sidebar context processor · base.html + the certified component canon ·
**the whole `/tracking/` surface** (barcode dashboard/list/print/scan,
history timelines, manifest-tracked exports — views live HERE so the
tracking app imports no production; P4.2 D1).

## What it does NOT own

`Role` + `SidebarItemRule` MODELS — relocated to `accounts` (2026-06);
`inventory.models` is a re-export shim so old imports still work ·
permission DECISIONS (`accounts.permission_service` — middleware calls
`can_access_url_name`) · barcode DATA (`tracking.BarcodeBatch/BatchBarcode`
+ history models — inventory renders them) · any business domain.

## Where requests enter — 10 + 13 URLs, 2 mounts

| Mount | Routes | Who |
|---|---|---|
| `/inventory/` | 3 dashboard (1 live + 2 redirects) · styleguide · 4 role CRUD · sidebar-access · access hub | dashboards: all · rest: SA-only |
| `/tracking/` (namespace `tracking:`, owned here) | dashboard · barcode list/print/export-csv · scan + scan-status · roll/adda history · 5 export routes | management (exports: manager+) |

## The census

- **URLs:** 10 (`config/inventory/urls.py`) + 13 (`config/inventory/tracking_urls.py`)
- **Views:** 8 modules in `config/inventory/views/` (~21 classes + dashboard functions) — [views.md](views.md)
- **Models:** re-export shim only (15 lines) — [models.md](models.md)
- **Services:** `sidebar_service` (+ middleware + context processor as the runtime trio) — [services.md](services.md)
- **Tests:** app-root files: sidebar order, error handlers, auth history isolation, R1 broadcast
- **Also owned:** `signals.py` = a TOMBSTONE documenting why signals were removed (ADR-0001) — never revive it

## The laws to carry in

1. **The pair is sacred:** a menu rule IS a URL gate — never add a menu
   item without its rule, never gate a URL two different ways.
2. **Middleware is additive:** unmanaged URLs keep their view mixins;
   the panel gate only ADDS on managed ones. Dashboards are exempt
   (redirect-loop prevention) — don't "fix" that.
3. **UI canon:** compose from UI_COMPONENTS.md; new shared CSS only at 3+
   occurrences (rule 9/10); ALL selects = FancySelect (standing rule).
4. Exports refuse until barcode-gen stage completes (service-gated).

## Engineering Checklist — pre-flight before ANY change here

- [ ] New URL anywhere in the PROJECT? It needs a SidebarItemRule decision (managed or consciously unmanaged-with-mixin)
- [ ] Menu change = access change — treat Sidebar Access edits as security edits
- [ ] Middleware edit? Re-test: exempt dashboards (no loops) · JSON requests · unmanaged pass-through · SA bypass
- [ ] Template/CSS: canon check → rule-of-3 → page-scoped block → mobile+tablet+desktop verified (rule 11) → **restart runserver** (template cache lesson)
- [ ] Dashboard queries: count-pinned mindset — bulk aggregates, no per-row template calls
- [ ] Tracking exports: manifest rows are history — re-download, never regenerate silently
- [ ] kos-sync + docs-sync same session

## Change Impact — touching this app affects

- **EVERY page's chrome** (base.html/sidebar = global blast radius)
- **Access enforcement everywhere** (middleware runs on every request)
- **All roles' navigation** (rules drive menus for every user)
- Worker phone experience (dashboards are their landing) · sidebar-order + error-handler tests · certification matrices assumptions ([rbac-access](../../features/rbac-access.md))

## Learn it / debug it

WHY: [rbac-access](../../features/rbac-access.md) · [people-and-roles](../../project/people-and-roles.md)
· [system-map](../../project/system-map.md) (the click-path) · broken:
[access playbook](../../debugging/access-denied-or-invisible.md) ·
UI canon: [UI_COMPONENTS.md](../../../UI_COMPONENTS.md) · docs: [RBAC.md](../../../docs/production/RBAC.md)
