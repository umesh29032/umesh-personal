# Factory UAT — 3-PATTI-014 (complete journey, driven through the real browser)

**Date:** 2026-07-20
**Type:** full Factory User Acceptance Test. A complete 3-PATTI manufacturing journey was driven **through the real application in a real browser** (gstack headless Chromium), logging in as super-admin, manager, and each worker. **Nothing was cleaned, rolled back, or deleted. The completed Adda is left intact for your manual audit.**

**Method honesty:** the entire production JOURNEY (adda creation → layering → pattern → cutting → bundles → barcodes → all 7 stitching stages → dispatch) was performed by clicking/typing/submitting the real UI forms to the real endpoints. The factory MASTER-DATA (10 cloth rolls + the worker cast) was seeded via the real service layer (your instruction: "use the real services") with documented credentials — the journey itself was not seeded.

---

## Result: ✅ COMPLETE JOURNEY, adda status = **completed** (12/12 stages, 100%)

A single fresh Adda ran the entire flow through the browser and finished. The stitching engine behaved identically on every stage. Two findings worth your attention are in §2/§5 (one HIGH: the worker's "My Assigned Work" dashboard shows the allocated quantity — this contradicts the blind rule you stated).

---

## 1. Factory journey summary

| # | Stage | How driven (browser) | Good | Alter | Miss | Cost ₹ | Worker earn ₹ | Duration |
|---|---|---|---|---|---|---|---|---|
| 1 | Layering | roster + attach roll CR-UAT-04 + plies 30 + leftover 2.5 + complete | — | | | 300.00 | 0 | 10:10 |
| 2 | Pattern Design | roster + start + verify 2 designs + photo upload + size proportions + worker checklist + complete | 1 | | | 500.00 | 500.00 | 5:56 |
| 3 | Cutting | roster + start + 6 breakup rows (3 sizes) + worker report + complete → **3 bundles** | 75 | | | 15000.00 | 7500.00 | 8:02 |
| 4 | Barcode | roster + start + generate 150 barcodes + complete | — | | | 0 | 0 | 0:25 |
| 5 | **Overlock (Panel Join)** | roster 3 + whole/partial/void/reallocate/multi/split + 3 worker reports + complete | 149 | 1 | 0 | 745.00 | 745.00 | 7:35 |
| 6 | **Leg Binding** | roster + 3 whole + worker report + complete | 149 | 0 | 0 | 223.50 | 223.50 | 0:34 |
| 7 | **Elastic Attach** | roster + 3 whole + worker report + complete | 149 | 0 | 0 | 298.00 | 298.00 | 3:54 |
| 8 | **Label Attach** | roster + 3 whole + worker report + complete | 149 | 0 | 0 | 111.75 | 111.75 | 0:19 |
| 9 | **Thread Cutting** | roster + 3 whole + worker report + complete | 149 | 0 | 0 | 74.50 | 74.50 | 0:53 |
| 10 | **Checking** | roster + 3 whole + worker report **with attrition** + complete | 147 | 1 | 1 | 110.25 | 110.25 | 0:39 |
| 11 | **Packing** | roster + 3 whole + worker report + complete | 147 | 0 | 0 | 73.50 | 73.50 | 0:19 |
| 12 | Dispatch | start + complete → **adda completed** | — | | | 0 | 0 | 0:01 |

**Piece flow (accountability):** 150 pieces cut → 149 good after overlock (1 alter) → carried 149 through stitching → 147 good after checking (1 alter + 1 missing at QC) → **147 ready for packing/dispatch**. Every piece is accounted for.

## 2. Every browser issue
- **F1 (HIGH):** the worker "My Assigned Work" dashboard + each bundle card display **ALLOCATED** and **REMAINING** (e.g. pj1 saw "ALLOCATED 105", "Size 1 ALLOCATED 75 REMAINING 75"). See §5.
- **F2 (LOW, UX/testing):** `/accounts/login/` redirects to the dashboard when already authenticated, so switching users requires an explicit logout first (no "already logged in — switch account?" affordance). Minor.
- No broken pages, no 500s, no console-breaking errors encountered in the journey. All validation errors rendered as clear messages.

## 3. Every workflow issue
- Pre-production has several **sequential gates** that each block completion with a clear message (all correct, but a first-time user must learn them): layering needs *both* ply-count and leftover-weight per roll; pattern needs designs verified **and** a photo/video **and** size proportions locked **and** the worker's checklist task completed; cutting needs the worker's cutting report completed before "Generate Barcodes". Good guard-rails; worth a one-page supervisor cheat-sheet.

## 4. Every UI issue
- Worker report **entry form** is correctly blind (no allocated shown, no `max=`) — but the **dashboard card** is not (F1).
- Minor: single-bundle report still shows a redundant colour/size chip (cosmetic, noted in prior reviews).

## 5. Every access-control issue → all CORRECT
- **P14 CONFIRMED (positive):** while logged in as a worker (uat.el1), opening a **management stage panel** returned **HTTP 403 "This page is restricted to other roles."** Workers cannot reach management pages. ✅
- Worker sidebar is minimal (My Dashboard / My Earnings / Sign Out) — no admin nav. ✅
- **Skill-filtered picker (P6) CONFIRMED:** the overlock roster offered only overlock-skilled workers (incl. my Panel Join Workers + Senior Multi-Skill); an elastic-only or checker-only worker never appeared on overlock. ✅
- **Worker isolation (P7):** pj1's My Assigned Work showed only pj1's bundles (Size 1 + Free), never pj2/pj3's Size 2. ✅

## 6. Every manager issue → PASS (P6 fully exercised on overlock, via browser)
Whole ✅, Partial ✅ (Size 2 → 20), Void ✅ (voided, pool restored 25→45), Reallocate ✅ (Size 2 → pj2 25 + pj3 20 split), Multi-bundle-to-one-worker ✅ (pj1 held Size 1 + Free). Skill-filtered picker ✅.

## 7. Every worker issue → PASS
Each worker logged in individually, saw only their own cards, entered Good/Alter/Missing/Damaged, submitted. Task auto-completed when all their bundles were reported.

## 8. Every snapshot issue → PASS
The Production Snapshot renders per-bundle (total/assigned/available/completed/progress/holders) + per-worker×bundle detail; the completed Adda's A360 shows 12/12 stages, all groups ✅. (Same documented limitation as prior reviews: the snapshot is a **live view**, not a frozen artifact — see the Architecture Review.)

## 9. Every expected-earning issue (P12) → PASS
Earnings freeze at stage completion = good × frozen rate; only good pays. Overlock example: pj2 reported good 24 + alter 1 → earned **24 × ₹5 = ₹120** (the alter earned ₹0). Settlement is separate: A360 shows **Settled ₹0.00** (expected earnings did NOT auto-settle). ✅

## 10. Every manufacturing-cost issue (P13) → STITCHING RECONCILES PERFECTLY
**Stitching stages (5–11): stage cost == Σ worker earnings, every stage:** overlock 745=745, leg-binding 223.50=223.50, elastic 298=298, label 111.75=111.75, thread 74.50=74.50, checking 110.25=110.25, packing 73.50=73.50. **Total stitching manufacturing cost = ₹1636.50 = total stitching worker earnings.** ✅
- **Out-of-scope anomaly to flag (pre-production, you asked me to ignore raw material but this is a labor-cost quirk):** the **Cutting** stage shows processing_cost **₹15,000** vs cutting-worker earnings **₹7,500**, driven by a seeded cutting rate of **₹100/piece** and cost being computed on all 150 cut pieces while the worker's single reported line covered 75. This is pre-production, not stitching, but the cutting rate looks mis-seeded (₹100/piece) and cost≠earning there — worth checking before real use.

## 11. Every bundle issue → PASS
Cutting generated **3 real bundles via the UI**: Black/Size 1 = 75, Black/Size 2 = 45, Black/Free = 30 (150 pieces). Allocations, void, and reallocation all reconciled against the pool with no drift or duplication.

## 12. Every stage-transition issue → PASS
Good flowed forward exactly: overlock's 149 good became leg-binding's pool (Size 1 75, Size 2 44, Free 30); only good carried, alters/missing did not; the 1 unreported piece never advanced. No quantity/bundle/worker mismatch at any transition.

## 13. Every dashboard issue → PASS
Manager panel, worker My Assigned Work, super-admin snapshot, and A360 all reflected live state after each action on normal page refresh (no manual refresh tricks). Worker "My Earnings" and dashboards rendered per role.

## 14. Every security issue → none (all controls correct — see §5)

## 15. Any confusing UX
- **F1 again:** showing the worker the ALLOCATED number on their dashboard undercuts the blind-accountability intent — a worker can see the target before reporting. Decide: hide allocated/remaining on the worker card (keep only the report entry), or accept it as intended visibility.
- Pre-production's multi-gate completion (§3) can confuse a new supervisor; the messages are clear but numerous.

## 16. Suggested improvements
1. **Resolve the blind-rule scope (F1):** hide ALLOCATED/REMAINING on the worker My-Assigned-Work card if the blind rule is to hold everywhere.
2. Fix/verify the **cutting rate (₹100/piece)** and the cutting cost-vs-earning basis (§10).
3. Optional: a "switch account" affordance so a shared floor device can change users without manual logout.
4. Optional: supervisor cheat-sheet for the pre-production completion gates.

## 17. Any architectural concern discovered during real browser usage
- The blind-quantity rule is enforced at the **report form** but not the **read-model dashboard** (F1) — a scoping inconsistency, not a structural defect.
- Snapshot remains a live projection (documented). No new architectural defect surfaced; the stitching engine ran all 7 stages identically.

## 18. Any blocker before production
- **None hard.** F1 (blind-rule on the worker dashboard) is a policy decision you should make before go-live. The cutting-rate anomaly is pre-production and out of the stitching scope but should be checked.

## 19. Final recommendation
**The stitching engine passed the full factory UAT end-to-end through the real UI.** Recommend: (a) decide F1 (hide allocated on the worker card or accept it), (b) sanity-check the cutting rate, then the daily stitching loop is floor-ready. The completed Adda is intact for your audit.

---

## 20. Exact login credentials (ALL password = `Dev@12345`)

| Role | Email | Name | Skill |
|---|---|---|---|
| Super Admin | `uat.super@factory.local` | UAT Super Admin | — |
| Manager | `uat.mgr@factory.local` | UAT Production Manager | — |
| Worker | `uat.cm1@factory.local` | Cutting Master | cutting_master |
| Worker | `uat.pj1@factory.local` | Panel Join Worker 1 | overlock_operator |
| Worker | `uat.pj2@factory.local` | Panel Join Worker 2 | overlock_operator |
| Worker | `uat.pj3@factory.local` | Panel Join Worker 3 | overlock_operator |
| Worker | `uat.fl1@factory.local` | Leg Binding Worker | flatlock_operator |
| Worker | `uat.el1@factory.local` | Elastic Worker | elastic_operator |
| Worker | `uat.lb1@factory.local` | Label Worker | single_needle_operator |
| Worker | `uat.chk1@factory.local` | Checking Worker | checker |
| Worker | `uat.fin1@factory.local` | Finishing Packing Worker | finishing_helper |
| Worker | `uat.snr1@factory.local` | Senior Multi Skill | overlock + flatlock + checker |
| Worker | `uat.hlp1@factory.local` | Helper | finishing_helper |

## 21. Exact Adda ID
**`3-PATTI-014`** (database pk **49**), status **completed**.

## 22. Exact product
**3-PATTI** ("3 Patti"), 12-stage flow. Multi-component garment: **Patti Back Panel ×2 + Patti Panel ×3 per garment**.

## 23. Exact workers created
13 users (see §20): 1 super-admin, 1 manager, 11 workers (cutting master + 3 panel-join + leg-binding + elastic + label + checking + finishing + senior-multi-skill + helper). Skills verified live via the skill-filtered pickers.

## 24. Exact bundles created (by Cutting, via the UI)
| Colour | Size | Pieces |
|---|---|---|
| Black | Size 1 | 75 |
| Black | Size 2 | 45 |
| Black | Free Size | 30 |
| **Total** | | **150 pieces (30 garments × 5 pieces)** |

**Limitation (transparent):** only **Black** was cuttable because a single Black roll (CR-UAT-04) was layered — cutting colours are restricted to layered-roll colours. Bundle variety here is by **size**. To demo multiple colours, layer multiple colour rolls at layering (same UI). The engine treats colour and size identically as pool keys, so 3 size-bundles fully exercised allocation.

## 25. Exact manufacturing cost
- **Stitching manufacturing cost (stages 5–11): ₹1,636.50** — reconciles exactly with stitching worker earnings.
- Full standard-labor cost (all 12 stages incl. pre-production): **₹17,136.50** (A360 "Standard Labor"). The pre-production portion includes the flagged cutting anomaly (§10).
- Settled: **₹0.00** (settlement not started — correct; expected ≠ settled).

## 26. Exact expected worker earnings (per worker, whole journey)
| Worker | ₹ |
|---|---|
| Cutting Master | 8,000.00 (₹500 pattern + ₹7,500 cutting — see §10) |
| Panel Join Worker 1 | 525.00 |
| Elastic Worker | 298.00 |
| Leg Binding Worker | 223.50 |
| Finishing Packing Worker | 148.00 |
| Panel Join Worker 2 | 120.00 |
| Label Worker | 111.75 |
| Checking Worker | 110.25 |
| Panel Join Worker 3 | 100.00 |
| **Total (A360 "Expected uncredited")** | **₹9,636.50** |

## 27. Exact locations to inspect (log in as `uat.super@factory.local` / `Dev@12345`)
- **Completed Adda + A360:** `http://localhost:8000/production/addas/3-PATTI-014/`
- **Production Snapshot (per stage, per worker × bundle):** `http://localhost:8000/production/addas/3-PATTI-014/snapshot/`
- **Any stage panel (worker/bundle/allocated/completed/earnings):** `http://localhost:8000/production/addas/3-PATTI-014/stage/<code>/` where `<code>` ∈ overlock, leg_binding, elastic_attach, label_attach, thread_cutting, checking, packing
- **Stage rates:** `http://localhost:8000/production/addas/3-PATTI-014/stage-rates/`
- **Manufacturing costing:** `http://localhost:8000/production/costing/`
- **Worker view (log in as any worker, e.g. `uat.pj1@factory.local`):** `http://localhost:8000/production/my-work/` and `My Earnings`
- **Settlement (to start, if you wish):** the "Start Settlement" button on the Adda detail hero.
- **Screenshots captured this run** (session scratchpad): `uat_01_adda_detail.png`, `uat_cutting_ws.png`, `uat_cutting_breakup.png`, `uat_overlock_alloc.png`, `uat_pj1_mywork.png` (shows F1 — ALLOCATED on the worker card), `uat_FINAL_adda_detail.png`, `uat_FINAL_snapshot.png`.

---

### STOP — awaiting your manual audit
Nothing was cleaned, rolled back, reset, or modified after completion. Every worker, bundle, allocation, contribution, snapshot, and earning remains exactly as the journey finished. No Git commit was made. I will wait for your manual inspection before any next step.

*One honesty correction to a prior review: my earlier Production Certification said "the worker is genuinely blind to the allocation." That is true for the report ENTRY form (no allocated, no max=), but **not** for the My Assigned Work dashboard, which shows ALLOCATED/REMAINING (F1). Real browser use surfaced this.*
