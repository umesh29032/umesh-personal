---
id: app-inventory-urls
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Any /inventory/ or /tracking/ URL — its own full learning story."
related: [app-inventory]
---

# inventory — URL Learning Pages (10 + 13, each individually)

> 📂 [inventory app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)
> Sources: `config/inventory/urls.py` (app_name=`inventory`) +
> `config/inventory/tracking_urls.py` (app_name=`tracking` — P4.2: views
> owned here, namespace preserved so templates never changed).

**Reading Strategy** — *Beginner:* §1 (my-dashboard) → §12 (scan) →
README's Mental Model. *Intermediate:* §5–§7 (the access surfaces) →
§9–§16 (the tracking surface). *Senior:* §6 (the pair editor — a security
control disguised as a settings page) → the middleware chapter in
[views.md](views.md).

---

## `/inventory/` mount

### 1. `my-dashboard/` — `my_dashboard`
**Purpose:** THE landing page, role-aware — a worker sees active stages +
report badges; management sees the ops summary. **Why:** every user needs
ONE home; role-aware beats role-separate (no duplicate pages to drift).
**Method:** GET → `user_dashboard` (function, `views/dashboard.py:281`).
**Why a fresh url_name (learn from history):** F-1 polish — the old names
carried legacy SidebarItemRule rows that hid the menu for some roles; a
fresh name = no legacy row = renders for everyone. Naming AS a migration tool.
**Reads:** bulk badge/state queries. **Writes/locks:** none.
**Middleware note:** EXEMPT (landing page — loop prevention).
**Tests:** dashboard + sidebar-order suites. **Why simple:** composition of
other apps' aggregates; correctness borrowed, not created.

### 2. `dashboard/` — `inventory_dashboard`
**Purpose:** permanent redirect for the oldest bookmark generation → §1.
**Method:** GET → `dashboard_redirect` (`views/dashboard.py:296`). Middleware-exempt.
**Why it exists forever:** bookmarks are contracts (production's pattern
redirects, same lesson). **Why simple:** one redirect — simplicity IS the feature.

### 3. `my-dashboard/legacy/` — `user_dashboard`
**Purpose:** permanent redirect carrying the SECOND historical url_name → §1.
**Method:** GET → same `dashboard_redirect`. Middleware-exempt.
**Why a second one:** two eras of bookmarks existed; each old NAME needs its
own route so `reverse()` in any surviving template keeps working. Learn from
the pair: renames accumulate redirects — cheap, honest, permanent.

