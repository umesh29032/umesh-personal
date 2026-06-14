# Phase C — Navigation & UX

**Method:** analysis of the 68-page desktop crawl (text + screenshots) + sidebar/nav structure + terminology sweep over all rendered pages.
**Carve-out (per LOCKED foundation):** the **worker self-report** screen and the **stage-assignment/roster** screen are excluded — they will be redesigned by the production-truth foundation (S4/S5). Reviewed with the foundation, not here.

---

## Verdict
The UI is **consistent and well-built at the component level** (filters-in-cards, status badges, clear CTAs, good empty-state copy, clean terminology, dark mode). The weaknesses are **structural navigation/hierarchy**, not styling: the owner lands on a worker view, the core workflow is buried in the sidebar, and a few discoverability/label issues. No broken navigation; friction and hierarchy, not dead-ends.

---

## Findings

### MEDIUM

**C-1 — Owner/management lands on a worker-style "My Dashboard".** *information hierarchy* · confidence high (screenshot)
- Repro: log in as owner → land on `/inventory/dashboard/` titled "My Dashboard / Welcome", showing "Active Addas", **"No active tasks — When a manager assigns you to a Layering or Cutting stage, it'll appear here"**, and "My Earnings" in the sidebar.
- Problem: an owner/manager has no assigned tasks, so they see an empty worker widget. The real operational view (KPIs, in-progress-by-stage) exists at `/production/` but is **not the landing** — it takes a click to reach.
- Fix: role-based landing — owner/manager → the Adda/operational dashboard; worker → My Dashboard. Effort: **M**.

**C-2 — Core workflow (Production) is buried below Storefront in the sidebar.** *information hierarchy* · confidence high (screenshot)
- Sidebar order: Main → **Storefront** → **Raw Materials** → (Production/Tracking/Admin below the fold). The primary manufacturing flow (Addas/Production) sits beneath the secondary e-commerce module.
- Impact: the most-used section requires scrolling past less-used ones; new users misread the app's priorities.
- Fix: reorder — Production/Addas directly under Main; Storefront lower. Effort: **S** (section ordering).

**C-3 — Two identical "Dashboard" menu items.** *navigation / labels* · confidence high
- Under "Main" there are two entries both labeled **"Dashboard"** (`inventory:inventory_dashboard` + `inventory:user_dashboard` — both `SidebarItemRule.label = 'Dashboard'`). Indistinguishable.
- Fix: relabel — e.g. "Overview" (operational) vs "My Work"/"My Dashboard" (personal); or merge behind the role-based landing (C-1). Effort: **S**.

**C-4 — Management expense pages (Payroll, Settlements) not in the sidebar.** *discoverability* · confidence high (refines Phase-1 C5)
- Correction to Phase-1 C5: **My Earnings IS present** in the Main sidebar (template-level) — it is discoverable. But `expense:payroll-overview` and `expense:adda-settlement-list` have **no** `SidebarItemRule` and no visible menu entry → management reaches Payroll/Settlements only by typing the URL.
- Fix: add a Management/Finance sidebar section with Payroll + Settlements. Effort: **S**.

**C-5 — Inconsistent permission-denial UX** *(cross-ref Phase G)* — silent redirect vs bare unstyled "403"; nav-relevant because a denied click gives no consistent feedback. Effort: **S–M**. (Detailed in Phase G.)

### LOW

**C-6 — Completed Adda shows Current Stage "—".** The adda list shows an em-dash for a completed batch's stage instead of "Completed" / the final stage. Minor clarity. Effort: **S**.

**C-7 — No global Adda search / quick-jump.** To open an Adda you navigate the list + filter; no "jump to code" search. Fine at 2 Addas, friction at scale. Effort: **M** (defer until volume grows).

**C-8 — No explicit loading state on filter Apply.** Server-rendered full reload (acceptable), but a heavy filtered list gives no progress cue. Low priority given SSR. Effort: **S**.

### OK / WORKS-WELL

- **Terminology is clean:** zero `karigar` leak (rename applied), no Hindi/Hinglish leaking into UI copy, "Adda" used consistently across all 68 pages.
- **Empty-state copy is good:** "No active tasks — When a manager assigns you…" is helpful, not a blank.
- **Component consistency:** filters live inside cards (matches design rule), status color-badges (In Progress/Completed), clear primary CTAs ("Start Adda"), dark-mode toggle on every page.
- **Adda Dashboard is a real operational view:** KPI cards (In Progress / On Hold / Completed Today / All Completed) + **In-Progress by Stage** breakdown + date filter + Recent Addas. (Deeper KPIs → Phase H.)
- **Recent Activity timeline (27 events)** on the dashboard — good built-in audit visibility.
- **Mobile:** no horizontal overflow on any tested page (Phase-D detail).

---

## Phase C coverage / carve-outs
- **Carved out (redesign pending):** worker self-report screen, stage-assignment/roster screen — reviewed in the foundation's S4/S5 UI work.
- Deeper KPI/report gaps → **Phase H**. Permission-denial UX detail → **Phase G**. Mobile specifics → **Phase D**.

**Net Phase C:** styling is strong; the wins are structural — role-based landing (C-1), sidebar reordering + dedupe (C-2, C-3), and management-finance discoverability (C-4). All low-to-medium effort, none blocking.
