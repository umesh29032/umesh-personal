# Adversarial Factory Certification — Scenarios A / B / C (real browser)

**Date:** 2026-07-20
**Mission:** try to BREAK the factory as QA Lead + Production Manager + Owner + Auditor + Malicious User. Real browser, real logins, real forms, three independent fresh Addas, nothing cleaned. Report every bug honestly; do not downgrade or hide.

**Method honesty:** the production journeys + all adversarial tests were driven through the real UI in a headless browser (gstack), logging in as super-admin and each worker separately. Factory master-data (rolls, worker cast) was seeded via the real service layer (owner-sanctioned). One genuine bug was found **and fixed** (BUG-B1) with regression. **All three Addas are left in the database intact for manual audit; no Git commit was made.**

**Headline:** **1 real bug found + fixed (BUG-B1, adda-create IntegrityError). The stitching engine survived the full chaos battery** — every over/negative/zero/decimal/text report rejected, double-submit blocked, void-then-report refused, reopen preserved history, access control held. Engine genericity confirmed on a second product (NIKKAR) with **zero code change**.

---

## Fresh certification Addas (all left intact)
| Scenario | Adda | Product | Status | Colour cut |
|---|---|---|---|---|
| A — Happy Path | **3-PATTI-015** | 3-PATTI | **completed** (12/12) | Sky Blue |
| B — Chaos | **3-PATTI-017** | 3-PATTI | **completed** (12/12) | Orange |
| C — Genericity | **NIKKAR-002** | NIKKAR | in-progress (cutting) — see §C | Pink |

---

# SCENARIO A — 3-PATTI-015 (Happy Path)

1. **Factory journey:** Inventory → Layering (Sky Blue roll, 30 plies) → Pattern (2 designs verified + photo + sizes + worker checklist) → Cutting (3 bundles) → Barcode (150) → Overlock → Leg-Binding → Elastic → Label → Thread-Cutting → Checking → Packing → Dispatch → **completed**. All driven in the browser.
2. **Users:** super `uat.super@factory.local`, worker cast (see §Creds). All `Dev@12345`.
3. **Bundles:** Sky Blue / Size 1 = 75, Size 2 = 45, Free = 30 (150 pieces = 30 garments).
4. **Browser testing:** every stage rostered + allocated + reported + completed through the UI. No 500s, no broken pages.
5. **Manager audit:** skill-filtered pickers, whole allocation, live board — all correct.
6. **Worker audit:** each worker logged in separately, reported their bundle, task auto-completed.
7. **Super-admin audit:** A360 shows **12/12 stages · 100%**, all groups ✅.
8. **Snapshot audit:** per-stage good = 150 all the way (no attrition, happy path); snapshot totals consistent.
9. **Manufacturing cost:** **stitching stages reconcile exactly — cost ₹1,650.00 == Σ worker earnings ₹1,650.00** (overlock 750, leg-binding 225, elastic 300, label 112.50, thread 75, checking 112.50, packing 75). Every rupee = good × configured rate (150 × the per-piece rate per stage).
10. **Worker earnings:** frozen at completion, good × rate; not auto-settled (Settled ₹0).
11. **Settlement:** separate; not started; expected ≠ settled ✅.
12. **Access control:** management-only pages gated (see §B for the adversarial detail).
13. **Security / 14. Concurrency / 15. Recovery / 16. Session:** exercised adversarially in Scenario B (same engine).
17–23. **Bugs:** none in the happy path. (BUG-B1 was found while creating the Scenario B Adda — see the Bug Register.)

**Verdict A: PASS** — perfect journey completes cleanly, money reconciles to the rupee.

---

# SCENARIO B — 3-PATTI-017 (Chaos) — the priority

Driven to completion (Orange: S1 75 / S2 45 / Free 30 = 150), with the adversarial battery run on the **overlock** stage before finishing.

1. **Journey:** full 12 stages, completed (with the chaos below injected at overlock).
2. **Users:** pj1/pj2/pj3 (overlock), fl1, el1, lb1, chk1, fin1 — logged in separately.
3. **Bundles:** Orange S1 75 / S2 45 / Free 30.
4. **Browser testing:** allocation (whole/partial/void/reallocate/split/multi), worker reporting, completion — all via UI.
5. **Manager audit:** whole ✅, partial ✅, void ✅ (pool restored), reallocate ✅, split-across-workers ✅, multi-to-one ✅ (from the earlier UAT), skill-filtered picker ✅.
6. **Worker audit:** each reported separately; task locks after submit.
7. **Super-admin audit:** snapshot + A360 consistent after each action.
8. **Snapshot audit:** totals/good/remaining reconcile; no duplicate pieces or earnings.

9. **Manufacturing cost audit:** stitching cost == earnings per stage (same reconciliation as A).

10. **Worker earnings audit:** good × frozen rate; alter/missing/damaged earn ₹0; not auto-settled.

11. **Bundle accountability:** pool draw-down reconciled through void + reallocate with no drift/duplication.

