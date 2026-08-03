# Architecture Design Document — Production Allocation Engine (Bundle Model)

**Status:** DRAFT for owner approval · **Date:** 2026-07-20 · **Author:** engineering (FAT follow-up)
**No code written. Implementation begins only after this ADD is approved.**
Inputs: FAT Phase 1A ([FAT_PRODUCTION_CERTIFICATION](FAT_PRODUCTION_CERTIFICATION_2026_07_20.md)) +
9-point architecture review (file:line evidence) + owner's revised business model (2026-07-20).

---

## 0. TL;DR — the recommendation up front (and the challenge)

The owner's revised model — **Whole Bundle allocation (default) + optional Partial allocation** —
is **a superset of what the engine already does.** The current `WorkerStageAllocation` is a
quantity slice of a per-(colour,size) pool with a hard `qty ≤ available` refusal. That IS
partial allocation. "Whole bundle" is simply `qty = entire remaining` behind a one-click UI.

**Therefore I do NOT recommend rebuilding the engine or introducing a first-class
exclusive-owner Bundle table.** That was the right idea for the *strict no-split* model in the
Phase-1A report, but the owner has now **explicitly allowed partial (multiple workers per
colour+size)** — which an exclusive-owner table would actively fight. The strongest long-term
design is **ADAPT & HARDEN** the existing pool engine:

1. A **Bundle read-model** (a service projection, **no new table**) so UI/dashboard/worker all
   speak one vocabulary: "Red / M / 100".
2. A **Whole-bundle allocation mode** (default) = allocate the full remaining in one click; the
   bundle then leaves the available list. **Partial** stays as an explicit, non-default toggle.
3. **Hard over-report validation** — delete the feature-flag gate; the correct logic already
   exists. Enforce at report-submit, not just at complete.
4. **(colour, size) pair validation** in the worker form (close the flat-list gap).
5. A worker **"My Assigned Work"** view listing each allocation as a bundle item.

This keeps everything the FAT already certified as correct (money-at-settlement-only,
append-only reassignment, full stage-genericity), needs **zero historical-data migration**, and
has a small blast radius (mostly UI + un-gating one flag + a read-model service + one form fix).

A heavier alternative (persisted Bundle table, Option C) is compared in §3 and **not
recommended** — for a stage pipeline it reinvents the per-stage pool snapshot it already has.

---

## 1. Current architecture

- **Pool source.** At cutting-complete, `_materialize_breakdown`
  ([cutting/service.py:181](../config/production/stages/cutting/service.py)) freezes
  `AddaProductSizeColorPieceBreakdown` (APSCPB) = one row per (adda, size, colour) with a
  `verified_piece_count`. Downstream stages materialize a `StagePoolSnapshot` from the previous
  stage's good output (`pool_service.materialize_stage_pool`). **This is the true "bundle
  quantity" store**, per stage.
- **Allocation unit.** `WorkerStageAllocation` (WSA)
  ([core.py:490](../config/production/models/core.py)) = `stage_record` (consuming), `worker`,
  `color` (nullable), `size` (nullable), `allocated_quantity`, `created_by`, `voided_at`. All FKs
  PROTECT; **append-only** (void, never delete); **carries no money**. Meta constraint:
  `allocated_quantity > 0` only — **no uniqueness on (stage, colour, size)**.
- **Allocate.** `pool_service.allocate(consuming_sr, worker, *, qty, actor, color_id, size_id)`
  ([pool_service.py:346](../config/production/services/pool_service.py)) — management-only, takes
  an advisory lock on (source, dims), refuses `qty > available`. `available = pool_good − Σ
  non-voided allocations (+ recovered − garment-set caps)`.
- **Report.** `WorkerReportView` → schema from `GenericStageHandler.contribution_schema`
  scoped to the worker's allocated dims; writes `WorkerStageContribution` (good/alter/missing/
  damaged) via the single-writer services.
