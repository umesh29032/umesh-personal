# P2→P3 Soak Tracker — Worker Reporting Under Real Usage

**STATUS (owner clarification 2026-06-11): PRE-SOAK READINESS PHASE.** There is no
deployed environment and no real factory users yet — the §1 criteria CANNOT be
satisfied until deployment + onboarding. Until then this document is a
**readiness checklist, not completed validation**: developer-discovered issues
go in the §2 log, parity checks keep running (check.sh gate [5/5]), and **P3
(V2-1d) stays gated**. The TRUE soak executes after deployment, with real-usage
evidence filling §4. Implication: the PD deploy-blocker PR (review §5) now sits
on V2-1d's critical path.

**Opened:** 2026-06-11 (P2 shipped, commit dfcff6ca) · **Closes:** when ≥1 full Adda cycle has run through the worker report flow AND the soak review (§4) is written and owner-approved. **P3 (V2-1d M2M drop) is gated on this document.**
Scope guard (owner): no settlement, no MissingPiece, no Alter/Rework work during soak.

## 1) Soak success criteria (locked C2)
- [ ] ≥1 full Adda cycle: assignment → worker report (draft → submit) on each payable stage → stage completions → Adda done.
- [ ] Multiple workers report on at least one shared stage (isolation under real concurrency).
- [ ] At least one manager correction case exercised (`verified_quantity` path) — confirms D6 model suffices.
- [ ] Dual-write parity verified at soak end (§3).
- [ ] Soak review (§4) written, owner signs.

## 2) Live log (append entries here during soak — date · who · what)
Categories: `UX` worker feedback · `SCHEMA` contribution schema limitation · `EDGE` contribution edge case · `SEC` isolation/security observation · `PARITY` M2M↔task divergence · `BUG`.