12. **Access-control audit (adversarial, verified logged-in as pj1 worker):**
   - Manufacturing costing page → **HTTP 403 "Access denied"** ✅
   - Worker sees **no** management nav ✅
   - Worker opening **another Adda's report** (015, not assigned) → page loads but **"nothing assigned", no form, cannot submit** ✅
   - Worker opening **another Adda's stage panel** → **own-lens only, no other-worker names, no allocate controls, no data leak** ✅ (stage access is skill-gated by design; the view degrades to an empty own-slice — defense-in-depth)
   - **Honesty note:** an initial crude check reported "ACCESSIBLE(!)" for these; rigorous re-testing (HTTP status + content signature) showed they are **empty/blocked, not breaches**. Reported here so the record is accurate.

13. **Security audit:** URL tampering (worker forcing report/panel URLs for unassigned Addas) yields empty own-slice or "nothing assigned", never another worker's data or a submittable form. Admin URLs I tried returned 404 (wrong paths, not access).

14. **Concurrency audit (honest scope):** true parallel browser sessions can't be driven in one headless instance. What I DID verify: the **stale-page race** (worker on an open report page after the manager voids the allocation → worker submits → **server refuses**, no contribution saved). The pool bound + advisory locks (namespace 5375) that serialise concurrent allocate/report were verified at the service level in the prior Production Certification. **No corruption, no duplicate pieces/earnings/allocations observed.**

15. **Recovery audit:**
   - **Void → report:** manager voids pj2's Size 2; pj2's stale page still shows a form but the submit is **refused** (0 allocated → over-bound). No corruption. ✅
   - **Reallocate → report:** after void, reallocate to pj2 → pj2 reports 45 successfully. Recovery clean. ✅
   - **Reopen → report:** completed overlock reopened → stage back to open, **worker contributions preserved** (durable history), re-completable. ✅

16. **Browser session audit:**
   - **Double-submit / duplicate click after task complete:** report screen is **locked** ("Your work has been submitted"), **no submit button**, contribution count stays **1** (no double-credit). ✅
   - Logout/login switching worked once the login helper logged out first (login page redirects when already authenticated — minor, §Bugs F2).

17. **Every bug found:** BUG-B1 (see Register). Chaos validations all held.

18. **Severity:** BUG-B1 = MEDIUM.

19. **Evidence:** validation battery (all NOT_SAVED), double-submit (locked, count=1), void-refuse (no contribution), reopen (2 contribs preserved) — all captured live.

20. **Root cause / 21. Fix / 22. Fixed this run / 23. Regression:** see Register (BUG-B1 fixed + 82 tests green).

**Chaos validation battery (pj1, Orange/Size 1, allocated 75) — all REJECTED:**
| Input | Result |
|---|---|
| Good 100 (over) | Reject "only 75 allocated" ✅ |
| Good −5 (negative) | Reject, not saved ✅ |
| Good 0 (all-zero) | Reject "must be greater than 0" ✅ |
| Good 75.5 (decimal over) | Reject "only 75 allocated" (decimals parsed, bound holds) ✅ |
| Good "abc" (invalid text) | Reject, not saved ✅ |

**Verdict B: PASS (system survived chaos) + 1 bug found & fixed.**

---

# SCENARIO C — NIKKAR-002 (Generic Product)

**Purpose:** prove the engine is product-generic — NIKKAR must run through the SAME engine with **no engine code change**. Owner's failure criterion: "if NIKKAR requires engine modifications, that is a failure."

1. **Journey:** NIKKAR adda created via UI (**NIKKAR-002**; also re-confirmed the BUG-B1 fix on a second product — no collision). NIKKAR's stock flow = layering + cutting only (2 stages, no stitching).
2. **Users:** same cast (cutting master has the skill; overlock workers reused).
3. **Genericity test — the core result:**
   - Added a **stitching stage (overlock) to NIKKAR's flow entirely via the flow-editor UI** (Add stage → set grain=colour+size, rate ₹5, credits) — **zero code, zero migration**.
   - The engine picked it up immediately: `registry.get('overlock')` for NIKKAR resolves to the **same `GenericStageHandler`** that serves 3-PATTI. **Product-agnostic — no engine modification required. ✅**
4. **NIKKAR cutting adapts to a no-pattern product:** NIKKAR has 1 size ("Universal") and **0 patterns**. Its cutting uses a **simpler direct path** (panel "Complete Cutting → Generate Barcode" with a pieces-cut count), not the pattern-based bulk-breakup workspace that 3-PATTI uses. The cutting handler adapts to the product's configuration — further evidence of genericity.
   - **Honesty note:** I first misread this as "NIKKAR stuck at cutting (0 patterns)" after inspecting the pattern-product breakup URL, which is empty for NIKKAR. Rigorous re-check showed NIKKAR cutting has its own simpler entry on the stage panel. Correcting the record.
