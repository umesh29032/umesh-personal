> **ARCHIVED 2026-07-13** — 2026-06 production-readiness audit phase; findings closed, superseded by the current frozen architecture ([../../MANUFACTURING_V1_FREEZE.md](../../MANUFACTURING_V1_FREEZE.md)). Kept for history (Phase-7 DOCCLEAN-D). Its own outbound links reflect the 2026-06 tree.

# Phase D — Mobile UX Audit

**Method:** 12 mobile screenshots @375×812 (worker + management screens) with horizontal-overflow checks + numeric-input attribute audit across templates + live hamburger probe.
**Carve-out (LOCKED foundation):** worker **self-report** screen + **stage-assignment** screen excluded (redesigned under S4/S5).
**Assumption (owner rule 11):** most workers use phones → mobile is a functional requirement, not polish.

---

## Verdict
**Mobile is genuinely strong — well above typical Django apps.** Zero horizontal overflow on any of 12 pages; every table-heavy screen uses a mobile-correct pattern (stacked label:value cards or a vertical timeline, never a squished table); numeric inputs trigger the right keypad; the sidebar collapses behind a hamburger. Real issues are **minor and few**: text-link tap targets, one matrix, and the long drawer compounding the Phase-C sidebar order.

---

## Findings

### MEDIUM

**D-1 — Action affordances are text links, not buttons → small tap targets.** *touch targets* · confidence high (screenshots)
- Evidence: Payroll cards expose **"Settle"** (a money action) and the worker name as **orange text links**; Costing/Access panels use **"Edit →"** text links. On a 375px screen these are below the ~44px touch-target guidance.
- Impact: mis-taps on factory floor (gloved/quick hands), especially for the money action "Settle".
- Fix: render primary per-card actions ("Settle", "Record Advance" already a button — match it) as ≥44px buttons; keep name as a link. Effort: **S**.

### LOW

**D-2 — Access-hub "Roles × Pages" matrix doesn't stack on mobile.** *table responsiveness* · confidence high
- The access-control hub is mostly stacked cards (good), but the Roles×Pages grid is a true matrix — matrices don't reflow to narrow screens.
- Impact: low — Access Control is an admin/desktop-primary tool. Fix: a mobile-collapsed view (per-role list) or an explicit "best viewed on desktop" affordance. Effort: **M**.

**D-3 — Long sidebar drawer compounds the Phase-C ordering on mobile.** *mobile navigation* · confidence med
- The mobile drawer holds the full sidebar (Main → Storefront → Raw Materials → Production → Tracking → Admin). Because Production sits below Storefront + Raw Materials (Phase-C C-2), on a phone the **core workflow is several scrolls down** the drawer — worse on mobile than desktop.
- Fix: the C-2 reorder (Production under Main) benefits mobile most; consider a condensed mobile drawer (collapsible sections). Effort: **S** (rides on C-2).

**D-4 — Mobile drawer open-state not re-verified this session.** *coverage note*
- The hamburger toggle is confirmed present and the sidebar is collapsed by default on every mobile shot (correct pattern), but the drawer **open** state couldn't be captured this session (auth/rate-limit). Recommend a 1-minute manual confirm: drawer opens, is scrollable, closes on outside-tap/Esc, and doesn't trap focus. Effort: **S** (verification, not a known defect).

### OK / WORKS-WELL (strong mobile, keep)

- **No horizontal overflow** on any of 12 tested pages @375px.
- **Table-heavy pages use mobile-correct patterns:** Costing → stacked cards; Payroll → per-worker cards; Access → concept cards; Adda History → vertical timeline. No squished tables anywhere.
- **Numeric entry done right:** `type="number"` + `inputmode="numeric"` (counts) / `inputmode="decimal"` (money) with `min`/`max`/`step` (14 templates type=number, 17 inputmode) — settlement variance, advance-recovery, bulk-roll all trigger the correct keypad.
- **My Earnings** (worker phone view) is a clean card dashboard — Pending Payable / Earned / Expected / Advance / This Month / Paid, plus stage-wise + by-Adda + settlement history. Worker-first done well.
- **Settlement detail** packs dense financials (chain, expected/packed/missing/variance, per-worker snapshot) into readable mobile cards.
- **Blocked-stage states** are clear with a recovery button ("Cutting stage not yet reached. Complete Layering first." + Back).
- **Dark-mode toggle** on mobile; hero strips + cards scale cleanly.

---

## Factory-floor usability assessment
- **Worker phone experience (My Earnings + dashboards):** strong — big readable numbers, card layout, correct keypads, expectation-setting copy ("not final pay").
- **Productivity bottlenecks found:** small text-link actions (D-1) and the deep-drawer nav to reach work (D-3). Both low-effort.
- **The real worker-floor screen — self-report (count entry) — is carved out** and will be (re)designed mobile-first under the foundation (S5); its numeric-entry quality must match the rest (type=number + inputmode, big targets, no cap leakage).

---

## Phase D coverage / carve-outs
- Carved out: worker self-report + stage-assignment screens (foundation S4/S5 — design mobile-first there).
- Not re-verified live this session (auth): drawer open-state (D-4).

**Net Phase D:** mobile is a strength, not a risk. Only D-1 (tap-target buttons) is worth doing before staging; D-2/D-3/D-4 are low-priority or ride on C-2. The foundation's S5 worker-report screen is where mobile-first effort must concentrate next.