### 4. `styleguide/` — `styleguide`
**Purpose:** the living component gallery — the certified design system,
rendered. **Why:** UI canon needs a place you can SEE, not just read
(UI_COMPONENTS.md's visual twin).
**Method:** GET → login-wrapped `TemplateView` (no business logic).
**Deliberately UNMANAGED** (no rule row — any authed user): learning
surface, not an operational one. **Why simple:** static template by design.

*The role editor — four routes, shared context first: Role rows = RBAC
source of truth (model in `accounts` — [models.md](models.md)); ALL SA-only
because a role edit changes what EVERY holder can do (blast radius = the org).*

### 5a. `roles/` — `role_list`
GET → `RoleListView` (`views/role_views.py:14`). The curated list. **Why
simple:** read over foundation rows; the power is in who may reach it.

### 5b. `roles/add/` — `role_add`
GET+POST → `RoleCreateView` (:24). New role = new capability bundle —
pair it with sidebar rules (§6) or it exists but sees nothing (a common
real question — README's supervisor example).

### 5c. `roles/<pk>/edit/` — `role_edit`
GET+POST → `RoleUpdateView` (:40). Edits propagate to every holder on
next request — no caching of decisions anywhere (deliberate).

### 5d. `roles/<pk>/delete/` — `role_delete`
POST → `RoleDeleteView` (:58). **Guarded:** roles in use PROTECT
themselves — reassign holders first. Learn from the refusal: identity
anchors never vanish from under their references.

### 6. `sidebar-access/` — `sidebar-access` ⭐ THE PAIR EDITOR
**Purpose:** edit `SidebarItemRule` rows — which roles/skills SEE each menu
item AND may HIT its URL. One row, both effects.
**Why it exists:** menu-vs-gate drift is the classic access bug class; this
page makes the drift unrepresentable.
**Method:** GET+POST → `SidebarAccessListView` (`views/sidebar_access_views.py`,
`_SuperAdminOnly`). **Service:** `sidebar_service.save_sidebar_rules`
(atomic, validates assignment shape).
```
Journey: POST → SA gate → save_sidebar_rules [@atomic]
→ SidebarItemRule rows (accounts) → NEXT request: every user's menu
(context processor) AND every managed URL's gate (middleware) reflect it
```
**Failure modes:** malformed assignments (loud). **Security framing:** this
is a SECURITY CONSOLE wearing a settings-page costume — treat every save
as an access-control change.
**Tests:** `test_sidebar_order.py` + middleware suites.
**Required knowledge:** [rbac-access](../../features/rbac-access.md) FIRST.

### 7. `access/` — `access-control`
**Purpose:** the read-only RBAC hub — who-sees-what matrices per role/skill.
**Why:** reviewing access should be one screen, not archaeology.
**Method:** GET → `AccessControlHubView` (SA). **Why simple/read-only BY
DESIGN:** a review surface that could EDIT would become a second pair-editor
— one console (§6) keeps writes funneled.

---

## `/tracking/` mount (inventory-owned views, `tracking:` namespace)

### 8. `/tracking/` — `dashboard`
**Purpose:** the piece-scan overview board. **Method:** GET →
`BarcodeDashboardView` (`views/tracking_dashboard.py`). Read-only aggregates
over tracking data. **Why here (P4.2 lesson):** the VIEW lives in inventory
so the tracking app imports no production — the shell takes the coupling.

### 9. `barcodes/<adda_code>/` — `barcode-list`
**Purpose:** one Adda's barcode ranges + piece states. **Method:** GET →
`BarcodeListForAddaView` (`views/tracking_barcodes.py`). Reads
`BarcodeBatch` ranges (+ lazy `BatchBarcode` states). **Misconception
guard:** ranges ≠ per-piece rows — pieces materialize on first scan
(storage win — born in [production Part 4](../production/urls-cutting-barcode.md)).

### 10. `barcodes/<adda_code>/print/` — `barcode-print`
**Purpose:** the printable label sheet. **Method:** GET (print-layout
template). **The permanence edge:** once these leave the printer, payloads
are FOREVER (ADR-0010) — printing is the real commit; the page is honest
about that.

### 11. `barcodes/<adda_code>/export/` — `barcode-export`
**Purpose:** quick CSV of an Adda's codes. **Method:** GET →
`barcode_export_csv` (function). **Why simple vs §13-16:** ad-hoc pull;
the manifest-tracked export SYSTEM (below) exists for the audited flavors.

### 12. `scan/<value>/` — `scan` ⭐
**Purpose:** resolve a scanned value to ITS piece — identity (adda, seq),
current status, context. **Why:** the floor's fastest question: "yeh piece
kaun hai?"
**Method:** GET → `scan_piece` (function — phone-first, JSON-aware).
**Service:** `tracking.services.barcode_service`: range lookup; **lazy-creates
the `BatchBarcode` row on FIRST touch** (untouched pieces cost no storage).
**Failure modes:** unknown value → clean not-found (never a 500 on a
mis-scan). **DSA:** create-on-demand materialization.
**Why a function, not a CBV:** minimal surface for device-speed endpoints.

### 13. `scan/<value>/status/` — `scan-status` ⭐
**Purpose:** transition the piece: pending→packed→dispatched.
**Method:** POST → `update_piece_status`.
```
Journey: POST → resolve piece → transition [@atomic, FSM-guarded]
→ history append → JSON/redirect
```
**Failure modes:** illegal transition (the FSM refuses — dispatched never
returns to pending). **The lesson:** even a two-hop lifecycle deserves FSM
discipline; booleans would drift ([stage-tracking §DSA](../../features/stage-tracking.md)).
**Required knowledge:** FSM mindset + append-only history.

### 14. `history/roll/<roll_pk>/` — `roll-history`
**Purpose:** one cloth roll's whole life — arrival, attachments, leftovers.
**Method:** GET → `RollHistoryView` (`views/tracking_history.py`).
Read-only over `ClothRollHistory` (append-only, history_service-written).
**Why simple:** timelines render; they never interpret.

### 15. `history/adda/<adda_code>/` — `adda-history`
**Purpose:** one Adda's whole life — stages, settlements, overrides.
**Method:** GET → `AddaHistoryView`. **The wall-#4 edge lives HERE:**
financial CHANGE rows are STRIPPED for workers — audience-scoped truth,
certified (`test_g_auth_1_history_isolation.py`). Never "simplify" the
strip away.

### 16. `exports/` — `export-list`
**Purpose:** the manifest — every export ever made, re-downloadable.
**Method:** GET → `ExportListView` (`views/tracking_exports.py`,
ManagerOrAdmin). **Why a manifest:** an export you can't re-produce
byte-identically is a dispute waiting; rows are history.

*Export triggers — shared spine first: all three subclass
`_BaseExportTriggerView` (new format = subclass, never fork); all POST,
ManagerOrAdmin; all **refuse until barcode-generation completes** (exporting
identities that don't exist would mint fiction); each writes the artifact +
its manifest row. Why three URLs, not one `?format=` param: independently
menu-gated + independently searchable — the codebase applied the LOS's own
discoverability argument before the LOS existed.*

### 17. `exports/<adda_code>/csv/` — `export-csv`
POST → `ExportCSVView` (:69). The spreadsheet-friendly flavor — flat rows.

### 18. `exports/<adda_code>/xlsx/` — `export-xlsx`
POST → `ExportXLSXView` (:73). Formatted workbook — the office-facing flavor.

### 19. `exports/<adda_code>/pdf/` — `export-pdf`
POST → `ExportPDFView` (:77). Print/sign flavor — the one that leaves the
building; the manifest row matters most here.

### 20. `exports/<export_code>/download/` — `export-download`
**Purpose:** re-download a PAST export by its code. **Method:** GET
(ManagerOrAdmin). **The lesson:** re-download beats regenerate — the
manifest row IS the promise that bytes stay stable.

---

## Learning Graph (this page)

**Before:** README (Mental Model — the library). **After:**
[views.md](views.md) (middleware chapter!) → [services.md](services.md)
(the trio) → then [apps/production Part 4](../production/urls-cutting-barcode.md)
(where the barcodes were born).

## Direct paths

`config/inventory/urls.py` · `tracking_urls.py` · `views/` ·
`middleware.py` · `services/sidebar_service.py` · `context_processors.py` ·
`templates/base.html` · rule model: `config/accounts/models.py`