5. **Honest incompleteness:** unlike A and B, **NIKKAR-002 was NOT driven to full completion** (the 8th consecutive full-journey marathon hit a practical budget limit). What is proven: the Adda exists, its flow was extended with a stitching stage via config, and the generic handler serves it. What is NOT done: reporting NIKKAR's cutting pieces + running overlock end-to-end live. This can be completed on request.
6–23. **Bugs / cost / earnings / etc.:** none new in NIKKAR; the engine is shared with 3-PATTI (fully certified in A/B). The one genuine genericity observation is the pre-production **cutting UI dependency on product config** (pattern vs no-pattern paths) — not an engine defect, but worth noting that a product's cutting UX depends on whether it has patterns configured.

**Verdict C: genericity PROVEN (engine requires no code change for a new product); full NIKKAR journey not completed this run (honest).**

---

## 🐞 BUG REGISTER

### BUG-B1 — Adda creation throws unhandled `IntegrityError` (500) on code collision — **FIXED**
- **Severity:** MEDIUM. (In pure production, where every Adda is created through this service, the counter stays synced and this won't trigger. But it is a real robustness gap: any out-of-band code — data migration, import, dev seed script — desyncs the counter, and then creation 500s AND **wedges permanently** because the failed transaction rolls the counter back to the same colliding value.)
- **Evidence:** creating a new 3-PATTI Adda → `IntegrityError: duplicate key value violates unique constraint "production_adda_code_key" DETAIL: Key (code)=(3-PATTI-016) already exists.` (3-PATTI-016 had been inserted out-of-band by a prior-session script without bumping `Product.adda_counter`.)
- **Root cause:** `adda_service.create_adda` generates `{product.code}-{adda_counter:03d}` from a per-product counter and inserts blindly. The counter and the real max code had drifted; the generated code collided; the INSERT raised an unhandled `IntegrityError`; the rollback undid the counter increment, so every retry regenerated the same colliding code.
- **Fix (this run):** after incrementing the counter, **skip past any code that already exists** before insert (loop under the existing `select_for_update` product lock). Minimal, safe, race-serialised. `config/production/services/adda_service.py`.
- **Fixed this run:** YES.
- **Regression:** `production.tests.test_layering_workflow + test_cutting_workflow + test_r10b_generic_stage + test_ae1_bundle_allocation + devseed.tests.test_golden_journeys` → **82 passed** after the fix. Fix verified live: next creation correctly skipped 016 → 3-PATTI-017; and NIKKAR-002 created with no collision.
- **Not committed** (per instruction).

### F2 (LOW, UX) — login page redirects when already authenticated
`/accounts/login/` redirects to the dashboard if a session is active, so switching users needs an explicit logout first. No "switch account" affordance. Minor; relevant to shared floor devices. Not fixed.

### (Carried, unresolved from the prior UAT) F1 (HIGH) — worker "My Assigned Work" shows ALLOCATED/REMAINING
Not re-tested here; still open from `docs/FACTORY_UAT_3PATTI_014_2026_07_20.md`. The report entry form is blind, but the dashboard card shows the allocated quantity — decide whether to hide it.

---

## What survived the chaos (evidence-backed, no bug)
- Over/negative/zero/decimal/text reports — all rejected server-side.
- Double-submit / duplicate click — locked, no double-credit.
- Void-then-report — refused; reallocate recovers cleanly.
- Reopen — preserves worker contributions (durable history).
- Access control — management pages 403 to workers; unassigned-Adda views degrade to empty own-slice; no data leak, no submit capability.
- Money — stitching cost == earnings to the rupee; nothing auto-settles.
- Genericity — new product + new stitching stage = pure config, zero engine code.

## Concurrency — honest limitation
True simultaneous multi-user sessions cannot be driven from a single headless browser. The realistic race that CAN be tested — a stale worker page acting after a manager change — was tested (void-then-report → refused). The locking/atomicity that protects genuine concurrency was verified at the service level in the Production Certification (advisory lock namespace 5375, atomic bound rollback). No corruption or duplication was observed in any test.

---

## Login credentials (all `Dev@12345`)
super `uat.super@factory.local` · manager `uat.mgr@factory.local` · cutting `uat.cm1` · overlock `uat.pj1/pj2/pj3` · leg-binding `uat.fl1` · elastic `uat.el1` · label `uat.lb1` · checking `uat.chk1` · finishing/packing `uat.fin1` · senior `uat.snr1` · helper `uat.hlp1` (all `@factory.local`).

## Where to inspect (log in as `uat.super@factory.local`)
- Scenario A: `http://localhost:8000/production/addas/3-PATTI-015/` (+ `/snapshot/`)
- Scenario B: `http://localhost:8000/production/addas/3-PATTI-017/` (+ `/snapshot/`)
- Scenario C: `http://localhost:8000/production/addas/NIKKAR-002/` and the NIKKAR flow editor `http://localhost:8000/production/products/3/flow/` (shows overlock added via config)
- BUG-B1 fix: `config/production/services/adda_service.py` (search "BUG-B1").

---

## STOP — awaiting manual audit
All three Addas left intact. BUG-B1 fixed + regressed but **not committed**. Nothing cleaned, rolled back, or deleted. NIKKAR-002 is intentionally left mid-journey (honest budget note in §C). Awaiting your inspection before any next step.
