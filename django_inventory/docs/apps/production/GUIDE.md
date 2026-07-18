---
id: apps-production-guide
type: app-guide
status: active
owner: handwritten
scope: production
anchors: config/production/
verified: 2026-07-13
---

# production app — file-by-file GUIDE

> Business view: [config/production/README.md](../../../config/production/README.md).
> Sabse bada app: Adda lifecycle, stages, worker truth, costing freeze.

> **📦 MODULE 9 INVENTORY VERIFIED (2026-07-11)**: architecture correct — ownership split holds (raw_materials=roll master/intake/status/denorm-remaining · production=consumption truth (LayeringRollEntry verified width/weight + remnant records) · tracking=roll history · costing=cost_per_kg intake). LOWER-002 material fully reconstructable (intake 25kg → verified 36"/25kg → 40 layers × 1.10m → 2.5kg remnant → per-field-audited history). Stock cannot go negative (roll-grain statuses + CHECK constraints); manual edits audited per field. **FIX (M3-class): RollUpdateView + RollAssignView → new raw_materials ManagementRoleMixin — workers could mutate stock+cost truth via direct URL (sidebar covers only menu URLs); test_m9_roll_gates.** Recorded (owner decisions, not built): remnant RE-ISSUE (leftovers visible but not issuable as stock — owner's Q12 suggests future want) · no roll-damage status (not_used/used only) · CR-000001 phantom reset = pre-hardening dev data, every CODE path logs.

> **📱 MODULE 8 TRACKING VERIFIED (2026-07-11)**: architecture FROZEN untouched (review verdict: no gap — absorbed streams+append with zero tracking changes; LOWER-002 fully reconstructable). ONE presentation wire shipped: `update_piece_status` view (`tracking:scan-status`, POST-only, PRODUCTION_ROLES) + one-tap 44px status buttons on scan_detail — mark_status finally has its UI caller (was zero callers). Verified live: dashboard totals w/ appended ranges · list/print (84 QRs incl. 81-82) · scan resolve + lazy row + status lifecycle on phone · Adda/Roll history · CSV/XLSX/PDF exports + re-download (EXP codes; concurrent-mint limitation pre-documented, floor-scale fine) · 404 honesty · role probes (worker: dashboard blocked, scan allowed by design; exports-list reachable = recorded with the parked A360-class finding). ScanStatusButtonTests green.

> **🔒 IDENTITY LAW + APPEND GENERATION (Module 7, 2026-07-11)**: "Identity is meaning-blind; meaning lives on the lane" (tracking/README.md + PLATFORM_STATUS §8b). `assembly.append_uncovered_batches` = per-(size,color) deficit coverage from Max(end_seq)+1; join branch auto-appends when batches exist (late/recut lanes get identities the moment they exist); BarcodeBatch unique moved (adda,color,size)→(adda,start_seq) (tracking 0017); rec.total_barcodes synced; barcodes_generated event carries lane labels+reasons; **no-memory rule enforced** (post-join lane never regresses the pointer — live defect fixed + LateLaneNoRegressTests). test_barcode_append 7/7.

> **🔀 CUTTING STREAMS REDESIGN SHIPPED 2026-07-11** (frozen arch: docs/PRE_PRODUCTION_ARCHITECTURE_FINAL_REVIEW.md + CUTTING_STREAM_LIFECYCLE.md): `CuttingStream` (adda.py — identity-only lane rows (adda, fabric_group, sequence); derived at Adda creation from patterns_ai's `FABRIC_GROUPS_PROVIDER` registry #5, fail-closed 1 lane) · `AddaStageRecord.stream` nullable FK w/ CONDITIONAL uniques (per-lane WHERE stream NOT NULL · classic WHERE NULL) · migrations **0050/0051** (backfill: 1 'body' lane per existing adda) · `adda_service`: `resolve_stream` (None→single lane; zero lanes→auto-provision; >1→specify) + `lane_stage_record` (Q lane|NULL + ADOPT legacy rows; order_by('stream_id') never 'stream') + `_finalize_stage_record` (extracted leave-work: PAY-2 → C3 → freeze → resolve → pool → COST_FROZEN) + `advance_lane` (JOIN = every blocking lane's CUTTING SR complete — frozen §3; pointer forward-walks, never regresses) · trio services (layering/cutting_pattern/cutting) all take `stream=`; guards are LANE-truth not pointer-equality (roll attach = any open layering SR — raw_materials/roll_service) · views: `_request_stream` + ?stream= threading + lane switcher chips + form lane-injector (at partial END — top placement leaks script text) · `assembly.generate_for_adda` = ONE pass over all lanes' APSCPB at THE JOIN (per-record loop double-generates) · `_materialize_breakdown` BREAKUP-FIRST (bundle FK None by design; bundle path = legacy fallback) · barcode stage reads APSCPB adda-wide · A360 lane cards (mgmt-only, >1 lanes) · mixins stage-assignment = ANY lane · `test_streams.py` 9 laws. Proof: DEV-NICKAR-001 two lanes end-to-end, join held→fired, one sequence 1–60 across fabrics; suite **551/551**. Deferred (honest): adda-level bundle-slip screen · pattern-console injector · Pattern-Design UI simplification · Add-lane button (lifecycle §10).

## models/ (split by domain — har file = ek concern)
| File | What lives here | Pattern / why |
|---|---|---|
| `core.py` | Product, Stage (library), **StageCategory + MachineType (R10-A config masters)**, WorkflowStage (+RoleRate), AddaStageRoleRate, RateCorrectionAudit, AllocationDimensions, StagePoolSnapshot, WorkerStageAllocation | WorkflowStage = per-product POLICY row (order, cost_rate dual-duty ADR-0009, credits_workers, cost_billed_at grouping; **S4/D1 `allocation_dimensions` = piece-pool grain, POOL-ONLY, orthogonal to credits_workers/cost_method**). AddaStageRoleRate = frozen resolved payable rate (S1; snapshot at stage-start, locked at first completion, per (stage_record,role)). RateCorrectionAudit = append-only re-rate audit (S1.1). Product.clean() = F1 guard (R1 2026-07-04): code IMMUTABLE once Addas exist (PDD §31.1-F1). **R10-A (migrations 0045/0046): Stage.work_type{manual|machine}+machine_type+category (pair CheckConstraint = frozen rule 4; owner defaults seeded; category = display-metadata ONLY, fence-tested). R10-C (0047): StageCategory.is_active + owner CRUD for StageCategory/MachineType (access_views master views + master_list/master_form templates; Stage-library header links; pickers = ACTIVE rows; no-static-options pinned)** |
| `adda.py` | Adda, AddaStageRecord (+ pending_report_workers helper) | SR = stage ka polymorphic parent; processing_cost frozen (honest-NULL) |
| `worker_task.py` | WorkerStageTask, WorkerStageContribution | THE production truth (ADR-0005, C-TM); partial-unique active task; settlement_line provenance string-FK. **S3: good/alter/missing columns (good NOT NULL = payable; alter/missing immutable observations); reported dual-written = good (renamed-not-dropped @S6); constraint wsc_gam_nonneg_sum_positive** |
| `layering.py` | LayeringRecord, LayeringRollEntry, RemainingClothOfClothRoll | per-roll verify + MANDATORY leftovers (G1 ke facts) |
| `cutting.py` | CuttingRecord, ProductSize, PatternVerification, PieceBreakup, Bundle(+items), ProductPattern | cutting = first real quantities; breakup = expected denominators |
| `barcode.py` | BarcodeGenerationRecord | archetype-E stage record |

## services/ (ALL writes — views kabhi nahi)
| File | Role |
|---|---|
| `worker_task_service.py` | ★ chokepoint: WST/WSC sole writer, expected freeze, verified qty (P1), auto-cancel resolve. **R10-B: report lines accept optional alter/missing observations (S3 columns; good stays the ONLY payable — D2)** |
| `adda_service.py` | Adda create (race-safe per-product counter; **F-2 polish 2026-07-05: NO auto-assign — empty roster, manager assigns via panel; spec-D6 no-skilled-users guard retained; C-1 closeout: the retro-tag other-half `sync_layering_workers_for_skill` is REMOVED from layering/service — manager assignment = the ONLY roster source, PDD amendment 4**) + stage advance |
| `cost_service.py` | processing_cost freeze/clear; `role_rate_for` (grouped-member guard C-1); **`effective_pay_rate` = THE F2 chokepoint: grouped→0 AND (A360 follow-up 2026-07-05) non-payable `credits_workers=False`→0 — one rule at freeze/rerate/settlement/dashboards** |
| `flow_service.py` | WorkflowStage CRUD + grouping guards |
| `stage_rate_service.py` | ★ sole writer of AddaStageRoleRate: snapshot/freeze/lock/edit + `rerate_stage_role` (S1.1 super-admin correct-until-settlement + recalc + RateCorrectionAudit). **F1: rerate joins settlement advisory lock 5374. F4: `refloat_rates_on_reopen` (re-resolve+unlock, symmetric w/ cost). cost_service.`effective_pay_rate` = F2 grouped→0 structural guard.** |
| `pool_service.py` | ★ S4/P2-P5: THE piece-pool chokepoint — sole writer of StagePoolSnapshot + WorkerStageAllocation. `pool_good`/`materialize_stage_pool`/`clear_stage_pool` (snapshot) + `allocate`/`void_allocation`/`available` (draw-down, D2 advisory lock 5375) + `check_allocation_bound` (P4 complete-time Σ(good+alter+missing)≤allocated, `ENFORCE_ALLOCATION_BOUND`) + `preview_bound_violations`/`bound_soft_warning` (S5 rollout safety). POOL-ONLY, decoupled from cost/rate/settlement |
| `_shared.py` | auth helpers + ★ reopen_stage_record skeleton (settled-block + **S4/P5 `_downstream_consumer_guard`: refuse reopen if any downstream stage has a non-voided WorkerStageAllocation or completed contribution; + `clear_stage_pool` wiring; F4 rate re-float**) |
| `access_service.py` | skill-gating reads + **`eligible_stage_workers(stage_code)` = THE shared picker population (F-4: active ∩ Stage.access_by_skill — picker == gate; all 4 stage start-forms use it)** |
| `activity_service.py` | timeline UNION reads |
| `costing_views.py`/`costing.html` +RMX-D | **Model-B completion (2026-07-18): Material (net) + Full Cost (ADR-0009) columns + the full-cost hero tile — every value pass-through from `full_costs_for_addas` (the view calculates nothing; grand line = presentation-sum, documented); per-row unpriced-incomplete flags; perf pin 11→16 conscious (+5 = the assembly's constant query set)** |
| `cost_service.py` +RMX-C | **Phase 17 read-paths (2026-07-18, charter = PDD entry 8; READ-ONLY, zero writers):** `material_costs_for_addas` (bulk arm = the M13 derive's rules as 3 grouped aggregates; NullIf parity for the verified-weight-0 quirk) · `material_cost_for_adda` now DELEGATES (one valuation implementation; original loop = the parity test's reference, `tests/test_rmx_read_paths.py`) · `full_costs_for_addas`/`full_cost_for_adda` (THE Decision-2 assembly, extracted from a360 — one assembly, consumers: A360 [switched INERT, panel values byte-equal] + the costing surface at RMX-D) · `material_consumption_in_period` (the derive law time-sliced: +entries −remnants +leftover-ins at source price; Σperiods ≡ ΣAddas ≡ intake-once, test-pinned) |
| `operations_digest.py` | pure reads: the management morning-pulse (`operations_digest` = 6 tiles) + the SINGLE stalled/pending paths shared with their drill-downs (H-2B/F-3 reconcile-by-construction). **G-4 (BOD-C 2026-07-18, owner-gated): `adda_status_counts` + `stage_breakdown` — the Adda-dashboard KPI/chips reads extracted VERBATIM (one calculation, two consumers: the page + the BOD tiles); INERT proven in `tests/test_g4_status_reads.py`. BOD-D: `adda_status_counts(fields=)` optional subset — same expressions, one calculation site, dashboard call unchanged (parity-pinned)** |
| `product_service.py` / `product_size_service.py` | masters |
| `reconciliation_service.py` | (expense app) settlement reconciliation: `reconcile_stage_pay` + `SETTLEMENT_WARN_FLAGS` (over_allocated); S5 M-6 finalize BLOCK lives in `adda_settlement_service` (`ENFORCE_SETTLEMENT_RECONCILIATION`) |

## stages/ — the OPEN-CLOSED engine
`base/handler.py` (contract: typed record, complete validations,
cost_quantity, contribution_schema) + `base/registry` + per-stage packages
(layering/cutting/cutting_pattern/barcode_generation each = handler + service;
barcode_generation/export_service = V1.1 Item 3 2026-07-12 MANAGEMENT_ROLES
backstop `_ensure_management_role` on all export fns — [docs/tracking/EXPORTS.md](../../tracking/EXPORTS.md)).
NAYA STAGE = naya package — **ya R10-B se: koi package hi nahi. `generic_stage/` = THE config-only archetype (good/alter/missing schema, work-type-aware admin_snapshot incl. machine holders, generic start/complete/reopen endpoints — **campaign-M6 fix 2026-07-11: `reopen_generic_stage` gained the missing `@transaction.atomic` (shared skeleton locks via select_for_update; siblings already atomic; first live generic reopen 500'd) + 2 regression tests in test_r10b_generic_stage**); `base/registry.get()` FALLBACK serves any active Stage row without a bespoke package. views/presentation.py = category-grouping single seam (StageCategory = presentation truth).**
**GAP-2 fix 2026-07-11 (production-hardening #1, cutting/service.py):** the
two COMPLETION validations in `complete_cutting_from_bundles` are now
LANE-scoped — `_pattern_record_for_adda(adda, stream=lane)` (size
allocations) + `_get_layering_record_for_adda(adda, stream=lane)` (roll
colors). Before: lowest-stream_id record validated EVERY lane ⇒ a
cross-fabric lane (cream trim vs navy body rolls) could NEVER complete
("Color … not in layered rolls" — found live on NKS/SHA audits, masked in
the original streams proof by same-color rolls). Informational console
reads (suggestions/reconciliation, lines 424/472/504) stay adda-level by
design. Regression: `test_streams.CrossFabricCompletionTests` (full
service path, two colors, both lanes complete → join). Browser-proven on
XFB-001 (grey lane "Lane cut recorded (9 pieces)" via the console, join
fired, 21 identities across 2 fabrics).

## views/ (12 modules — parse→gate→delegate ONLY)
FILE MAPs already in code: `stage_views.py` (1.4k — layering+cutting consoles,
6 sections documented at top), `pattern_stage_views.py`, `barcode_gen_views.py`,
`worker_report_views.py` (★ phone report + AddaReportReviewView P1; **C-3 closeout 2026-07-05: report requires active assignment AND live Stage Access — hub revocation closes the path instantly**),
`adda_views.py` (**MGT-B-1 fix 2026-07-12 (management cert): module never imported `PermissionDenied` yet both lane views' `except (ValidationError, PermissionDenied)` referenced it → ANY service refusal on add-lane/cancel-lane (e.g. mandatory-reason ValidationError, UI-reachable) crashed 500 via NameError instead of the designed error flash; fix = one import line; pins `test_management_role_certification` 3/3**; **campaign-M3 fix 2026-07-11: `AddaCreateView` → `ManagementRoleMixin` — old ProductionRoleMixin let any WORKER reach + POST the create form (create_adda has no role gate; the view is the wall); found live in browser; `test_m3_adda_gate` 2/2**; **C-2 closeout 2026-07-05: per-stage `can_open` = access ∩ assignment (mirrors StageViewAccessMixin) → iframe / 'Not assigned' / 'Restricted' cards**; R1 2026-07-04: AddaDetailView ctx adds mgmt state-aware
Settlement button target + self-scoped presentation-only "My Work" tasks —
PDD §23/§27-D7; R2: unit label from stage contribution_schema),
`flow_views.py` (R2: `credits_workers` payability checkbox on the cost form —
PDD §6/§17), `costing_views.py`, `dashboard.py`,
`product_views.py`, `pattern_views.py` (**Platform Phase 1+2 2026-07-09:
`product-patterns` = `ProductPatternsEntryView` (login-only redirect → the
patterns_ai Pattern Dashboard); `product-pattern-blueprint` =
`ProductPatternBlueprintRedirectView` (→ the patterns_ai BLUEPRINT module,
owner-approved D-1 — production only LAUNCHES the platform). Both = URL-name
reverses only, ADR-H wall intact + test-asserted across all view files.
RETIRED Phase 2: `ProductPatternsEditView` + `product_patterns_edit.html` —
its add/remove/update_count actions now live behind the atomic
`register_pattern_definition` single-writer in patterns_ai**),
`access_views.py`, `mixins.py` (RBAC +
**`embedded_advance_redirect` — F-3 polish 2026-07-05: all 4 embedded stage
COMPLETES redirect to the gate-free `production:stage-advanced` bounce page
(`StageAdvancedBounceView` + `stage_advanced_bounce.html`, data-free, login-only)
so a completing worker never lands on a 403; reopen redirects unchanged**).
R2 (2026-07-04) also: `stages/layering/handler.py` `contribution_schema`
override (workers report LAYERS); `stages/layering/service.py`
`worker_layer_reconciliation` (non-blocking Σ-reported-vs-lay_count WARN,
logged at complete + surfaced as a message by LayeringCompleteView);
`flow_service.set_stage_cost` accepts optional `credits_workers`.
R3 (2026-07-04, PDD §27-C3): `adda_service.advance_to_next_stage` carries the
C3 completion guard (blocks while workers are IN_PROGRESS — TRANSITIONAL
scope, see guard comment; super-admin override w/ mandatory reason →
`AddaHistory.COMPLETION_OVERRIDE`, audit-complete metadata);
`worker_task_service.resolve_stage_tasks_on_complete(cancel_note=)`;
override threading through the 4 stage `complete_*` services + views;
shared `_completion_override.html` partial in all 4 stage panels;
`complete_layering` now `@transaction.atomic` (was missing — half-complete
hazard fixed).
R4 (2026-07-05, PDD §27-D4): `adda_views` My Work is monthly-aware —
`viewer_is_monthly` (deferred read of `expense.payroll_service.is_monthly`)
suppresses the ₹ expectation entirely (qty + "Monthly Salary" badge instead);
the pay-basis machinery itself lives in the expense app (see its GUIDE).
**campaign-M10 fix 2026-07-11 (template-only, `adda_detail.html`):** My Work
lines now surface the CHECK result derive-at-read — `checked ✓` when
`verified_quantity` equals good, amber `checked: N passed` when management
reduced it — so a worker sees WHY settlement will pay verified-else-good
BEFORE money moves (owner M10 law: "every rupee explainable"). The Expected ₹
stays the frozen good×rate visibility (ADR-0005 — never recomputed); the
check note is presentation only. Found live: OW-A reported 30 S, verified 29,
panel showed only "30 pieces · Expected ₹170".
R8 (2026-07-05, spec docs/STAGE_TRIO_SPEC_IMPACT_2026_07_05.md): **"Cutting
Pattern" → "Pattern Design" display rename** (migration prod **0043** data-only;
identifier `cutting_pattern` FROZEN). **GENERIC stage snapshots**: handler
`admin_snapshot(adda)` (base default None) + ONE shared partial
`_stage_admin_snapshot.html` + `stage_views.prev_admin_snapshot()` — every
panel auto-shows the previous stage's reference, MANAGEMENT-gated (workers
leak-tested 0); layering + pattern producers shipped; future stages just
override. **Checklist worker report** (spec §3): pattern handler
`contribution_schema` mode='checklist' + `checklist_submit` hook (base refuses)
— phone tick-list of ProductPatternAssignments syncs the SAME
CuttingPatternVerification rows as the console (single truth), photos →
CuttingPatternPhoto, submit-all-or-refuse, ONE contribution qty=1 → FIXED pay
(rate×1, engine untouched). **WP-4**: `complete_worker_task` refuses a 2nd
completed report on a fixed_cost stage (double-fixed-pay guard). **WP-5**:
`CuttingPatternRecord.lead_minutes_from_layering` (migration prod **0044**),
stamped at pattern complete — analytics only. Recon `_classify` is now
method-aware (fixed_cost → ok/over_allocated, no more false no_output_qty).
A360 (2026-07-05, plan v2): `views/a360.py` = the per-Adda management
overview builder — READ-ONLY aggregation (progress+health via THE single
stalled predicate · timeline = filtered AddaHistory · worker board
Progress-then-Contribution with per-stage-only share (honest mixed-units
rule) + monthly/non-payable ₹ suppression · money strip reusing the
settlement-queue trio · ADR-0009 cost rows + variance); STAGE-GENERIC
(source-inspection test pins zero stage-name literals — future stages need
NO A360 change); rendered by `_a360.html` (mgmt-gated ctx, worker leak=0
tested); costing page relabeled "Standard Labor Cost" + Variance column
(P-COST fix). **NEW-STAGE CHECKLIST (the standard): register handler +
typed record + snapshot()/admin_snapshot() (+ optional contribution_schema
override) + Flow-Editor config — tiles, panels, prev-stage reference, phone
report, and A360 all pick the stage up automatically.**
R6 (2026-07-05, PDD §31.1-F6): `set_verified_quantity` emits a DB-resident
`AddaHistory.VERIFIED_QTY_CORRECTED` event (who/old/new/worker/stage; clear
= new None; no-op = no event) — closes the Phase-10 "verified-qty no-audit"
debt; `activity_service` verb_map got 'corrected verified qty' +
'overrode stage completion' (R3 label debt) rows.

> **RCP-2A hygiene (2026-07-18):** 5 orphan legacy routes REMOVED (zero references
> anywhere — pre-workspace era): layering entry-update / full-create-roll /
> remove-remaining · cutting bundle add-item / bundle item-save. Their view classes
> (stage_views.py) + `EditRollEntryForm` (sole consumer) removed with them; the
> underlying SERVICE functions stay (tested, other callers). Evidence:
> [RELEASE_CERTIFICATION_LOG](../../RELEASE_CERTIFICATION_LOG.md) §RCP-2A.

## forms/ · urls.py · templates/
forms = plain Django forms per stage (`_shared.py` = worker chips widget).
urls.py header me poora route-group map. Templates: `_stage_panel_*.html`
(operator consoles), `worker_report*.html` (phone), `product_flow.html` (editor).

## Dots kaise connect (ek request)
```
worker report POST → urls → WorkerReportView ( assignment gate )
  → worker_task_service.report_contributions/complete (WSC + freeze)
  → history via stage services · settlement (expense) baad me READS WSC
```

## Topics yahan use hote hain — kahan padhein
Har concept ka official link + "is project me kahan" mapping:
[../../LEARNING/10_ONLINE_RESOURCES.md](../../LEARNING/10_ONLINE_RESOURCES.md).
App ka business-view: README (code ke saath). Deep lessons: [docs/LEARNING/](../../LEARNING/README.md).

**GAP-5 SHIPPED 2026-07-11 (production-hardening #3 — bundle services in
their frozen post-join role, PROPOSAL §3):** all six bundle writers
(`create_bundle` · `create_bundle_with_pieces` · `add_pieces_to_bundle` ·
`add_item_to_bundle` · `add_bundle_item` · `delete_bundle[_item]`) now gate on
`adda_service.preproduction_joined(adda)` (the join predicate extracted as a
derive-at-read — same rule `advance_lane` fires on) and anchor on
**(adda, size), cutting_record NULL** (the shipped conditional unique);
consumption spans EVERY lane's breakups; cross-lane takes of one Production
Component INCREMENT the single (bundle, pattern, color) line (DB truth;
`source_breakup` blanks on a second source; **group invariant**: Σ consumed
over a (pattern,colour)'s breakups ≡ Σ bundle-line counts —
`_resync_group_consumed`, oldest-lane-first, used by manual edits/deletes of
multi-source lines). Legacy pre-streams bundles stay readable/editable via
their old anchor. **Initial join barcode generation now logs
`barcodes_generated`** (parity with the append event — final-audit note
closed). **Garment Readiness panel** (A360, management, post-join,
multi-component only): `pool_service.garment_readiness(adda)` DERIVE-ONLY —
per size each component's cut ÷ per-garment, sets, ▲ bottleneck, blocked
sizes, leftovers (count−consumed); one-tap slip `bundle_ready_sets` (
`production:adda-bundle-sets` POST) bundles exactly the complete unbundled
sets through the normal writers. Cutting console: bundle forms render only
post-join (`bundles_locked_until_join` ctx; pre-layering legacy path has no
bundle UI at all). **GAP-3 SHIPPED same session** (pulled forward — it broke
A360's own embedded tab on multi-lane Addas): `_request_stream(...,
for_render=True)` returns None on bare-URL ambiguity and both console
builders render a LANE PICKER (44px chips, reasons shown) instead of a 500;
the ambiguity refusal stays law on every POST path. Tests:
`test_gap5_bundles` (join-gate · adda-anchor · cross-lane increment ·
over-take · readiness/slip · bundle-never-truth) + legacy suites converted to
post-join semantics (test_cutting_workflow · counter_invariants ·
breakdown_materialization · barcode_generation_workflow · unified_tracking ·
tracking/test_barcode_export · expense/test_allocation_ui; A360 query pin
68→71 conscious). Browser-proven: XFB-001 one-tap "Bundled 9 sets — bundle
16 holds 18 pieces" + instant re-derive; NKS 48-set panel w/ Rib ▲ + per-size
buttons; SHA 40-set 7-component panel; picker live on bare URL + embedded tab.

**GAP-4 SHIPPED 2026-07-11 (production-hardening #5 — FINAL ledger item; battery 1479/1479):**
① **Worker lane ISOLATION** (owner UI law "he should only see Body Cycle 1"):
`stage_views._visible_lanes` + `_scope_console_lanes` — management sees every
lane; a worker sees ONLY lanes whose stage record carries their assignment
(legacy NULL-stream rows count for all, adopt-on-touch parity); sibling lane
by URL ⇒ 403 with a My-Dashboard hint; a single own lane AUTO-SELECTS (zero
lane chrome/vocabulary); the GAP-3 picker + switcher list only the worker's
own lanes. ② **Add-lane lifecycle (§1–§9 verbatim)**: sole writers
`adda_service.add_stream` (mgmt-only · mandatory reason · Adda-row lock →
Max(sequence)+1, cancelled lanes never reuse numbers · fabric group must
EXIST (new group = Blueprint change → future Addas) · blocking inherited from
the group · refuses on completed Adda) + `adda_service.cancel_stream`
(cancel-if-empty §9.4: zero SRs only · seq-1 derived lanes never · mandatory
reason). NEW history vocabulary `STREAM_ADDED` / `STREAM_CANCELLED`
(tracking migration **0018**, choices-only). UI: `adda_add_lane.html`
(confirm-with-context §9.1: existing lanes + live state before the button;
reason picks = DATA + free text) + A360 "＋ Add lane" (also on single-lane
products — recuts there are the primary use; zero-chrome law kept: lone link,
no cards) + per-card "Cancel lane" (eligible = empty ∧ seq>1, prompt-for-
reason). ③ **Cancelled lanes render GREYED with cancel_reason** (lifecycle
§7 — was filtered out); exclusions re-asserted: cancelling the empty lane
releases the join. ④ Presentation: stages-overview trio counts read
COMPLETED once the join fired (untouched non-blocking lane no longer holds
"2/3" forever) · "Settlement History" card on My Earnings/Worker Detail →
**"Payments"** (it lists cash — no accounting language). Tests:
`test_gap4_lanes` 13/13 (add/cancel laws · events · isolation 403/auto-
select/manager-sees-all). Browser: SHA-001 greyed cancelled card + "Pre
Production 3/3" · XFB-002 add-lane form → "Lane added: body (lane 2)" →
cancel via card prompt → greyed with reason, live. **HARDENING LEDGER
CLOSED — see docs/PRODUCTION_ENGINE_FREEZE.md.**

**M12 fix 2026-07-12 (views/a360.py):** the A360 cost panel now Σs EVERY
lane's stage record per stage (payable→std_labor, non-payable→
nonpayable_priced, settled per stage = Σ lanes). Before: stages_overview's
single representative SR stood in for all cycles — GLDN-001 showed
"Standard Labor ₹280" on A360 vs ₹1408 on the costing dashboard (the
read-side sibling of GAP-1/2). After: A360 ₹1244 payable-std vs settled
₹1279.25 → variance −35.25 = rerate +35.75 − verified −0.50 exactly;
costing ₹1408 = 1244 + non-payable layering 164. Query pin 71→72
(conscious, one prefetch).

**M13 COSTING 2026-07-12 (final campaign module — every rupee derives):**
① `cost_service.material_cost_for_adda(adda)` — MATERIAL cost as a pure
derive (Σ verified-kg × roll ₹/kg − remnant value; honest-NULL: unpriced
consumed rolls counted + flagged, never ₹0). A360's "Full cost" line now
renders it live: `material ₹X (net of remnant ₹Y) + actual settled +
non-payable processing = ₹FULL · ₹Z / garment (N sets)` — sets from the
readiness derive; a360.py stays stage-blind (the genericity guard forced
the derive into cost_service, where roll-consumption reads belong).
② Costing dashboard variance made LIKE-for-LIKE: columns now
`Standard Labor (payable) | Non-payable priced | Actual Settled |
Variance (payable std − actual)` — the old single-std variance mixed
non-payable layering into a vs-settled drift (GLDN: ₹128.75 'variance'
was mostly layering's ₹164; now −35.25 = rerate +35.75 − verified −0.50,
identical on A360 and the dashboard). Query pins: costing 10→11, A360
72→74 (conscious, documented in the tests). Recut cost fully answerable
by lane-scoped derive (GLDN trim lane 2 = ₹1644: material-net 1482 +
labour 158 + lay 4 + 8 appended IDs) — no new truth anywhere.

**V1.1 item-1 ROLL DAMAGE 2026-07-12 (raw_materials):** `ClothRoll.Status`
gains `DAMAGED` (migration rm **0012**, choices-only) — a WHOLE unusable
roll (water/supplier/fungus/transport) leaves available stock honestly;
every "available" read filters NOT_USED so damage self-excludes from
pickers, assign guards and counts. Sole writers
`roll_service.mark_roll_damaged` / `restore_damaged_roll` (management-only ·
mandatory reason · USED rolls refused: "record damage on the pieces/reports"
· ClothRollHistory STATUS_CHANGED rows carry the reason — soft state, never
delete). UI: roll-detail ✕ Mark damaged / Restore buttons (prompt-for-
reason), red Damaged badge, cloth-dashboard DAMAGED tile (renders only >0).
Partial damage stays the audited weight-correction + verified-at-lay path
(by design, documented in the model comment). Tests: test_roll_damage 8/8
(mgmt-only · reason · audit rows · used-refusal · picker/assign exclusion ·
restore roundtrip · view 403). Browser: GLDN-R5 marked damaged live w/
reason → badge + assign gone + tile 32/2/29/1 → history row exact.

**V1.1 item-2 REMNANT RE-ISSUE 2026-07-12:** the review verdict FIRST — the
architecture was already decided and LOCKED (C-1/ADR-0009 inside
`roll_service.consume_leftover`: remnant = a weighed PIECE attached forever
to its parent roll + source Adda; whole-piece one-shot consumption into a
DIFFERENT Adda; valued at the SOURCE roll's ₹/kg, never re-priced;
append-only; un-consume = future event, not built). What was owed = WIRING:
① `consume_leftover` now writes the consuming Adda's history (ROLL_ASSIGNED
w/ "leftover #id · N kg from SRC" note) ② the layering console gained the
"♻ Leftover cloth available" section (management-only; one 44px "Use this
leftover" per piece; confirm dialog; "Leftovers used in this Adda" list) via
`LayeringConsumeLeftoverView` (`production:layering-use-leftover`, POST) ③
`cost_service.material_cost_for_adda` counts reused leftovers at source
price (`leftover_in`) — across Addas the intake value counts EXACTLY once
(source pays consumed−remnant; consumer pays the remnant; test-pinned:
4500 + 500 = 5000). Layering ctx also exports `is_management` (the guard
had silently failed without it). Tests: test_leftover_reissue 4/4 (history
row · one-shot + never-home · exactly-once costing · console door gates).
Browser: XFB-002 console listed GLDN/LOWER pieces → "Leftover used: 0.30 kg
(GLDN-R6, from GLDN-001)" → used-list + XFB-002 material ₹58.50 (0.3×195)
+ GLDN net unchanged. A360 pin 74→75 conscious.

**V1.1 item-4 WORKER ROLE CERTIFICATION — Phase A (Production) 2026-07-12:**
full worker-surface audit of production URLs/views/templates/stage services;
report of record = [docs/WORKER_ROLE_CERTIFICATION.md](../../WORKER_ROLE_CERTIFICATION.md).
3 bugs fixed: ① `complete_cutting_legacy` was PRODUCTION-gated
(`_ensure_can_manage` name trap) — any worker could complete Cutting
(advance+barcodes+cost freeze); now MANAGEMENT_ROLES (browser-proven refusal)
② `save_layering_draft` — production role alone could tamper any Adda's
draft; now assigned ∨ helper-skill ∨ mgmt ③ `_build_cutting_context`
per-bundle allocation ₹ rows (era-A, other workers' money) now built
management-only (V2-3 own-money rule). `/production/stalled/` +
`/pending-reports/` = worker-scoped by design (no bug). Pins:
`tests/test_worker_role_certification.py` (6). Other apps = future phases.