- **Over-report bound.** `check_allocation_bound` (complete-time) — correct logic
  `Σ(good+alter+missing+damaged) ≤ Σ allocated` per reported dim — **gated by
  `ENFORCE_ALLOCATION_BOUND` (default False)**. Only `bound_soft_warning` runs by default.
- **Money.** Settlement-only: `finalize_adda_settlement` reads contributions, writes
  `StageWorkAssignment = good × frozen rate`. WSA never feeds money. Legacy money-at-allocation
  disabled (`LEDGER_CREDIT_AT_ALLOCATION=False`).
- **Extensibility.** Handler registry + generic fallback + `WorkflowStage.allocation_dimensions`
  ({NONE, QUANTITY, COLOR_SIZE}); **zero stage-name conditionals** in allocation/report/
  earnings/settlement.
- **`CuttingBundle`** ([cutting.py:415](../config/production/models/cutting.py)) — a **per-size,
  all-colours** container from the legacy bundling flow. Different grain, unrelated to the pool
  allocation path. Its name is the source of much confusion (see §4).

## 2. Problems found during FAT (Phase 1A)
| Ref | Problem | Proven |
|---|---|---|
| B | Same (colour,size) splittable across workers with no guard | LIVE: 6+4 to 2 workers |
| D | Over-report bound OFF by default → worker reported 10 vs 6 allocated, accepted | LIVE |
| C | Allocation UI = worker + colour·size-lot + free-qty box ("edit to split"); no whole-bundle one-click; lot never disappears | code + UI |
| A | "Bundle" (`CuttingBundle`) is per-size, wrong grain; no bundle vocabulary in the pool path | code |
| E | Worker form validates colour and size as flat independent lists → can report an unallocated (colour,size) pair | code |

**Reframe under the revised model:** B is **no longer a bug** (partial is now allowed) — it just
needs to be *deliberate* (Partial mode), not the *only* mode. D and E are real defects. C and A
are UX/vocabulary gaps. So the "violation" surface shrank the moment the owner allowed partial.

## 3. Target architecture — options compared (the challenge)

| | **Option B — Adapt & Harden (RECOMMENDED)** | Option C — Persisted Bundle table | Option A — Exclusive-owner Bundle (Phase-1A original) |
|---|---|---|---|
| Bundle = colour+size | Read-model projection over APSCPB/pool + WSA | New `Bundle` table, FK from WSA | New `Bundle` table with single holder FK |
| Whole + partial | Whole = `qty=remaining`; partial = `qty=n` (both exist) | Same, via bundle FK | Whole only; **partial impossible** without breaking the one-owner rule |
| New tables | **0** (optional 1 additive column) | 1 (+ per-stage quantity children) | 1 + exclusive constraint |
| Data migration | **None** (additive only) | Backfill Bundle rows for all history | Backfill + resolve existing multi-holder rows |
| Cross-stage identity | Stable (adda+colour+size); quantity per stage via existing snapshot | Must add per-stage quantity or child rows = **reinvents StagePoolSnapshot** | Same problem, worse |
| Fits owner's "partial optional" | **Yes, natively** | Yes | **No — contradicts it** |
| Blast radius | UI + 1 flag + read-model + 1 form fix | +migration, +model, +settlement re-point | Large; also wrong for partial |
| Money/extensibility already-passing | **Preserved untouched** | Risk of re-pointing settlement to bundle | Risk |

**Recommendation: Option B.** Rationale as a 10-year-maintainability call: a garment stage
pipeline inherently re-pools each stage's *good* output (defects drop between stages), so a
bundle's quantity is **per-stage, not global**. `StagePoolSnapshot` already models exactly that.
A persisted global Bundle row (C) would need per-stage quantity columns/children — i.e. it would
**rebuild the snapshot it already has**, adding a table, a migration, and a second source of
truth for the same number. The clean invariant is: **Bundle = stable identity (adda + colour +
size); quantity is always derived from the current stage's pool; allocation is a WSA slice.**
Option B encodes that with the least moving parts and the least risk.