| Date | Cat | Entry | Status |
|---|---|---|---|
| 2026-06-11 | — | Soak opened. P2 browser-verified pre-soak (draft/submit/locked/badges/mobile). | — |
| 2026-06-11 | — | **§7 setup checklist EXECUTED via real admin UIs** (browser-driven): worker2 (worker+cutting_master), worker3 (worker, no skill — isolation probe), manager1 (manager); 3 ProductSizes (Free/1/2) for 3-PATTI; cutting rate ₹3.00/piece; barcode_generation appended to flow; Patti Panel pattern ×3 assigned; 4 Red rolls bulk-created (CR-000001..4); Adda **3-PATTI-001** created — 4-stage pipeline renders, layering workspace loads, zero console errors. cutting_pattern was already in flow (owner added it 2026-06-10 20:22 UTC after reading §7). | setup done |
| 2026-06-11 | UX | User-create form: clicking "Create User" with an empty required field gives NO visible feedback in some cases (native HTML5 bubble only; my password value was cleared by the fancy-select re-render and the click died silently — no server POST). Real workers/admins may hit the same silent-stall. SETUP issue (admin surface), not architecture. | logged |
| 2026-06-11 | UX | Bulk roll intake: "Create Rolls" stays disabled until "+ Add color row" is clicked — the filled color/qty inputs alone don't count. Reasonable design but not obvious; a hint near the button would help. SETUP issue. | logged |
| 2026-06-11 | EDGE | Flow editor allowed appending cutting_pattern/barcode_generation UNPRICED (rate=None) with no warning. Correct per NULL=unpriced semantics (both stages are legitimately unpriced), but docs describe a "mandatory-rate flow editor" — guard appears scoped to priced methods only. Verify intent during validation. ARCHITECTURE observation (benign). | logged |
| 2026-06-11 | SEC | Layering workspace worker-assignment list correctly shows only SKILLED users (utest, worker2); worker3 (no skill) absent — skill-filter works at the assignment UI level. First positive isolation evidence. | ✅ pass |
| 2026-06-11 | — | **SCENARIO 1 (Layering) EXECUTED** — owner started stage + assigned utest/worker2; agent continued: manager1 attached CR-000001 (36in/10kg), draft layers=25 + leftover 1.5kg + length 8m; worker2 reported 25 via qty-only schema → draft → submit → locked; super_admin completed → advanced to Cutting Pattern. | done |
| 2026-06-11 | EDGE | **Layering draft silently drops a partial row**: `save_layering_draft` skips an entry unless BOTH layers AND leftover-weight are non-empty (layering/service.py:596) but the UI still flashes "Draft saved." — worker/manager believes layers persisted when they didn't. Misleading success on partial fill. | **OWNER TRIAGE: EDGE · fix-before-P3** — silent data loss + success message is misleading; worker must be told when rows are skipped. |
| 2026-06-11 | SEC | **Manager cannot complete layering**: manager1 refused with "only cutting_master_helper can complete Layering stage". Manager bypasses stage ACCESS but not the skill-gated COMPLETION → with current users only super_admin can complete layering. Asymmetry: manager can start + assign but not complete. Intended (completion = skilled act) or gap? | **OWNER TRIAGE: SEC/WORKFLOW · won't-fix (for now)** — completion stays a skilled-worker action; access ≠ completion authority. Revisit if validation shows managers frequently need it. |
| 2026-06-11 | EDGE | **Stage completion leaves unreported tasks dangling as `assigned`** (utest) on a completed stage record — completion neither blocks on nor auto-resolves active tasks. Consistent with locked semantics (the all-tasks-completed gate is the PAY-2 worker-ADVANCE guard, not stage advance) and harmless to money (settlement reads completed only) + parity (sets still match), but the task is stuck active forever = data hygiene + reporting noise. Options: block / auto-cancel at complete / leave. | **OWNER TRIAGE: EDGE · fix-before-P3** — completed stage must not leave unresolved active tasks; deliberate lifecycle decision needed before V2-1d freezes behavior. |
| 2026-06-11 | SCHEMA | ✅ Open-closed renderer proven on REAL stages: same template rendered layering as single Quantity field (no chips) and cutting as colour+size+qty. Zero stage conditionals hit. | ✅ pass |
| 2026-06-11 | EDGE | ✅ credits_workers=False + unpriced stage: worker2's contribution froze expected_rate=0.0000/expected_earning=0.00 (Option B visibility rows); worker screen shows NO money — reads cleanly. | ✅ pass |
| 2026-06-11 | UX | ✅ Badge transitions exact: Report needed → ✎ Draft saved → ✓ Submitted. | ✅ pass |
| 2026-06-11 | UX | ✅ NO manual duration input anywhere; workspace says "Time is recorded automatically"; completion computed duration_minutes=35 from timestamps; drafts cleared on complete. Owner auto-duration rule implemented. | ✅ pass |
| 2026-06-11 | PARITY | ✅ `check_worker_task_parity` after Scenario 1: PARITY OK — M2M == task sets everywhere. | ✅ pass |
| 2026-06-11 | — | **SCENARIO 2 (Cutting Pattern) EXECUTED** — super_admin assigned utest, started stage, uploaded photo evidence, verified 1/1 patterns, locked size proportions (Free=100%), completed → advanced to Cutting; then REOPENED + re-completed. | done |
| 2026-06-11 | EDGE | ✅ **Completion gates fire in strict order with clear refusals**: (1) evidence gate "Upload at least one photo or a video…", (2) verification gate "0 of 1 patterns verified — verify all before completing" (R0 C3 stage-level handler gate confirmed at runtime), (3) size-proportions gate "Select at least one size for this batch and lock proportions." All three refused premature completion correctly. | ✅ pass |
| 2026-06-11 | EDGE | **Reopen semantics differ per stage**: pattern reopen = SOFT unlock (record/verification/photo/proportions all preserved; re-complete sails through), layering reopen = teardown (record deleted, header copied to drafts). Both are handler-owned (`reopen()` contract, I2) so divergence is by design — but worth a one-line doc note so future stages pick a semantic deliberately. | **OWNER TRIAGE (F4): EDGE · fix-after-P3** — valid behavior, not an architecture issue; document the destructive-vs-soft reopen choice so future handlers decide deliberately, never inherit accidentally. |
| 2026-06-11 | EDGE | F3 RECURS on pattern stage: utest's task left `assigned` on the completed stage record (never reported). Same lifecycle gap as layering — strengthens the fix-before-P3 triage. | covered by F3 |
| 2026-06-11 | PARITY | ✅ Parity after Scenario 2: PARITY OK — 2 stage records, sets match everywhere. | ✅ pass |
| 2026-06-11 | — | **SCENARIO 3 (multi-worker Cutting) EXECUTED** — utest+worker2 assigned; breakup 105 Red/Free; bundle Lot-A (105); allocation 45pc→worker2 (live money); completed → advanced to Barcode Generation. | done |
| 2026-06-11 | SEC | ✅ **Concurrent draft isolation**: worker2 drafted Red/Free/40; utest's report page showed ONE BLANK line (no cross-task leakage); utest drafted 2 lines (60+20) without touching worker2's draft. | ✅ pass |
| 2026-06-11 | EDGE | ✅ **Replace-draft semantics exact**: worker2 prefill showed 40, re-draft → single row 50 (no duplicates); utest's lines untouched. Multi-line (2 rows) round-tripped. | ✅ pass |
| 2026-06-11 | EDGE | ✅ **expected_* freeze math exact at submit**: worker2 50×3.0000=150.00; utest 60×3=180.00 + 20×3=60.00. Rate source = stage rate (no role override configured). | ✅ pass |
| 2026-06-11 | EDGE | ✅ **Manager correction immutability**: verified_quantity=45 set on worker2's line; reported_quantity (50) and frozen expected_earning (150.00) UNCHANGED — corrections never rewrite the worker's report or the freeze. | ✅ pass |
| 2026-06-11 | UX | **verified_quantity has NO writer surface** — not even Django-admin registration; today the D6 correction path is SHELL-ONLY. D6 deferred a full UI deliberately, but for the true soak managers need at least an admin form. | owner triage — suggest fix-before-TRUE-soak (admin registration or minimal service+form), not P3-blocking |
| 2026-06-11 | UX | **Management readiness invisible**: Adda detail shows assigned workers but NOT per-worker report progress (1-of-2-submitted state unseen). Derived readiness exists in data; no management surface renders it. | owner triage — suggest fix-after-P3 (panel addition) |
| 2026-06-11 | SEC | **Assignment-list filter inconsistency**: layering assign list = skill-filtered (worker3 absent); cutting workspace assign list = UNFILTERED (manager1, super_admin, no-skill worker3 all offered). Also note: worker-report view gates on assignment (task) only — a no-skill worker WITH a task could report (assignment-implies-authorized; defensible, but Skill∧Assignment is the stated stage rule). | owner triage |
| 2026-06-11 | EDGE | ✅ **Dual money surface observed live (ADR-0007 coexistence)**: allocation wrote SWA 45×3 + immediate ledger CREDIT ₹135 (allocation-era path); expected_* visibility shows ₹150 (reported 50×3). Worker payroll summary reads LEDGER (135.00 payable) — money never reads expected_*. Exactly the documented pre-V2 state V2-2 will cut over. | ✅ pass |
| 2026-06-11 | EDGE | ✅ **Cost freeze on completion**: processing_cost=315.00 (105×3) with rate/qty snapshots; advanced to barcode_generation; both worker tasks already `completed` (no F3 dangling — both reported first). | ✅ pass |
| 2026-06-11 | PARITY | ✅ Parity after Scenario 3: PARITY OK — 3 stage records, sets match everywhere. | ✅ pass |
| 2026-06-11 | — | **SCENARIO 4 (isolation probes) EXECUTED.** | done |
| 2026-06-11 | SEC | ✅ worker3 (no skill, no task): **403 on all six** probed URLs (report×2, cutting workspace, layering, pattern, payroll overview). ✅ Cross-worker payroll blocked BOTH directions (worker3→worker2 403; worker2→utest 403). ✅ worker2 own /expense/my/ renders (ledger ₹135). ✅ manager1 bypass correct: 200 on worker detail, payroll overview, cutting workspace. | ✅ pass |
| 2026-06-11 | — | **SCENARIO 5 (Barcode Generation + P4.2 smoke) EXECUTED — ADDA 3-PATTI-001 COMPLETED (full cycle).** | done |
| 2026-06-11 | EDGE | ✅ **P4.2-relocated surfaces all work in the real flow**: generate → exactly 105 barcodes (one batch Red/Free 1-105 from the FROZEN breakdown, via production assembly); print sheet rendered 105 QR data-URIs; scan lazy-created BatchBarcode 0042 with scanned-by stamp; manifest CSV export EXP-2026-001 (105 labels) via relocated export service. Stage complete → **Adda status=completed**. | ✅ pass |
| 2026-06-11 | UX | **Barcode-gen start REQUIRES ≥1 worker** ("Select at least one worker") although generation is system work (E-archetype) — worker selection forced on a stage with nothing to report. Minor; relates to F3 (that worker's task will dangle as `assigned` since there's nothing to report — confirmed: utest task on barcode stage left assigned at completion). | owner triage — candidate to allow worker-less start OR auto-complete tasks on E-stages; fold into the F3 lifecycle decision |
| 2026-06-11 | PARITY | ✅ Final parity after full cycle: PARITY OK — 4 stage records, sets match everywhere. | ✅ pass |
| 2026-06-11 | — | **ALL 5 VALIDATION SCENARIOS COMPLETE.** Dev-level evidence for soak criteria: full Adda cycle ✓ (assignment → reports incl. payable stage → completions → done), multi-worker shared stage ✓, manager correction exercised ✓ (shell path), parity ✓×4. TRUE-soak versions of these criteria still require deployment + real workers (§1 unchanged). | summary |
| 2026-06-11 | — | **F1 + F3/F8 FIXED (commit f9d9a897, owner-approved design).** F3/F8: `resolve_stage_tasks_on_complete` in the advance funnel — unreported active tasks auto-cancel (note + log), completed/verified untouched, draft lines retained, M2M roster syncs via chokepoint (DISPLAY CHANGE: completed-stage roster = reporters only, owner-intended), parity by construction; data migration 0034 resolved the 3 dev dangling tasks; reopen→re-assign = recovery. F1: partial layering-draft rows now reported back with roll ids (warning message), blank rows silent. +9 tests, suite 445 green, parity OK. **All fix-before-P3 items CLOSED.** | ✅ fixed |

