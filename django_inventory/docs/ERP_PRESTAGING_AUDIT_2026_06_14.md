# ERP Pre-Staging Product Audit — Phase 1 Report

**Date:** 2026-06-14 · **Branch:** new_flask_app · **Method:** live headless-browser dogfooding (4 personas) + DB ground-truth reconciliation + targeted code reads. Evidence-first, no fixes applied.

> Coverage note: this report is built from **first-hand browser + DB evidence I gathered directly**. A deeper 9-phase parallel code-analysis pass was launched but **halted on an account session/usage limit (HTTP 429, resets ~01:30 IST)** before it could add its layer. Phases marked ⚠️ below are partially covered and flagged for a follow-up code pass. The financial phase (B) and access phase (G) are complete and first-hand.

---

## 1. Ship-readiness verdict

**CONDITIONAL — not ready for an unsupervised worker rollout yet; close to ready for a supervised owner/manager pilot.**

The money engine is sound: I reconciled a real 3-version settlement supersede chain to the rupee (no money created or lost across two reversals), and the settlement UI surfaces variance honestly. Core management flows render cleanly on desktop and mobile. **But three things block a clean staging:** (1) a plain worker account is authenticated yet has **zero reachable pages** — including their own earnings; (2) a real **GET request crashes with HTTP 500** on the settlement-start URL; (3) **unverified work is paid at the worker's self-reported quantity**, and the **frozen Adda processing-cost doesn't equal what workers actually got paid** — both are financial-trust issues an owner must consciously accept or gate before relying on the numbers.

**Top 3 blockers:** F1 worker-zero-access · A1 settlement-start 500 · B1 unverified→paid-at-self-report (with B2 cost/payout divergence).

---

## 2. Answers to the owner's 6 questions