## 4. Bundle model (Option B)
- **Definition.** A *Manufacturing Bundle* is the tuple **(Adda, colour, size)** — a stable
  business identity that flows through every downstream stage. It is **not a new table**; it is
  projected by a new `bundle_service`.
- **Per-stage quantity.** At any consuming stage, a bundle's numbers come from the existing pool:
  `total = pool_good(colour,size)`, `assigned = Σ active WSA(colour,size)`,
  `available = total − assigned`, plus its `holders = [(worker, qty, mode)]`.
- **Rename the confusing object.** `CuttingBundle` (per-size container) is out of scope for the
  allocation engine; the doc/UI word "Bundle" will mean the (colour,size) identity above.
  (Optional cleanup: rename `CuttingBundle`→`CuttingSizeLot` later; not required for this work.)
- **Bundle states (derived):** UNASSIGNED (available = total), PARTIAL (0 < available < total),
  FULLY ASSIGNED (available = 0), IN PROGRESS / DONE (from contributions).

## 5. Allocation model
- **Keep `WorkerStageAllocation` as the allocation unit.** One WSA = one worker's slice of one
  (colour,size) at one consuming stage. Whole and partial are the same row type; only `qty`
  differs. Multiple WSA rows per (colour,size) = the *sanctioned* partial/multi-worker case.
- **Add `allocation_mode` (optional, additive):** `{'whole','partial'}`, default `'partial'`
  for back-compat. Stored for audit/UX clarity ("whole bundle" vs "40 of 100"); the numbers stay
  authoritative from `allocated_quantity`. (If we prefer zero schema change, `mode` is derivable:
  `whole` iff the allocation took the entire remaining at creation — but storing intent is
  cleaner and cheap.)
- **Invariant (unchanged, already enforced):** `Σ active allocations ≤ pool_good` per (colour,
  size). This is what makes partial safe and whole exact.

## 6. Whole allocation workflow (default)
1. Manager: Stage → Worker → Bundle (from the **unassigned/available** list).
2. Mode defaults to **Whole**; no quantity input.
3. Assign → `allocate(qty = available(bundle))` → one WSA with `mode='whole'`.
4. Bundle's `available` → 0 → it **disappears** from the available list.
   (If a bundle was already partially assigned, "Whole" grabs the *remaining*, which is the
   correct, unsurprising behavior.)

## 7. Partial allocation workflow (optional)
1. Manager toggles **Partial**.
2. UI shows "Pieces to Allocate" with the current **remaining** as the max.
3. Assign → `allocate(qty = entered)` (`mode='partial'`), refused if `> remaining` (already
   enforced). Remaining stays visible for the next worker.

## 8. Database changes
- **Additive only:** `WorkerStageAllocation.allocation_mode` (CharField, choices whole/partial,
  default 'partial', not null). One migration, no data backfill needed (existing rows = partial,
  which is truthful).
- **No** new tables. **No** change to APSCPB, StagePoolSnapshot, WorkerStageContribution,
  StageWorkAssignment, settlement, or cost tables.
- **Optional later:** a CHECK/partial-unique is *not* added (partial requires multiple rows per
  dim); pool integrity is enforced in the service under the advisory lock (already correct).

## 9. Model changes
- `WorkerStageAllocation`: + `allocation_mode`. Add helper `is_whole`.
- New **`bundle_service.py`** (read-model, no model): `bundles_for_stage(consuming_sr)` →
  list of bundle dicts (identity, total, assigned, available, holders, state); `bundle(...)`
  for one. Pure projection over `pool_service` + WSA. No writes.
- No other model changes.

## 10. Migration strategy
1. One additive migration for `allocation_mode` (default 'partial').
2. **No historical rewrite.** Existing WSA rows remain valid and correct.
3. Flipping `ENFORCE_ALLOCATION_BOUND` on (or removing it) is gated by
   `preview_bound_violations` — run it, clear any over-bound rows, then enforce. In our world
   only DEV/FAT data exists, so this is trivial; there is no production data at risk.

