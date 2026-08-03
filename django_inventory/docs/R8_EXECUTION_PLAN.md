---
id: r8-execution-plan
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# R8 EXECUTION PLAN — Pattern Design redesign + rename + generic stage snapshots

> Phase R8 of [IMPLEMENTATION_ROADMAP_PDD_V1.md](IMPLEMENTATION_ROADMAP_PDD_V1.md).
> Spec-of-record: [STAGE_TRIO_SPEC_IMPACT_2026_07_05.md](STAGE_TRIO_SPEC_IMPACT_2026_07_05.md)
> (owner 10-section stage-trio spec + resolved decisions C-1 delete-and-rebuild ·
> C-2 display-only rename · C-3 phone checklist · generic snapshot architecture).
> Functions as the PDD §15/§16 amendment. Earning engine untouched (stage_earnings_flow
> recipe); money-write STOP rule applies throughout.
> STATUS: **✅ ACCEPTED by owner 2026-07-05 (uncommitted — checkpoint
> policy). Post-acceptance follow-up delivered: precise
> `lead_minutes_from_layering` behavior + future waiting/working split
> documented in [STAGE_TRIO_SPEC_IMPACT §F](STAGE_TRIO_SPEC_IMPACT_2026_07_05.md).**
> Owner-ordered 7-point pre-implementation verification
> ran CLEAN first (V-1 input→consume chain is formula-documented:
> lay_count × pieces_count × size% = cutting's suggested breakup · V-6 fixed
> freeze = rate natively; ONE nit found+fixed: recon `_classify` false-flagged
> fixed stages `no_output_qty` → method-aware branch).
> Built: WP-1 rename (migration prod 0043 data-only + ~10 templates + docs;
> identifier frozen) · WP-2 generic snapshots (handler `admin_snapshot` +
> shared partial + prev-stage injection, mgmt-gated) · WP-3 phone checklist
> (schema mode='checklist' + `checklist_submit` hook; single truth with the
> console) · WP-4 fixed double-guard · WP-5 lead-minutes (migration prod
> 0044) · WP-6 teardown (ALL 15 test Addas + all money purged, dependency-
> ordered, 0 residue; real products kept) + Flow-Editor config (layering
> non-paying · Pattern Design fixed ₹500 pays · Cutting ₹100 pays — all data).
> Results: gate PASS **800** (+12 test_r8_pattern_design) · golden
> byte-identical · LIVE full-trio E2E on fresh REAL 3-PATTI-009 (owner §9
> rule): layering report shows ZERO ₹ → complete → panel shows "Layering —
> reference" to admin ONLY (worker leak-check 0) → phone checklist @360
> (partial submit refused naming "Patti Panel"; ticks persist = shared
> verification rows) → submit → **fixed ₹500 frozen** → pattern complete →
> lead-time 2 min stored → cutting panel shows "Pattern Design — reference
> (2/2, lead 2 min)" → 10 pcs @ ₹100 = ₹1000 → bundles → complete (cost
> 1000 = 100×10; pattern cost 500 fixed — duality coherent) → settlement
> draft "Pattern Design + Cutting, expected ₹1500" → finalized → utest
> ledger ₹1500. One regression caught live: multi-line `{# #}` comment
> leaked into the checklist page (the known Django-template rule) — fixed to
> `{% comment %}`.
> Anchors verified against code 2026-07-05 (post-R7, gate 788).

## Work packages (in build order)

### WP-1 — Rename: "Cutting Pattern" → "Pattern Design" (display only, C-2)
- Data: `Stage.name` update (data migration in `production`, reversible; the
  seeded flow row) — internal `stage.code='cutting_pattern'` FROZEN (registry
  key/URLs/tests/seeds untouched; documented in GLOSSARY + stage docstring).
- User-facing strings: ~10 templates (panels, workspace, product_sizes_edit,
  buttons/labels), form labels, docs (GUIDE/README/GLOSSARY/PAGES).
- Verify: existing Addas render "Pattern Design" everywhere; zero behavior
  change (browser sweep: Adda detail, dashboards, flow editor, settlement
  screens, timeline verbs).