1. **Ready for staging?** Conditional. Owner/manager pilot: yes, with eyes open. Worker self-service: no, until F1 (worker access) + nav (C1) are fixed.
2. **What confuses a worker?** A freshly-created worker logs in and lands on a page that looks logged-out, with no menu and no link to "My Earnings" (the expense app isn't in the sidebar at all). And "My Earnings" shows **80 pieces produced** but pays for **75** — no explanation of the gap.
3. **What frustrates an owner?** Cost accounting and payroll disagree (₹315 frozen vs ₹360 paid for the same cutting stage); there's no operational dashboard (WIP-by-stage, throughput, advance exposure, pending-settlement aging); permission denials are inconsistent (silent redirect vs a bare unstyled "403").
4. **Financial risks?** Real but bounded. Unverified work is trusted at face value (over-report risk). Cost-vs-payroll divergence means product costing understates true labour. The reversal/supersede ledger itself is **correct** (verified). DEBUG=True would leak tracebacks if it reached staging.
5. **Assignment-model gaps?** There is **no worker-facing "my assigned tasks / my queue" view** and no manager assignment-monitoring dashboard. Today work is discovered by navigating to an Adda, not pushed to a worker. This won't scale to TM-1 / Missing-Pieces / Alter / G1-G7 / stitching-finishing-packing without an explicit assignment+queue layer. ⚠️
6. **Fix before TM-1?** F1 (worker access + queue), A1 (500), B1/B2 (verification gate + cost-truth reconcile), C1 (expense in sidebar). See §6.

---

## 3. Findings by severity

Format: **ID** — title · *area* · repro → expected vs actual · root cause · fix · effort.

### HIGH

**A1 — `GET /expense/settlements/start/<pk>/` returns HTTP 500.** *workflow / robustness*
- Repro: as owner/manager open `http://127.0.0.1:8000/expense/settlements/start/2/` (bookmark, refresh, back-button, or shared link).
- Expected: render or redirect (the normal path is a POST from the settlements list). Actual: **500** — `ImproperlyConfigured: TemplateResponseMixin requires 'template_name' or get_template_names()`.
- Root cause: `AddaSettlementStartView(TemplateView)` defines only `post()`, no `template_name` → any GET falls through to `TemplateView.get()` and crashes. [config/expense/views.py:301](config/expense/views.py#L301). (Contrast: `cutting-start` correctly returns 405 on GET.)
- Fix: subclass `View` (not `TemplateView`), or add a `get()` that redirects to the settlement list / 405. Effort: **S**.

**F1 — A plain Worker is authenticated but has zero reachable pages.** *permissions / onboarding*
- Repro: log in as `worker3@test.local` (role=Worker, no skill, no WorkerProfile, no sidebar grants). Lands on `/app/` with no logout link, no sidebar. Every URL — including own `/expense/my/` — redirects to `/app/?next=…`.
- Expected: a worker can at minimum see their own work + earnings. Actual: trapped; authorization denial is rendered as a **login-style `?next=` redirect**, indistinguishable from being logged out.
- Root cause: access is gated entirely by `SidebarItemRule` + skills; a worker with no grants matches nothing, and denial routes to `LOGIN_URL=/app/`. [config/config/settings/base.py:282](config/config/settings/base.py#L282); SidebarAccessMiddleware. The expense app has **no** sidebar rule at all (see C1).
- Fix: every Worker should have a default landing (My Dashboard) + My Earnings; denial for an *authenticated* user should be a 403 page with explanation, not a login redirect. Effort: **M**.

**B1 — Unverified contributions are paid at the worker's self-reported quantity.** *financial control*
- Repro: contrib#10 (utest, Cutting): reported=60, **verified=None** → billed 60×₹3 = **₹180**. contrib#11: reported=20, verified=15 → billed 15×₹3 = ₹45. One worker, one settlement, two lines — one paid on self-report, one on verified.
- Expected (owner's mental model): verification gates payment. Actual: rule is `qty = verified_quantity if not None else reported_quantity` — **absence of verification = full trust in the worker's number**. [config/expense/views.py:341](config/expense/views.py#L341) (`_line_dict`); same rule in the earning/settlement path.
- Risk: a worker over-reports, no one verifies, they're paid in full. Fix: decide policy — either block finalize while any contribution is unverified, or make "unverified → pay reported" an explicit, visible toggle per stage. Effort: **M** (policy + guard).

**B2 — Frozen Adda processing-cost ≠ actual settled payout for the same stage.** *costing accuracy* · confidence: medium (data confirmed; freeze-timing root cause not yet code-traced)
- Repro (adda 3-PATTI-001, Cutting stage): `AddaStageRecord` SR#4 `processing_cost` = **₹315.00**. Actual settled cutting payout = worker2 ₹135 + utest (₹180+₹45) = **₹360.00**. Gap **₹45** = exactly contrib#11.
- Expected: the Adda's frozen cost of processing equals what was paid to process it. Actual: they diverge by ₹45 — product costing understates labour.
- Root-cause hypothesis: `processing_cost` froze before contrib#11 (utest's second cutting line) was added, and isn't recomputed. Needs confirmation in the costing-freeze service (ADR-0009 cost-truth). Fix: reconcile freeze event vs contribution-add, or recompute/version processing_cost at settlement. Effort: **M–L**.

### MEDIUM

**C1 — The entire `expense` app is missing from the sidebar.** *navigation*
- `SidebarItemRule` has 20 rows (inventory/production/raw-materials/storefront/tracking/admin) and **none** for `expense:my-earnings`, `payroll-overview`, or `adda-settlement-list`. Workers and managers can only reach earnings/settlements by typing the URL. Verified via DB. Fix: add expense sidebar rules (My Earnings for workers; Payroll/Settlements for management). Effort: **S**.

**C2 — Inconsistent permission-denial UX + bare unstyled 403.** *permissions / UX*
- Manager probe: some restricted routes **silently redirect** to the dashboard (access, roles, sidebar-access, users, stages, storefront) with no message; others return a **bare Django "403 Forbidden"** (user-types, products/add, stages/add, rolls/bulk-add) with no app shell/nav. No `handler403` is registered. Verified via probe matrix + screenshot. Fix: one consistent, branded 403 (or sidebar-consistent redirect-with-message). Effort: **S–M**.

**B3 — "Pieces produced" doesn't match the paid basis on My Earnings.** *worker clarity / financial*
- My Earnings (utest) shows **80 PIECES PRODUCED** (reported 60+20) but **₹225 earned** = 75 pieces (60 unverified + 15 verified). Worker sees 80 made, paid for 75, no explanation. Fix: show verified vs reported, or label the basis. Effort: **S**.

### LOW

**E1 — Unapplied migration locally:** `tracking 0014_alter_addahistory_change_type` is pending in the dev DB (139 applied, 1 not). Confirm it's intended/applied before staging. Effort: **S**. ⚠️ docs/data-drift.
**I1 — `GET /production/addas/3-PATTI-002/report/cutting/` → 404.** Worker-report route 404s (stage not reached / worker not assigned for that adda+stage). Confirm it's an intentional guard, not a dead link, and return a friendly "not your task" page. Effort: **S**. ⚠️
**S1 — DEBUG=True** locally exposes full tracebacks (that's how A1's stack was read). Ensure staging runs `config.settings.production` with DEBUG off. Effort: **S** (deploy config).

### INFO / WORKS-WELL (confirm-intended)

- **OK — Money reconciles exactly.** utest net ledger = 690 credit − 465 debit = **₹225 = finalized `final_payable`**, across two reversals; reversed SWAs voided, offsetting ledger entries link via `reverses`. No money created or lost. (Worked example in §4.)
- **OK — Settlement detail UI is strong:** correction chain, EXPECTED/PACKED/MISSING/REJECTED/VARIANCE(ABSORBED), per-worker frozen snapshot, "Settled by … Replaces …" audit line.
- **OK — Mobile baseline is clean:** no horizontal overflow at 375px on 12 tested pages; My Earnings and settlement-detail are well-built card layouts; blocked-stage states are clear ("Cutting stage not yet reached. Complete Layering first.").
- **OK — Security primitives work:** login is rate-limited per IP+email (it actually throttled me mid-audit); logout is POST-only by design.
- **Confirm — Manager has full financial access** (settlements, advances, worker-settle, payroll) and **reaches the cutting workspace without the cutting_master skill** — verify the stage skill-gate is meant to be bypassed for management roles.
- **Confirm — Accountant and Listing-Team roles are defined but no users exist** — provisioning gap if those teams are expected at staging.
- **WorkerLedgerEntry.settlement FK is always null** — settlement linkage is only transitive (entry→assignment→adda_settlement); reversal entries link only via `reverses`. A direct "ledger for settlement X" query isn't possible — minor auditability gap.

---

## 4. Phase B — Financial deep-dive (worked examples)

**Setup:** adda 3-PATTI-001 (3 Patti), cutting rate ₹3/piece. Rule: `qty = verified ?? reported`.

**Contributions (production truth):**
| # | worker | stage | reported | verified | billed qty | × ₹3 |
|---|--------|-------|---------|---------|-----------|------|
| 9 | worker2 | Cutting | 50 | 45 | 45 | ₹135 |
| 4 | worker2 | Layering | 25 | — | 0 (rate 0) | ₹0 |
| 10 | utest | Cutting | 60 | **none** | **60** | ₹180 |
| 11 | utest | Cutting | 20 | 15 | 15 | ₹45 |

**Supersede chain (worker utest):**
- ADST-0001 (superseded): expected ₹240 (SWA#2 60×3=180 + SWA#3 20×3=60). Ledger +180, +60. → reversed: SWAs voided, ledger −180, −60.
- ADST-0002 (superseded): expected ₹225 (SWA#4 180 + SWA#5 15×3=45). Ledger +180, +45. → reversed: −180, −45.
- ADST-0003 (**finalized**): expected ₹225 (SWA#6 180 + SWA#7 45). Ledger +180, +45.

**Net ledger utest** = credits (180+60+180+45+180+45 = **690**) − debits (60+180+45+180 = **465**) = **₹225** = ADST-0003 `final_payable`. ✓ **Reconciles. No double-impact, no leakage across two reversals.**

**Variance:** ADST-0003 EXPECTED 75 pieces, PACKED 73, MISSING 2, VARIANCE **₹0.00 (ABSORBED)** → worker paid full expected; the 2 missing are absorbed by management. *Self-corrected:* my initial "73≠75 silently lost" was **wrong** — the UI shows it explicitly. (See §5.)

**Two real issues from these numbers:** B1 (the ₹180 line is paid on an **unverified** 60) and B2 (Adda frozen cutting cost ₹315 ≠ total cutting payout ₹360).

---

## 5. Refuted / withdrawn claims (audit self-correction)

- ❌ **"packed 73 ≠ billed 75, 2 pieces silently lost."** Refuted by the settlement-detail screen, which explicitly shows **MISSING 2 + VARIANCE ABSORBED ₹0.00**. It's a deliberate, visible *absorb* policy, not a silent gap. Downgraded to "confirm absorb-is-intended-default" (info).
- ❌ **"GET logout is a no-op bug."** Refuted — `LogoutView` is **POST-only by design** ([config/accounts/urls.py:42](config/accounts/urls.py#L42)); my crawler used GET. Correct behavior.
- ❌ **"My Earnings renders blank."** Refuted — page renders fully (1008 chars, all sections); my first selector was wrong.

---

## 6. Recommended pre-TM-1 fix order (blockers first)

1. **A1** — settlement-start 500 (S). Trivial, user-facing crash.
2. **F1 + C1** — worker default landing + expense sidebar entries; turn authenticated-denial into a real 403 (M). Unblocks worker self-service.
3. **B1** — verification-gate policy decision + guard at finalize (M). Financial trust.
4. **B2** — reconcile frozen processing-cost vs settled payout (M–L). Cost-truth.
5. **C2 / B3** — consistent branded 403 + clarify pieces-vs-paid (S). Polish that removes confusion.
6. **Assignment layer (⚠️ design)** — a worker "my queue" + manager assignment monitor, designed so TM-1 / Missing-Pieces / Alter / G1-G7 / stitching-finishing-packing plug in. (No implementation now — design review first.)
7. **Deploy hygiene** — DEBUG off (production settings), apply/confirm migration 0014.

> Follow-up: re-run the halted 9-phase code-analysis workflow after the usage limit resets to deepen Phases E (docs alignment), F (assignment model), H (reporting gaps), I (edge/concurrency) with file-level root causes.