## 11. Allocation engine
- `pool_service.allocate` stays the single writer; add a thin `allocate_whole(consuming_sr,
  worker, *, actor, color_id, size_id)` = `allocate(qty=available(...))` stamping `mode='whole'`
  atomically under the existing pool lock (no TOCTOU: compute-and-write inside the lock).
- `void_allocation` unchanged (append-only reassignment, post-report guard).
- Everything remains handler-generic — the engine never learns stage names.

## 12. Reporting engine
- **Remove the flag gate** in `check_allocation_bound` → **always hard-enforce**
  `Σ(good+alter+missing+damaged) ≤ Σ allocated` per reported dim; a reported-but-unallocated
  (colour,size) → refused. (Logic already written and correct.)
- **Enforce at submit**, not only at complete, so the worker sees the error immediately (better
  UX than the current complete-time-only check).
- **Fix pair validation:** `contribution_schema` / `_parse_lines` validate the **(colour,size)
  pair** against the worker's allocations, not flat colour/size lists (closes gap E).
- Retire `bound_soft_warning` (superseded by hard enforcement).

## 13. Worker dashboard — "My Assigned Work"
- New per-bundle read (from `bundle_service` filtered to the worker): each row = **Bundle
  (colour/size) · Allocated · Completed · Remaining · Expected Earnings**. One entry per active
  WSA; whole and partial both appear as independent items. Worker never picks bundles.
- Mobile-first (rule 11): card list, tap a bundle → its report form.

## 14. Manager dashboard — allocation screen
- Rebuild the stage panel allocation form to: **Stage → Worker → Bundle (unassigned/available
  list) → Whole | Partial → [qty if partial] → Assign**, showing **Remaining / Already Assigned
  / Available** per bundle. Assigned/whole bundles drop out of the list live.
- Super-admin snapshot per completed stage (worker × bundle × good × defects × earning × time)
  already exists via contributions; surface it on this screen.

## 15. Manufacturing cost
- **Unchanged.** Cost freezes on `AddaStageRecord` (`cost_method × cost_quantity`) at advance;
  it does not read allocations. Whole/partial allocation has zero effect on manufacturing cost.

## 16. Settlement
- **Unchanged.** Earnings = reported **good** × frozen rate at `finalize_adda_settlement`, read
  from contributions, never from WSA. Whole vs partial changes *who reported what*, not the money
  path. Settlement stays the only money boundary. (This is why the redesign is money-safe.)

## 17. Future-stage extensibility
- **Preserved and required.** All new logic lives in the generic pool/allocation/report layer
  and `bundle_service`; **no stage-name conditionals**. A new stitching stage (Elastic Stitch,
  Double Needle, Pocket Attach, Button Machine…) = add a `Stage` row + `WorkflowStage` with
  `allocation_dimensions=COLOR_SIZE`; allocation, whole/partial, reporting, validation, worker
  dashboard, earnings, settlement, cost all work unchanged. This is an **acceptance gate** for
  the build.

## 18. Backward compatibility
- Additive column only; existing WSA rows read as `partial` (truthful). Existing contributions,
  settlements, costs untouched. Single-lane and multi-lane addas unaffected. The C-2 lane-aware
  report fix stays. Turning the bound hard is the only behavior change for existing flows —
  gated by the preview/clear step.

## 19. Implementation phases (each: build → browser test → tests → STOP for approval)
- **AE-1 Backend hardening (no UI):** un-gate hard bound + enforce at submit + pair validation +
  `bundle_service` read-model + `allocate_whole`. Regression tests for whole, partial,
  over-report block, pair block.
- **AE-2 Manager allocation UI:** Stage→Worker→Bundle→Whole|Partial→Assign; unassigned list;
  remaining/assigned/available. Browser-certified mobile+desktop.