### WP-2 — Generic stage-snapshot architecture (owner requirement)
The NEW standard, built on the existing seam (`handler.snapshot(adda)`,
base/handler.py:86, already registry-consumed at adda_views.py:166):
- Handler contract gains **non-abstract** `admin_snapshot(self, adda) -> dict
  | None` (default None = stage exposes nothing; open-closed — future stages
  just override). Return shape is template-free data:
  `{'title': str, 'sections': [{'label': str, 'rows': [(key, value), …]}]}`.
- **One shared partial** `production/_stage_admin_snapshot.html` renders that
  shape (mobile-first stacked; desktop grid). Adda-360 will reuse this exact
  partial (owner requirement).
- `StagePanelView` injects `prev_admin_snapshot` = the admin_snapshot of the
  nearest PREVIOUS stage in the product's flow (order-driven, registry lookup)
  — **management-gated in ctx AND template** (workers never receive the data;
  leak-test like R1 My Work).
- R8 implements two producers: **layering** (rolls, colour breakdown,
  widths/weights verified, total layers, layer lengths, leftovers — reusing
  `get_layering_snapshot` + roll entries) and **pattern_design** (designs
  completed/total, per-design verified state, photos count — reusing the
  verification rows). Cutting's panel consumes layering→pattern automatically;
  **R9's cutting snapshot becomes a data-only exercise.**
- Reference views ONLY: live reads via existing services; NO new tables, NO
  frozen copies, NO new writes.

### WP-3 — Pattern-master phone checklist report (C-3)
- `cutting_pattern` handler `contribution_schema()` override → new field kind
  **`check`**: one row per `ProductPatternAssignment` of the Adda's product
  (label = pattern name, thumbnail = `ProductPattern.reference_image` if set).
  Optional multi-photo upload field → existing `CuttingPatternPhoto` (same
  storage path).
- Report engine: `worker_report_views` renderer + `worker_task_service`
  parser learn the `check` kind (today: quantity/choice). Submission is the
  SAME C-TM chokepoint call and does two things atomically:
  1. syncs `CuttingPatternVerification` rows via the EXISTING pattern
     verification service (single source of truth with the operator console —
     C-3), refusing partial checklists on complete (all required designs must
     be ticked);
  2. books ONE contribution `good_quantity=1` → fixed pay = frozen rate × 1
     (freeze/settle engine untouched).
- Worker sees ONLY: checklist + reference images + photo upload (§5). The
  report page is already minimal/self-scoped; no layering/costing data in ctx.
- Console keeps working unchanged; whichever surface verifies first wins
  (rows are shared).

### WP-4 — Fixed-pay double-guard
At the chokepoint (`complete_worker_task` or report path): a
`cost_method='fixed'` stage REFUSES a second COMPLETED report with an
actionable error naming the worker who already completed (else two assigned
workers = 2× the fixed amount). Single-writer intact; test-pinned.

### WP-5 — Layering→Pattern lead-time analytics (§3)
`pattern_design_lead_minutes` nullable column on the pattern stage record
(production migration; computed at pattern complete = pattern
`completed_at − layering completed_at`). Analytics only (standing
auto-duration rule 2026-06-03); shown in the pattern admin_snapshot + stage
tile. No payment reads it.

### WP-6 — Config + C-1 data rebuild (no code — Flow Editor + audited teardown)
1. **Teardown (owner C-1):** delete DEV/test Addas that no longer represent
   the final flow — 3-PATTI-001…008, DEV-R4M-*, DEV-R7F-*, TEST-* and their
   money rows (dependency-ordered script: ledger entries → PSIs → settlement
   items/SWAs → settlements → history → contributions/tasks → stage rows →
   Addas; dev DB only; the DEV worker ACCOUNTS stay). Listed + logged; run
   once, verified 0 residue.
2. **Flow Editor config on 3-PATTI (data, never hardcoded):**
   layering `credits_workers=False` (production-input-only, §2) ·
   pattern_design `cost_method=fixed`, per-product rate, `credits_workers=True` ·
   cutting rate **₹100**, `credits_workers=True` (§7).

## Files (estimated)