## 3) Pre-V2-1d worklist (kept visible per owner)
| Item | Shape | Status |
|---|---|---|
| **Parity assertion** | `check_worker_task_parity` command + check.sh gate [5/5] (runs against the dev DB on every check). Re-run at soak end + immediately before V2-1d. | ✅ BUILT 2026-06-11 (c851f902, 3 tests) |
| Kill-switch semantics | Documented in V2_1_REVIEW §10 header (flag OFF ⇒ tasks stale ⇒ re-backfill before re-enable). | ✅ done (R0) |
| Clone rehearsal | up→down→up of the drop migration on a dev-DB clone. | TODO (at V2-1d time) |
| Stale docstrings (A8) | `worker_task.py:14` "deferred to V2-1c" + `adda.py:89-92` M2M note — fix inside the V2-1d PR (already on V2_1_REVIEW:218's list). | TODO (V2-1d PR) |

## 4) Soak review template (fill at soak end — the P3 gate document)
1. **Worker feedback** — usability, mobile, language, chip ergonomics, draft habits.
2. **Schema limitations discovered** — fields workers needed but schema lacked; any pressure toward the `attributes` JSONB (note: JSONB lands only with a real consumer — F1).
3. **Contribution edge cases** — multi-line patterns, replace-draft surprises, concurrent reports on one stage, reopen interactions, blank/partial lines.
4. **Isolation / security findings** — any cross-worker visibility, URL probing results, manager-bypass correctness.
5. **Parity observations** — `check_worker_task_parity` output; any divergence + root cause.
6. **Recommended changes** — classified: fix-before-V2-1d / fix-after / won't-fix.

## 5) Tracked risks from P2 (owner triage 2026-06-11 — none block roadmap)
- **Registry restore footgun** (TRACK): `registry.clear()+autodiscover()` cannot restore handlers in-process (modules already in `sys.modules` → re-import no-op → registry left empty). Tests must snapshot/re-register (pattern in `test_worker_report_view.py`). Candidate hardening later: guard `clear()` behind test-only flag or make `autodiscover()` force-reload.
- **Seed collisions** (TEST HYGIENE): seeded Stage codes / ClothColor names break naïve `objects.create` in tests — use `get_or_create` (helper pattern now exists).
- **Perf-baseline semantics** (DOCUMENT ONLY): worker-dashboard baseline measures the context builder; lazy querysets count zero until materialized — documented in `test_perf_baseline.py`.
- **Pre-existing foundation-purity gate failure**: ✅ FIXED 2026-06-11 (2399b044, P4.2 PR-0) — gate [1/5] KEPT.

## 6) P4.2 during soak — evaluation (owner asked)
**Recommendation: YES, run P4.2 during the soak window**, with sequencing rules.

For: (1) fully independent of the worker-report flow — touches barcode assembly/export/scan code paths only; (2) zero data migration (string FKs; verified by design review) → `git revert`-able; (3) characterization tests come FIRST and outputs must be byte-identical, so regressions surface before merge, not in the factory; (4) clears the import-cycle suppressions (P4.4 contract flip) and directly advances extraction readiness; (5) uses an otherwise idle engineering window.

Against (mitigated): two things in flight muddies attribution if a barcode page breaks mid-soak → mitigation = small reversible PRs in the planned order (characterization → assembly move → export/view move → contract flip), each gate-green before the next; pause P4.2 immediately if soak surfaces report-flow bugs needing fixes.

Suggested P4.2 PR order (from P4_2_BARCODE_DESIGN_REVIEW): characterization lock → relocate 3 assembly fns into `production/stages/barcode_generation/assembly.py` → relocate export production-reads + 4 views (D1: cross-cutting views → inventory/apps; stage panel stays production) → flip `.importlinter` layers (tracking BELOW production) + drop `ignore_imports` → `makemigrations --check` must say "No changes" at every step. Fold in the foundation-purity test-import chore.

— **Owner approved 2026-06-11 → ✅ P4.2 EXECUTED same day**, 4 commits, all gates green, `makemigrations --check` clean throughout (no data ever moved):
  - PR-0 `2399b044` purity chore + characterization baseline
  - PR-1 `23ba2b69` assembly (generate_for_cutting/_legacy/from_breakdown + _allocation_key) → `production/stages/barcode_generation/assembly.py`
  - PR-2 `ce930ac1` export service → production stage pkg; 4 /tracking/ views → `inventory/views/tracking_*.py`; urls → `inventory/tracking_urls.py` (namespace + every path/name preserved)
  - PR-3 `4b19fe01` layers flipped (tracking BELOW production), tracking ignore block deleted — **production↔tracking cycle GONE**; remaining worklist = production→expense (V2-3 facade) + raw_materials edges + test noise.
  Rollback for any step = `git revert` (pure code moves).

## 7) Real-workflow validation — 3-PATTI sufficiency analysis (2026-06-11)

**Dev-DB reality check (as configured today):** 3-PATTI flow = `[layering, cutting]` ONLY (no cutting_pattern in flow); cutting `cost_rate=None` (expected_earning would freeze 0.00); **zero ProductSize rows** (cutting size chips render empty); zero patterns; **zero available rolls** (layering cannot start); **one worker user** (utest, cutting_master) + super_admin only; layering `credits_workers=False` / cutting `True` (good payability contrast).

### Setup checklist BEFORE validation can start (all via existing real UIs — doing it manually also validates those admin surfaces):
1. Users: create worker2 (worker role, cutting skill) + worker3 (worker role, NO cutting skill — isolation probe) + a `manager` role user (manager-bypass ≠ super_admin path). `/inventory/users` + Access Control hub.
2. Cutting rate: set per-piece rate on 3-PATTI flow (`/production/products/<pk>/flow/`); optionally a role-rate override to validate the rate-source order (role_rate → stage rate).
3. Sizes: add 2-3 ProductSizes for 3-PATTI (`/production/products/<pk>/sizes` editor) — without them the cutting schema renders degenerate.
4. Rolls: bulk-add a few rolls (`/raw-materials/rolls/bulk-add/`) so layering can attach.
5. OPTIONAL but recommended: insert `cutting_pattern` into the 3-PATTI flow via the flow editor (+ assign a pattern) — it is the ONLY stage exercising the stage-completion VERIFICATION GATE (R0 C3 semantics) and the reopen path; and insert `barcode_generation` to manually smoke the P4.2-relocated assembly/export/print/scan surfaces.

### Q1 — validatable NOW with the real workflow (post-checklist):
WorkerStageTask lifecycle (assign/report/complete/cancel-via-unassign) · assignment isolation (worker2 vs worker3 + URL probing) · draft→submit→locked · schema rendering across TWO real schemas through one renderer (layering=default qty-only vs cutting=color+size+qty) · expected_* freeze incl. rate-source + HALF_UP rounding · data-driven payability contrast (credits_workers False/True) · derived readiness + advance gates · multi-worker same-stage behavior (parity gate watches dual-write) · manager correction PATH (admin/shell — D6: no UI by design) · handler contracts for A/C archetypes (+B verification gate and E identification if step 5 done) · dashboard badge transitions · P4.2 smoke.

### Q2 — NOT validatable until future stages/modules exist (by design, not gaps):
`attributes` JSONB path (first machine/QC consumer) · `scan_policy`/`validate_scan` seam (future Barcode review) · free-standing D-archetype QC + F packing/dispatch · settlement consumption of contributions (V2-2) · advance-recovery + variance entry against real settlements · sub-stage parent FK · Missing/Alter lifecycles · real-device mobile ergonomics + true concurrency (deployment).

### Q3 — risks that stay HIDDEN if validating only the current flow as-is:
1. Empty-sizes degenerate form (fixed by checklist 3). 2. Single-worker blind spot — isolation + concurrent replace-draft races invisible (checklist 1). 3. Zero-rate blind spot — expected-earning math bugs invisible (checklist 2). 4. Verification-gate semantics unexercised without cutting_pattern in flow (checklist 5). 5. P4.2-relocated barcode surfaces untouched in-browser without barcode_generation (checklist 5). 6. Observation to confirm during validation: `complete_worker_task` freezes expected_* regardless of `credits_workers` (visibility on non-payable stages shows 0-rate lines) — expected per Option B, but verify it reads sanely on worker screens.

### Q4 — seed tooling verdict: DEFERRED.
Owner preference is right: real workflow first. The blocker isn't missing synthetic scenarios — it's incomplete real master data, and completing it MANUALLY through the existing admin UIs is itself validation coverage. `seed_validation_factory` only earns its keep if scenario RESETS become frequent (rule of thumb: automate after the 2nd-3rd manual reset). Revisit then.