- **AE-3 Worker "My Assigned Work":** per-bundle dashboard + per-bundle report entry.
- **AE-4 `allocation_mode` field + super-admin stage snapshot polish.**
- **AE-5 FAT resume:** re-run Phase 1A cert (whole default, partial optional, hard over-report,
  no split unless partial-chosen) + continue past Cutting → Settlement.

## 20. Regression strategy
- New `TransactionTestCase` + `TestCase` suite: whole assigns full & hides bundle; partial
  leaves remainder; second whole on a partial grabs remainder; over-report (good and good+defect)
  hard-blocked at submit and complete; unallocated-pair blocked; void frees qty; multi-bundle
  worker; **a synthetic NEW stage proves zero-logic-change extensibility**; golden settlement
  values (₹344.25/₹801/₹633) byte-identical (proves money path untouched); full battery green.
- `preview_bound_violations` run before enabling hard bound. Browser E2E on 3-PATTI (whole +
  partial) + one Nikkar-class check. Mobile/tablet/desktop verification (rule 11).

---

## Open decisions for the owner
1. **Approve Option B** (adapt & harden) vs Option C (persisted Bundle table)? (Recommend B.)
2. Store **`allocation_mode`** explicitly (recommended) or derive it (zero schema change)?
3. **Whole grabs remaining** on an already-partially-assigned bundle — OK? (Recommended;
   alternative: Whole only offered when bundle is fully unassigned.)
4. Reuse **3-PATTI-013** for the AE-5 FAT resume, or a fresh cert adda?

## Owner decisions (received 2026-07-20)
1. **Option B approved** (no persisted Bundle table; WSA-based; bundle read-model).
2. **Store `allocation_mode` explicitly** — done (`WorkerStageAllocation.allocation_mode`, migration 0052).
3. **Whole grabs the remaining** on a partially-allocated bundle — implemented in `allocate_whole`.
4. **Fresh cert adda** for the FAT resume (3-PATTI-013 kept as failed-cert evidence).
Clarification: Whole = default workflow; Partial = explicit exception. Bound is HARD, no flag.

---

## ✅ AE-1 COMPLETE (backend hardening, no UI) — 2026-07-20, awaiting owner approval for AE-2

Shipped (build → browser → tests):
- `WorkerStageAllocation.allocation_mode` {whole,partial}, default partial (migration prod **0052**, additive).
- `pool_service.allocate_whole` (qty=available, mode=whole, atomic under pool lock, grabs remainder, refuses empty); `allocate` gains `mode` param (explicit partial).
- `check_allocation_bound` **HARD + always-on** — `ENFORCE_ALLOCATION_BOUND` flag RETIRED (removed from settings + verification declaration + assertions); refuses over-report AND unallocated-(colour,size)-pair; **producer stages (no upstream) skipped**.
- `_parse_lines` + handler `contribution_schema` expose/validate `allowed_pairs` (closes flat-list gap-E early with a precise message).
- `bundle_service` read-model (no table): `bundles_for_stage`/`unassigned_bundles`/`worker_bundles`.
- Soft-warning retired from the report view (owner: no warning mode).

Verified:
- New `test_ae1_bundle_allocation.py` 10/10 (whole, whole-grabs-remainder, whole-on-empty-refused, partial, within-bound OK, good-over refused, good+defect-over refused, unallocated-pair refused, schema pair validation, bundle read-model).
- Focused pool/op1/golden/p19a battery 95/95; full production+expense suites **886/886**; verification flag test updated + green.
- Obsolete tests updated: FlagOffTests deleted; preview tests re-pointed to historical-audit; op1 soft-warn → hard-block; verify-cap → reported-good cap.
- **Live on dev server (browser):** worker over-report 9 vs 4 allocated → HARD REFUSED ("only 4.00 is allocated"), task stays in_progress. Previously accepted (FAT residue).
- Pre-existing unrelated: 16 verification dev-world tests error on `Missing staticfiles manifest entry for storefront/vendor/gsap.min.js` (uncommitted homepage GSAP WIP, commit bb2d9358; vendored gitignored) — NOT caused by AE-1; flagged for the storefront stream (run collectstatic / commit vendor).

