---
id: end-to-end-business-audit-2026-07-05
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# End-to-End Business Audit — 2026-07-05 (pre-R10)

> Owner-ordered audit BEFORE R10 (Machines). Method: a complete REAL browser
> run on a fresh Adda (**3-PATTI-011**) with real users per role — no shell
> shortcuts for any business action; shell used only to inspect DB truth and
> to create the one missing DEV cast member (`dev.helper`, worker +
> `cutting_master_helper` skill). Nothing in app code was changed. Findings
> are recommendations only — implementation is owner-gated.

## 1) The business story, exactly as it ran

| # | Actor (role) | Action (browser) | System response — verified |
|---|---|---|---|
| 1 | Umesh (super admin) | Start Adda → 3 Patti | `3-PATTI-011` created; layering auto-started; **all 4 skill-holders auto-assigned** (F-2); A360 renders immediately (0/4, ₹0) |
| 2 | dev.manager (manager) | Layering tab → roster → dev.monthly only | Roster full-replace works; cancelled tasks kept (never deleted) |
| 3 | dev.manager | Attach roll CR-000004 (37", 12 kg) | Roll bound + logged in history |
| 4 | dev.monthly (worker, MONTHLY, phone 390px) | My Dashboard → "Report needed" → 12 layers → Submit & Complete | Contribution immutable ("Locked after submit"); **rate froze 0 / earning 0** (non-payable one-rule) |
| 5 | utest (cutting master) | Layering console → save draft (12 layers, leftover 0.5 kg, 2.5 m) → Complete | Stage complete, cost frozen **₹120** (12×₹10); Adda → Pattern Design; **worker hit post-complete 403** (F-3) |
| 6 | dev.manager | Pattern tab → assign dev.helper → Start | Panel shows **Layering — reference** snapshot: 12 layers · 2.50 m · colour-wise rolls · leftover — exact match to entered data |
| 7 | dev.helper (helper, phone) | Checklist report: 1-of-2 ticked → refused ("pending: Patti Panel"); both → Submit | ONE contribution qty=1; **₹500 frozen** (fixed = rate×1); console rows show "✓ Verified by Dev Helper" (single truth) |
| 8 | dev.helper | Complete Pattern | Guards fired in order: needs photo/video → needs sizes=100%; after photo + 60/40 proportions → complete, cost frozen **₹500**; lead-time stamped (4 min); post-complete 403 again (F-3) |
| 9 | utest + dev.monthly (phones) | Cutting reports: 60 Red-S1 / 45 Red-S2 | Both accepted with the S5 soft-warn (allocation enforcement OFF by design); totals correct |
| 10 | utest | Cutting console: breakup rows 24/36 + 18/27 → bundle S1 (60) + bundle S2 (45) → Complete | EST 105 = reported 105; cost frozen **₹10,500** (105×₹100); barcode batches generated; Adda → Barcode Generation |
| 11 | Umesh | Start Settlement → ADST-0002 → Finalize | Draft: utest ₹6,000 + helper ₹500 + **"Excluded — monthly-salary worker" with full why-text** (45 pc listed, no ₹); finalize freezes per-worker snapshot; "earnings booked" |
| 12 | everyone | Payroll / My Earnings / A360 / Costing / History | All six money surfaces agree (below) |

**One number, six surfaces — all agree (no drift):**
- Settlement draft/finalize: ₹6,500 (2 workers)
- Payroll Overview: utest ₹7,500 payable (6,000 + 1,500 unpaid from 009 — live ledger math), helper ₹500, monthly ₹0 + MONTHLY badge + "Salary →"
- utest My Earnings: Expected ₹0 → Pending ₹7,500, per-Adda drill-down (011: 60 pc ₹6,000)
- monthly My Earnings: "PAY BASIS MONTHLY SALARY — work is tracked; salary is paid separately"; pieces counted (production truth intact), ₹ suppressed everywhere
- A360: Expected ₹0 · Settled ₹6,500 · Std labor ₹11,000 · **Variance ₹4,500 = exactly the monthly worker's 45×₹100** (the honest ADR-0011 story)
- Costing page: std ₹11,120 · settled ₹6,500 · variance ₹4,620 — the ₹120 delta vs A360 is the **lens difference**: Costing = full manufacturing cost (incl. layering ₹120), A360 = payable labor (layering split out as "non-payable processing ₹120"). Both labeled, not drift.

History timeline: 16 events, every action attributed to the right person
(umesh create → manager roster/roll → utest/helper completes → umesh finalize).

## 2) Role matrix (browser-verified)

| Role (user) | Sees | Correctly blocked from |
|---|---|---|
| Super admin (umesh) | everything incl. Stage Rates, Admin section, override reason field on settlement | — |
| Manager (dev.manager) | Operations, Costing, Addas, Payroll suite, Factory Expenses, A360, stage consoles, settlement | Stage Rates button, Administration section, Product Patterns (per DB rules) |
| Cutting master (utest, piece-rate) | own dashboard/earnings, assigned stage consoles, completes stages | `/expense/payroll/` 403 · settlement detail 403 · unassigned stage panels 403 (assignment gate V2-1c-iv) |
| Helper (dev.helper) | pattern checklist + panel when assigned; Expected ₹500 → "becomes Earned when settled" | cutting console (no skill) — 403 |
| Monthly worker (dev.monthly) | own tasks, production counts | every ₹ expectation (badge instead); excluded from settlement funnel with printed reason |
| Accountant / listing_team | not exercised this run (no cast) — RBAC rules exist in Sidebar Access | n/a |
| "Admin Manager" | **role does not exist** (roles: super_admin, manager, worker, accountant, listing_team) — manager covers it | n/a |

Every role saw exactly what it should. No permission leak found in the run.

## 3) Snapshot / one-purpose verification

- Layering truth lives ONCE (`LayeringRollEntry` + contributions). Pattern panel's
  "Layering — reference", worker-dashboard digest ("12 layers · 2.50 m · 10 min ·
  30.00 m fabric"), Operations digest, and A360 all RENDER the same rows — no
  copies stored (handler `admin_snapshot` = render-only, R8 architecture).
- Pattern truth (verifications/photos/proportions) lives ONCE; cutting panel's
  "Pattern Design — reference" (2/2 · 100% · photos 1 · lead 4 min) reads it live.
- The only stored freezes are the DESIGNED ones: `processing_cost` at stage
  complete, `expected_*` at task complete, `AddaSettlementItem` + per-worker
  snapshot at finalize. Each has exactly one purpose. **No unnecessary duplication found.**

## 4) Admin visibility (§4) — answered by existing pages

Operations dashboard already answers: stalled (0), pending reports (1 = utest's
real unreported 010 assignment), active Addas (3) + in-progress-by-stage board,
pending payable ₹8,000, advance exposure ₹0, recent-Adda digests. Payroll
Overview answers pay questions; A360 answers per-Adda. Nothing new needed.

## 5) The two dashboards (investigated, NOT changed)

- `/inventory/dashboard/` and `/inventory/my-dashboard/` render the **same**
  template/context (`dashboard.py` — URL twins kept for bookmarks).
- The sidebar defines two "My Dashboard" MenuItems with either/or predicates
  (management → first URL, others → second). Managers/workers see ONE because
  DB SidebarItemRules govern them. **Super admin sees BOTH** because
  `build_menu_for` short-circuits `is_super_admin → allowed=True` before any
  predicate/rule runs ([permission_service.py:453](../config/accounts/services/permission_service.py)).
- So: the duplication is an unintended side-effect of the super-admin bypass,
  not a routing bug. Third "dashboard" = Operations (`/production/`) — a
  different page by design (factory ops vs personal).
- **Recommendation:** ONE "My Dashboard" MenuItem for everyone (single URL;
  keep the twin URL routable as a redirect for old bookmarks). Zero role logic
  needed. Optionally label Operations "Factory Operations" to kill the
  remaining ambiguity.

## 6) Company overview / central navigation (§6) — recommendation

Keep the two-tier model that already exists; don't build a mega-dashboard:
- **My Dashboard** = personal lens (everyone) — my tasks, my earnings pointer.
- **Operations** (`/production/`) = THE admin landing — it already has the
  factory KPIs. Add a small "jump strip" of links (Payroll · Settlements ·
  Costing · Factory Expenses · Raw Materials · A360-per-Adda) so admins can
  navigate without the sidebar; each stays a drill-down page. Machines (R10)
  becomes one more count-chip + link here.
- A360 stays the per-Adda drill-down; Payroll Overview the per-worker one.

## 7) Barcode (§7) — no hidden dependencies

Settlement ADST-0002 finalized **while Barcode Generation was still active** —
live proof money never waits on barcodes. Code census: barcode appears only in
its own stage service, tracking dashboards/exports (barcode features
themselves), and the shared reopen guard. Only the Adda's final
"completed" status waits for it. ✔

## 8) Findings (fix recommendations — owner-gated, nothing changed)

> **STATUS UPDATE (same day): F-1 · F-2 · F-3 · F-4 = ✅ FIXED** in the
> pre-R10 polish phase ([plan+receipt](PRE_R10_POLISH_EXECUTION_PLAN.md),
> gate 821, browser-proven on 3-PATTI-012). F-5…F-9 remain open backlog.

| # | Severity | Finding | Recommendation |
|---|---|---|---|
| F-1 | MED (super-admin only) | Two "My Dashboard" entries for super admin (bypass beats either/or predicates) | single MenuItem; keep twin URL as redirect |
| F-2 | MED | Adda start **auto-assigns every layering-skill holder** — incl. junk (`worker2`) and brand-new users; pollutes "who's working", A360 counts, pending-report KPIs | explicit assignment (PDD direction): start with empty roster + manager picks; or filter to active users at minimum |
| F-3 | MED (UX) | Worker-driven stage completion redirects into the NEXT stage's panel → **403 after success** (proven 3×: layering→pattern, pattern→cutting, cutting→barcode) | redirect non-management completers to the Adda page / their dashboard with the success flash |
| F-4 | MED | Cutting panel worker picker lists **all 17 users** (incl. deactivated, managers, super admin) while layering/pattern pickers are skill-filtered; pattern picker still lists **deactivated** dev.leaver | one shared picker: stage-skill holders ∩ active users |
| F-5 | LOW | Test residue visible on real surfaces: junk users (`worker2`, `verify-*`, `w1`, …) and junk stages (`verify`, `verify-86f27f0a`) on the Operations by-stage board | data cleanup pass before staging (owner already planned "clean all development data together") |
| F-6 | LOW | A360 per-stage cost rows reuse the word "unpaid" for two meanings (non-payable stage vs not-yet-settled) | label non-payable rows "non-payable" |
| F-7 | LOW | Phone cutting report offers ALL colours (service refuses non-layered ones at submit) | filter options to layered colours in the schema |
| F-8 | LOW | My Earnings "Today's / Recent Work — No work allocated yet" while an Expected amount exists (section reads settlement-allocation rows, not contributions) | rename to "Settled work" or feed from contributions |
| F-9 | INFO | Worker sidebar includes the whole Raw-Materials suite + Barcode dashboard (financially filtered but noisy) | trim via existing Sidebar Access rules — owner decision, tool already exists |
| F-10 | INFO | "Admin Manager" role doesn't exist; manager covers that seat | none (or add a role later if a distinct seat is needed) |
| F-11 | MED (UX, diagnosed 2026-07-05 post-polish) | Stage iframes show "localhost refused to connect" for stages the viewer can't open: dashboards/Adda page render an iframe per stage regardless of access; an unassigned/unskilled viewer gets 403 + `X-Frame-Options: DENY` (the sameorigin decorator never stamps an EXCEPTION response, so the middleware default wins) and Chrome paints XFO-blocked frames as "refused to connect". Live-proven: fetch as unassigned worker → `{status:403, xfo:"DENY"}`; helper dashboard 011 → only his assigned stage LOADS. Pre-existing mechanism; F-2 made it common (auto-assign used to mask it on layering) | root fix: render workspace accordions/iframes ONLY for stages the viewer can open (access+assignment filter in dashboard/adda contexts — also the minimum-info principle); optional belt: embedded-safe friendly 403 mini-page for the panel view. Owner-gated |

**No money bug, no permission leak, no calculation drift, no snapshot loss was
found.** Every finding above is navigation/roster/hygiene polish.

## 9) Verdict

The foundation tells one connected story: a roll becomes layers, layers become
verified patterns, patterns become counted pieces, pieces become a settlement,
a settlement becomes ledger truth, and every page (worker phone → manager
console → owner costing) reads the SAME numbers with role-appropriate lenses.
**Architecturally ready for R10.** Suggested (not blocking) pre-R10 quick wins:
F-3 redirect fix + F-4 shared picker + F-2 roster default — all small,
UI/service-local, and none touches money paths.

### Verification sources
Browser run 2026-07-05 14:16–14:41 IST on dev server (3-PATTI-011, ADST-0002),
DB inspections quoted in-session; roles: umesh29mar / dev.manager / utest /
dev.helper / dev.monthly. Confidence: High.