| Area | Files |
|---|---|
| WP-1 | production data migration (Stage.name) + ~10 templates + docs |
| WP-2 | `stages/base/handler.py` (admin_snapshot default) + layering/cutting_pattern handlers + `_stage_admin_snapshot.html` (new) + `stage_views.py` (prev-snapshot injection, mgmt-gated) |
| WP-3 | `stages/cutting_pattern/handler.py` (schema) + pattern service (checklist sync entry) + `worker_report_views.py` + `worker_task_service.py` (check kind parse) + report template |
| WP-4 | `worker_task_service.py` guard + tests |
| WP-5 | production migration (lead-minutes column) + pattern service complete hook |
| WP-6 | one-off teardown script (scratch, not committed) + Flow Editor via browser |
| Tests | `test_r8_pattern_design.py` (new) + touched suites |

Migrations: production ×2 (Stage.name data rename · lead-minutes column) —
both additive/reversible. **Zero expense-app changes; zero new money writers.**

## Tests
1. Rename: seeded stage renders "Pattern Design"; identifier untouched
   (registry/URLs still resolve); existing SR/history unaffected.
2. Generic snapshot: layering admin_snapshot shape; pattern panel receives
   `prev_admin_snapshot` for management, **absent for workers** (leak test);
   stage with no override → None → partial renders nothing.
3. Checklist report: schema exposes one check row per assignment; complete
   with all ticked → verification rows synced + ONE contribution qty=1 +
   expected = fixed rate; partial checklist → refuse; console-then-phone and
   phone-then-console both converge on the same rows (single truth).
4. Fixed double-guard: second worker's complete on a fixed stage refuses,
   names the first; per_piece stages unaffected.
5. Lead-time: minutes stored at pattern complete; None when layering never
   completed.
6. Golden ₹225 byte-identical + full gate (734→788→+R8), writer gates green.

## Browser E2E (3-PATTI ONLY — §9; after WP-6 teardown+config)
Fresh 3-PATTI Adda end-to-end: layering (helpers report layers, NO ₹ shown
anywhere — non-earning now) → pattern: management sees the layering snapshot
on the panel, DEV pattern-master phone checklist (tick designs + upload photo)
→ fixed expected ₹ appears in My Work → second worker fixed-report refused →
cutting: panel shows pattern snapshot, per-piece flow at ₹100 → settlement
draft shows pattern (fixed) + cutting lines, finalize, golden-consistent
totals. 360 + desktop; worker vs management snapshot visibility both proven.

## Risks
| Risk | Mitigation |
|---|---|
| Rename misses a string | grep-driven sweep + browser check of every surface listing stages |
| `check` kind leaks into other stages' reports | kind only emitted by the pattern handler's schema; parser ignores unknown kinds elsewhere (tested) |
| Checklist ↔ console drift | both write through the SAME verification service (C-3); convergence test |
| Teardown breaks PROTECT chains | dependency-ordered deletes, dev DB only, verified 0 residue; DEV user accounts retained |
| Fixed guard blocks legit re-settle after reverse | guard reads COMPLETED tasks, not settlement state — reverse/re-settle path unaffected (test) |

## Rollback
Migrations reversible; rename is data (reverse migration restores);
`git revert` for code. Teardown is deliberate and owner-ordered (test data).

## Acceptance criteria
- [ ] "Pattern Design" everywhere user-facing; identifier frozen; existing
      Addas fine (browser sweep).
- [ ] Generic snapshot: pattern panel shows layering summary to management
      only; cutting panel shows pattern summary; ONE shared partial; zero new
      tables.
- [ ] Phone checklist E2E on real 3-PATTI (fixed pay ₹, photos, single truth
      with console).
- [ ] Layering shows no ₹ anywhere; cutting pays per-piece at ₹100 (config).
- [ ] Gate PASS + golden byte-identical; docs synced same session.

## Order (estimated)
WP-1 ~1.5h · WP-2 ~2h · WP-3 ~3h · WP-4 ~45m · WP-5 ~45m · WP-6 ~1h ·
E2E+docs ~2h ≈ 1.5 working days. Uncommitted (checkpoint policy).