## ✅ AE-1 approved by owner (2026-07-20). Commit held until AE-2 done (owner: minor backend adjustments may arise).

---

## ✅ AE-2 COMPLETE — Manager Allocation UI (2026-07-20), awaiting owner approval for AE-3

### What shipped (UI + the small backend the UI needed)
- **Whole-first allocation panel** ("Allocate bundles") on the generic stage panel
  ([_stage_panel_generic.html]). Flow = **pick worker once → tap "Assign whole →" per bundle**.
  Partial is a per-bundle **"Partial…"** reveal (quantity box, hidden until chosen) — never
  competes with the primary action. The default submit is WHOLE.
- **View** ([generic_stage_views.py] `GenericStageAllocateView`): `mode=whole` →
  `pool_service.allocate_whole` (no qty); `mode=partial` → `pool_service.allocate(qty)`. Bundle
  identified by `dim_pair="colorpk:sizepk"`.
- **Bundle cards** show Colour · Size · **Remaining / Total left** + current holders (with a
  `partial` tag). **Live board** below: Colour · Size · Total · Assigned · Remaining · Holders,
  each holder with an inline **void ×** (returns qty to the pool).
- **Worker context** in the picker: "FAT Overlock Worker 1 — holds 1 bundle · 100 pc" so the
  manager can balance load at a glance (`alloc_workers` in `views_ctx`).
- **Backend adjustment found via the UI:** `bundle_service.bundles_for_stage` resolved
  colour/size labels only from holder rows → an UNASSIGNED bundle showed "—". Fixed to resolve
  labels from the dim ids directly (bulk lookup). Added `wsa_id` to holders for the inline void.
- **Validation, graceful:** no-worker → JS guard blocks + inline "Pick a worker first" (service
  also refuses); partial `<input max=remaining>` → browser blocks over-entry client-side
  ("Value must be less than or equal to 60") AND the service refuses; negative/zero refused by
  `min` + service. Whole-on-empty refused with a clear message.
- **Mobile/tablet (rule 11):** allocation cards stack, full-width 44px touch targets, no page
  horizontal scroll at 390px; the reference board scrolls inside its own `out-wrap` container.

### Browser evidence (live dev server, demo adda FAT-AE2-001: Black/M=100, Blue/L=80, Red/Free=60)
- Screenshots: `ae2_desktop.png` (panel), `ae2_alloc.png` (bundle cards), `ae2_board.png`
  (populated board + graceful over-entry), `ae2_mobile.png` (390px), `ae2_tablet.png` (768px).
- Executed end-to-end: **Whole** — Black/M 100 → ov1 (`mode=whole`). **Partial** — Blue/L 30 →
  ov2 (`mode=partial`, tagged). **Whole grabs remainder** — Blue/L remaining 50 → ov3
  (`mode=whole`). **Multi-worker on one bundle** — Blue held by ov2(30)+ov3(50). **Invalid** —
  Assign with no worker → blocked + hint; Red partial 999 → client max + server refusal, Red
  stays 60/0. Board reflects every change live; per-holder void present.

### Tests
- Focused battery **46/46** (ae1, op1_operations, op1_hardening, s4_allocation, gap1_pool);
  updated `test_allocate_and_void_endpoints` (whole+partial modes) and the panel-lens needles
  for the renamed panel. Full production+expense green from AE-1 stands (allocation-path
  behaviour additive).

### Known issues / recommended improvements (for AE-3+ or owner note)
1. **One reload per assign** (server-rendered). Acceptable + reliable; if the owner wants
   zero-reload multi-assign, an AJAX enhancement is a later polish (not required by the brief).
2. **Board on mobile** scrolls horizontally inside its container (allowed by rule 11); could be
   converted to stacked cards in a future pass if preferred.
3. FancySelect wraps the worker `<select>` — worked in-browser via the native select; noted so
   AE-3's worker dashboard reuses the same pattern.

### Not committed yet (owner holds the commit until AE-2 reviewed).

## ✅ AE-2 approved by owner (2026-07-20). Commit still held (worker workflow is part of the same experience).

---

## ✅ AE-3 COMPLETE — Worker "My Assigned Work" (2026-07-20), awaiting owner approval for AE-4

### 1. UI review
- **Dedicated screen** `production:my-work` (`/production/my-work/`, sidebar item seeded for
  worker+manager via accounts migration 0019). One **independent card per bundle** across
  every in-progress Adda: Colour · Size · status badge (Ready/In progress/Done) · Adda + stage
  context · Allocated / Completed / Remaining / Expected ₹ · progress bar · one big CTA
  (Start / Continue / View report). Mobile-first, 48px CTAs, no page h-scroll at 390px.
- **Workload summary** (owner extra requirement) at the top: Active bundles · Allocated ·
  Completed · Remaining · Expected earnings · Current stage(s).
- **Per-bundle report** (`?color=&size=`): the card opens the report LOCKED to one bundle —
  "YOUR BUNDLE: Black · M" header, colour/size fixed, **only quantity fields**, no "add line",
  no bundle/colour/size choosing. Falls back to the full form if the pair isn't the worker's.

### 2. Browser evidence (live, demo adda FAT-AE2-001)
Screenshots: `ae3_mywork_mobile.png` (dashboard 390px), `ae3_report_mobile.png` (locked bundle
report), `ae3_mywork_done.png` (all cards Done). Executed:
- Dashboard lists ov1's 2 bundles + summary; worker taps a card → scoped report.
- **Whole bundle** report (Black/M) submitted → live progress updated.
- **Multi-bundle** worker: reported Black/M → task stayed OPEN ("1 more bundle to report");
  reported Red/Free (last) → **task completed with BOTH contributions**. Neither bundle orphaned.
- Cards flip to **Done · View report** once the task locks (no misleading "Continue").
- **Isolation**: ov2 sees only their own bundles; opening ov1's bundle URL falls back to ov2's
  own options (can't scope or report another worker's bundle).

### 3. Worker experience review
The worker never thinks about colour/size/bundle/allocation — they open a card and type numbers.
Multiple bundles are fully independent (report in any order; the stage task auto-completes only
when every allocated bundle has a report). Live progress + expected earnings after each submit.

### 4. Validation review
- Over-report **hard-blocked** in scoped mode (immediate, per-bundle: `report_bundle` refuses
  `good+alter+missing+damaged > allocated` before saving) — verified by test + design.
- Unallocated/other-worker bundle: scope falls back to the full worker-only form; `_parse_lines`
  pair-check + the C-2 option guard refuse a forged pair; another worker's task is unreachable.
- Negative/zero refused by the service; tampered params → safe fallback (no 500).

### 5. Backend added (the small backend the worker UX needed)
- `worker_task_service.report_bundle` — per-bundle upsert (replaces only that (colour,size) line,
  keeps the others), immediate per-bundle bound, completes the task ONLY when all allocated
  bundles are reported. (The full multi-line save+complete path is unchanged.)
- `bundle_service.my_assigned_work(user)` (cross-Adda cards + summary); `worker_bundles`
  progress now counts the worker's own reported good (display) + marks all bundles `done` once
  the task is locked.
- `WorkerReportView`: `_scope_to_bundle` (trims schema to the `?color=&size=` pair), single-bundle
  form_lines shows only that bundle's saved line, `_report_url` preserves the scope on POST-back.
- Template: locked-bundle header + quantity-only form + no add-line in single-bundle mode.
- No model changes (all reads); one data migration (sidebar item).

### 6. Known improvements (for later / owner note)
1. The stage task is still one row per (worker, stage); "complete only when all bundles reported"
   is the chosen semantic. A future option is one-task-per-bundle for fully independent
   completion — not needed now, flagged for the record.
2. Submit uses a confirm() dialog + one reload (server-rendered); fine on tablet.

### 7. Regression results
- New `test_ae3_my_assigned_work` **7/7** (dashboard list + summary, page render, live progress,
  single-bundle lock + no add-line, scoped submit, bad-param fallback, over-report block).
- Full **production + expense suites 893/893** green (886 AE-2 baseline + 7 AE-3).

### Not committed yet (owner holds the commit through the AE series).

## ✅ AE-3 approved by owner (2026-07-20). Commit still held.

---

## ✅ AE-4 COMPLETE — Super-Admin Production Snapshot (2026-07-20), awaiting owner approval

### 1. UI review
Dedicated management screen `production:adda-snapshot` (`/production/addas/<code>/snapshot/`,
linked from the Adda detail hero for management). Per pool stage, three reconciling views:
- **Stage totals** strip (7): Bundles · Whole · Partial · Workers · Allocated · Completed · Remaining.
- **Per-bundle rollup**: Colour · Size · Total · Assigned · Unassigned · Completed · Progress bar
  · Holders (each with a whole/partial tag).
- **Per-worker×bundle allocation detail**: Worker · Bundle · Mode · Allocated · Completed ·
  Remaining · Expected ₹ · Status · Started · Updated.
Answers the owner's four questions at a glance — who owns what, who's completed what, what's
pending, what's unassigned. Tables scroll inside their own container (rule 11); totals grid
stacks on mobile (no page h-scroll at 390px). All fields the owner listed are present.

### 2. Browser evidence
Screenshots `ae4_snapshot_desktop.png` + `ae4_snapshot_mobile.png` on FAT-AE2-001 (Panel Join:
3 bundles, whole+partial, 3 workers, one bundle 40% complete). Access: **super-admin 200,
manager 200, worker 403** (verified live + test).

### 3. Data accuracy review — every number cross-checked vs DB truth
`stage_snapshot` totals vs direct DB aggregates on FAT-AE2-001: Allocated 210 ✓, Whole 2 ✓,
Partial 2 ✓, Workers 3 ✓, Completed 70 ✓, Remaining 140 ✓, Unassigned 30 ✓ — all match. Per-bundle
Assigned/Available/Completed/Progress and per-allocation Allocated/Completed/Remaining/Expected₹
reconcile (e.g. ov1 Black/M whole 100, completed 40, remaining 60, expected 40×₹5 = ₹200.00).
Expected ₹ reads the already-frozen `expected_earning` (no new money math). Test asserts the
same reconciliation on an independent fixture.

### 4. Performance review
One `stage_snapshot(sr)` = a bounded set of queries (bundles via pool_service + one WSA fetch +
one WSC fetch + one task map) per stage; the view iterates only the Adda's pool stages
(allocation_dimensions != NONE). No N+1 across addas (Adda-scoped page). Fine for factory scale.

### 5. Backend added
`bundle_service.stage_snapshot(sr)` (read-model: bundles + allocations + totals);
`AddaSnapshotView` (management-gated); URL + Adda-detail link. No model changes; no migration.

### 6. Regression results
New `test_ae4_snapshot` 6/6 (totals reconcile, bundle rollup, allocation detail incl. expected₹
+ status + times, management-only access, page render). Full **production + expense 898/898** green.

### 7. Recommendations
- When AE-5 creates the fresh cert adda with multiple pool stages, the snapshot will list each
  stage section automatically (generic) — re-verify there.
- Optional later: a top-level "all in-progress addas" production board linking to each snapshot
  (this AE-4 screen is Adda-scoped, which matches "operational control for one Adda").

### Test data note
Verified on FAT-AE2-001 (the AE-2/AE-3 demo adda). AE-5 uses a FRESH cert adda per owner
decision #4.

## ⏸ STOP — AE-4 done + browser-tested + data-accuracy-verified + battery green.
Awaiting owner approval. **Per owner: after approval we review the full AE-1→AE-4 diff together,
then a single clean implementation commit, then the FAT resumes from Cutting (AE-5).**
