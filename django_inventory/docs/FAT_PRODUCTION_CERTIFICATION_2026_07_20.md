# FAT — Production Heart Certification (Factory Acceptance Test)

**Started:** 2026-07-20 · **Certification Adda:** 3-PATTI-013 · **Mode:** multi-phase
browser audit, one phase per session, STOP for owner approval between phases.
**Deployment blocked until FAT passes.**

Phase log (append-only): Phase 0 below. Later phases append their own sections.

---

# PHASE 0 — FACTORY PREPARATION ✅ COMPLETE (awaiting owner approval to proceed)

## 1. Executive Summary

Realistic factory fixture built and verified. **10 cloth rolls** (42″, 22–26 kg,
10 distinct colours) created through the real bulk-intake path; **30 workers** created
covering every production role with correct skill mapping, including multi-skill workers;
**skill-based visibility verified** both at the access-predicate level and live in the
browser. **Zero 500s, zero failed POSTs, no new bugs in Phase 0.** One pre-existing
inventory finding (width choice ceiling) reconfirmed as non-blocking for this fixture.
Fixture is ready for Phase 1 (Pre-Production audit).

## 2. What was created (all DEV-marked, reused in later phases)

### Cloth rolls — 10 (supplier tag `FAT-Phase0`, all AVAILABLE, Rohini Factory, Cotton)

| Roll | Colour | Width | Weight |
|---|---|---|---|
| CR-000023 | Red | 42″ | 22.00 kg |
| CR-000024 | Blue | 42″ | 22.50 kg |
| CR-000025 | Black | 42″ | 23.00 kg |
| CR-000026 | White | 42″ | 23.50 kg |
| CR-000027 | Yellow | 42″ | 24.00 kg |
| CR-000028 | Green | 42″ | 24.50 kg |
| CR-000029 | Navy | 42″ | 25.00 kg |
| CR-000030 | Grey | 42″ | 25.50 kg |
| CR-000031 | Brown | 42″ | 26.00 kg |
| CR-000032 | Orange | 42″ | 24.00 kg |

4 new colours created to reach 10 distinct (Navy/Grey/Brown/Orange; Red/Blue/Black/
White/Yellow/Green already existed).

### Workers — 30 (`dev.fat.*@test.local` / `Dev@12345`)

| Group | Count | Skill / role |
|---|---|---|
| Layering Master 1–2 | 2 | `cutting_master` |
| Layering Helper 1–2 | 2 | `cutting_master_helper` |
| Pattern Master 1 | 1 | `cutting_master` |
| Cutting Master 1 | 1 | `cutting_master` |
| Cutting Helper 1 | 1 | `cutting_master_helper` |
| Overlock Worker 1–10 | 10 | `overlock_operator` |
| Flatlock Worker 1–5 | 5 | `flatlock_operator` |
| Checking Worker 1 | 1 | `checker` |
| Packing Worker 1 | 1 | `finishing_helper` |
| Elastic Worker 1 | 1 | `elastic_operator` |
| Single-Needle Worker 1 | 1 | `single_needle_operator` |
| Multi Worker 1 | 1 | `overlock_operator` + `flatlock_operator` + `checker` |
| Multi Worker 2 | 1 | `cutting_master` + `overlock_operator` |
| Settlement User | 1 | role `accountant` |
| Payroll User | 1 | role `manager` |

Skills chosen from the live **stage → access_by_skill** table (not guessed): layering /
cutting / pattern / barcode all gate on `cutting_master(_helper)`; overlock/neck/shoulder/
side-seam on `overlock_operator`; leg-binding/bottom-fold/sleeve-fold on `flatlock_operator`;
checking on `checker`; packing/thread-cutting on `finishing_helper`; elastic on
`elastic_operator`; label/collar on `single_needle_operator`; sleeve-join on `sleeve_operator`.

## 3. Test cases & results

| # | Test | Method | Result |
|---|---|---|---|
| P0-1 | Bulk-intake 10 rolls, 10 colours, one submit | real POST through `raw-materials/rolls/bulk-add/` → `bulk_create_rolls` | PASS — 302, 10 rows, unique roll IDs from the PG sequence |
| P0-2 | Set width 42″ + weight per roll | roll-edit path (`RollEditForm` fields) | PASS — all 10 at 42″/22–26 kg |
| P0-3 | Inventory visible in list UI | browser `Cloth Rolls` list | PASS — 10 rolls, correct colour/width/weight/location/status=AVAILABLE (screenshot `fat_roll_list.png`) |
| P0-4 | 30-worker roster with correct skills | `get_or_create` + `skills.set()` | PASS — created=30, every skill mapping correct |
| P0-5 | Single-skill isolation | `user_can_access_stage` matrix | PASS — overlock worker sees only overlock/neck/shoulder/side-seam; checker sees only checking; elastic sees only elastic |
| P0-6 | Multi-skill union | `user_can_access_stage` matrix | PASS — multi1 (overlock+flatlock+checker) accesses the exact union of all three skills' stages |
| P0-7 | Worker dashboard + minimal sidebar (mobile) | browser login `dev.fat.ov1`, 390×844 | PASS — "Welcome FAT Overlock Worker 1", minimal worker sidebar, "No active tasks" empty-state (not yet assigned), Hinglish helper text (screenshot `fat_ov1_dashboard.png`) |

## 4. Browser evidence
- `fat_roll_list.png` — Cloth Rolls list, 10 FAT rolls.
- `fat_ov1_dashboard.png` — overlock worker mobile dashboard, skill-appropriate empty state.

## 5. Bug register (Phase 0)
- **None new.** No 500s, no failed POSTs.

## 6. UI review
- Bulk-add, roll list, worker dashboard all render correctly; roll list is a proper
  responsive table with status pills. Worker mobile dashboard clean, touch-friendly.

## 7. Workflow / extensibility review
- **Stage → skill mapping is data, not code** (`Stage.access_by_skill` M2M). Adding a
  future stage + skill needs no business-logic change — the access predicate reads the
  M2M live. Extensibility assumption holds at the visibility layer (deeper extensibility
  — reporting/allocation/dashboards for a NEW stage — is exercised in Phases 1–2).

## 8. Performance notes
- Bulk create of 10 rolls: single INSERT (`bulk_create`), 302 in well under a second.
- Access-predicate matrix over 20 stages × 6 workers: instant.

## 9. Recommended fixes (carry-in, none block Phase 0)
- **INV-1 (Medium, pre-existing E2E-2):** `WIDTH_CHOICES = 36–44″` (`raw_materials/models.py:99`).
  42″ is in range so this fixture is fine, but real stock has 60″ rolls that can't state
  their true width. Widen the choice range (or make it data-driven) before real intake.
- **SEED-1 (High, = audit H-1):** the 4 new colours + all this master data live only in the
  dev DB. Production seed path still pending (tracked in the P19A audit). Not a Phase-0
  blocker; flagged for deployment.

## 10. Data footprint (for reuse / cleanup)
- Rolls CR-000023..032 (`supplier=FAT-Phase0`). Colours Navy/Grey/Brown/Orange (ids 26–29).
  Workers `dev.fat.*@test.local` (30). Certification adda 3-PATTI-013 (from prior session).
  All DEV; reused by later phases; nothing to clean until FAT closes.

---

## ⏸ STOP — Phase 0 complete. Awaiting owner approval to begin Phase 1 (Pre-Production: Layering / Pattern / Cutting audit on 3-PATTI-013).

**→ Phase 0 APPROVED by owner. Phase 1 + Phase 1A executed below.**

---

# PHASE 1 — PRE-PRODUCTION (Layering → Pattern → Cutting) on 3-PATTI-013

## Executive summary
Layering and Pattern **pass** end-to-end in the browser; Cutting passes through start +
breakup entry. Cutting-complete was intentionally **not** finished — it requires the
post-join "actual bundle entry" step, and per the owner's explicit priority
("the allocation engine is more important than reaching settlement") I pivoted to the
Phase 1A allocation certification instead. No 500s. Three low/medium notes below.

## Test log (browser, real roles)
| Step | Actor | Result |
|---|---|---|
| Layering roster "Update workers" (the C-1-fixed button) | manager | PASS — assigns, no 500 |
| Attach roll CR-000023 (Red, 42″, 22 kg) | worker utest | PASS — "Roll CR-000023 attached" |
| Report layers (report page) | utest + dev.cm.b (parallel earlier) | PASS |
| Complete layering (breakup: 10 layers, 2 kg leftover, 1.5 m) | worker | PASS → advanced to cutting_pattern |
| Pattern start (assign dev.fat.pm1) | manager | PASS |
| Pattern checklist verify (2 patterns) + submit | worker dev.fat.pm1 | PASS — both `CuttingPatternVerification` rows written |
| Pattern complete | super admin | PASS → advanced to cutting (after photo + size proportions 50/30/20 set) |
| Cutting start (assign dev.fat.cm1) | manager | PASS |
| Cutting breakup entry (Black × Free Size/Size 1, 2 patterns, 75 pc) | manager/service | PASS — `CuttingPieceBreakup` rows created |
| Cutting complete | manager | DEFERRED — needs post-join "Actual Cutting Bundle Entry"; pivoted to Phase 1A |

## Phase 1 findings
- **P1-1 (Low, UI staleness):** after the worker checklist-verified both patterns, the
  manager Pattern panel still showed "✗ Pending / Verify" on a fresh load while the DB had
  both `CuttingPatternVerification` rows written (08:43). The manager view reads a different
  freshness than the truth — verify whether it's a caching/render bug or an intended
  manager re-verify gate. Did not block completion.
- **P1-2 (Low, permission clarity):** Pattern **complete** requires helper-skill or
  super-admin; a plain `manager` (dev.mgr) cannot complete it even though the Complete
  button renders for them. Either hide the button for managers or admit managers. (Same
  skill-vs-role tension as M-8 in the P19A audit.)
- **P1-3 (Info):** Cutting-complete's dependence on a separate post-join bundle-entry step
  (distinct from the breakup entry) is non-obvious; the workspace shows two piece-entry
  sections ("Suggested" vs "Actual Cutting Bundle Entry") which reads as duplication.
  Worth a UX pass — but note this is the CuttingBundle (per-size) object, which Phase 1A
  shows is itself mis-grained vs the owner's bundle model.

---

# PHASE 1A — STITCHING BUNDLE ALLOCATION & REPORTING CERTIFICATION 🔴 FAILED (architecture gap — owner decision required)

> **This is the certification the owner flagged as the most important in the whole FAT.
> The current allocation engine does NOT implement the owner's bundle model. Both core
> rules were violated LIVE in the browser. Do not build past Cutting until the architecture
> is decided.**

## 1. Current implementation review (what the engine actually is)
The stitching engine is a **quantity-pool** system, not a bundle-ownership system. Evidence
(file:line, verified by code read + live execution):
- At cutting-complete, `_materialize_breakdown` freezes a per-(size,colour) **piece-count
  snapshot** `AddaProductSizeColorPieceBreakdown` (`config/production/stages/cutting/service.py:181`).
  This is a passive count ("Black / Free Size / 50"), not an ownership object.
- A downstream stitching manager calls `pool_service.allocate(consuming_sr, worker, *, qty,
  color_id, size_id)` (`config/production/services/pool_service.py:346`) which writes a
  `WorkerStageAllocation` row = **quantity + colour + size, NO bundle FK**
  (`config/production/models/core.py:490`).
- `available() = pool_good − Σ non-voided allocations`; `allocate()` refuses **only**
  `qty > available` (`pool_service.py:314,366`). There is **no** uniqueness / single-owner
  constraint on `(stage_record, colour, size)` (`core.py:526` — only `qty>0`).
- The word "bundle" in code (`CuttingBundle`, `config/production/models/cutting.py:415`) is a
  **per-SIZE, all-colours** container (`unique_together=('cutting_record','size')`) — the
  *opposite* grain from the owner's "one colour + one size", and it is a parallel system the
  pool path never reads.

## 2. Gap analysis vs the owner's bundle model

| # | Owner's required rule | Current behaviour | Verdict |
|---|---|---|---|
| A | 1 bundle = 1 colour + 1 size | `CuttingBundle` = 1 size × all colours; allocation unit = qty+colour+size with no bundle object | 🔴 VIOLATES |
| B | 1 bundle → 1 worker; **no splitting** | Engine lets N workers each take a qty slice of the same (colour,size); UI help text literally says "edit to split" (`_stage_panel_generic.html:111`) | 🔴 VIOLATES (proven live, §3) |
| C | Allocation UI = Stage → Worker → **unassigned-bundle dropdown** → Assign | UI = Worker + colour·size-lot dropdown + **free qty box**; lot stays visible with reduced "available", never disappears | 🔴 VIOLATES |
| D | Worker never reports beyond allocation | Correct formula exists (`check_allocation_bound`, good+alter+missing+damaged ≤ allocated) but is gated by `ENFORCE_ALLOCATION_BOUND` = **False** by default → soft warning only | 🔴 VIOLATES by default (proven live, §3) |
| E | Worker sees "My Assigned Bundles", reports per bundle | Single schema form; options scoped to worker's allocated dims; **but** colour & size are flat independent lists, so a worker allocated Red/M+Blue/XL can report **Red/XL** (a pair never given) — `handler.py:66`, parse guard validates each field, not the pair | 🟠 PARTIAL / gap |
| F | Multiple bundles per worker, independent items | Supported via multiple allocation rows + one prefilled report line per dim pair | 🟢 MATCHES (dimension-based, not bundle-based) |
| G | Allocation carries no money; money at settlement only | `WorkerStageAllocation` has no money; earnings = reported-good × rate at `finalize_adda_settlement` (`adda_settlement_service.py:414`); legacy money-at-allocation disabled (`LEDGER_CREDIT_AT_ALLOCATION=False`) | 🟢 MATCHES |
| H | Reassignment safe + auditable | `void_allocation` append-only, management-only, post-report guard (`pool_service.py:503`) | 🟢 MATCHES |
| I | Fully stage-driven; new stitching stage = config only | Handler-dispatched, zero stage-name conditionals in allocation/report/earnings/settlement; `WorkflowStage.allocation_dimensions` is flow-editable | 🟢 MATCHES |

## 3. Live browser evidence (executed, not inferred)
- **SPLIT (rule B) — VIOLATED:** on 3-PATTI-009 overlock, pool (Black, Free Size) = 10 pc.
  Allocated **6 pc → dev.fat.ov1** AND **4 pc → dev.fat.ov2** (same colour+size). Both POSTs
  302-succeeded; both `WorkerStageAllocation` rows persisted. The forbidden "25+25 across two
  workers" workflow is exactly what the engine does.
- **OVER-REPORT (rule D) — VIOLATED:** dev.fat.ov1 (allocated 6) reported **10 good** →
  ACCEPTED, task `completed`, `good_quantity=10`. `ENFORCE_ALLOCATION_BOUND=False` (confirmed
  live) so the bound is only a soft warning. Owner's "51 vs 50 → INVALID" is not enforced by
  default.

## 4–10. UI / workflow / bundle / dashboard / cost / settlement audits
Covered by the matrix above and the P19A-E2E money certification (settlement/cost/earnings
verified paisa-exact there). The allocation UI (§2-C) and the report validation (§2-D/E) are
the failing surfaces; cost/earnings/settlement/reassignment/extensibility all pass.

## 11. Required UI improvements
- Replace the worker + colour·size-lot + free-qty allocation form with **Stage → Worker →
  Unassigned-Bundle dropdown → Assign** (whole bundle, one click). Assigned bundles must
  disappear from the dropdown.
- Worker dashboard: render **"My Assigned Bundles"** as discrete items (one per bundle), each
  linking to its own report — instead of one dim-scoped form.

## 12. Required backend improvements
- Introduce a first-class **Bundle = exactly one colour + one size**, with a single nullable
  **holder** (current worker) and a **one-active-owner constraint**. Either re-grain
  `CuttingBundle` to colour+size, or add a one-active-row-per-`(stage_record,colour,size)`
  uniqueness guard to `WorkerStageAllocation` and drop the `qty` parameter (whole-bundle,
  all-or-nothing allocation).
- Flip `ENFORCE_ALLOCATION_BOUND` to **ON by default** (hard block over-report).
- Validate the **(colour,size) pair** in `contribution_schema` / `_parse_lines`, not flat
  colour and size lists (closes rule E).

## 13. Future-stage extensibility review
🟢 **PASS.** The engine is genuinely stage-generic (handler registry + `allocation_dimensions`,
no stage-name conditionals anywhere in allocation/report/earnings/settlement). Inserting a new
stitching stage is Stage-Library config only. **The bundle-model change above must preserve
this** — implement it in the generic pool/allocation layer, not per-stage.

## 14. Acceptance criteria (for the rebuilt allocation engine)
1. A bundle is exactly one colour + one size; a stage cannot have two active holders for the
   same bundle (DB constraint, not just UI).
2. Allocation UI offers only **unassigned** bundles; assigning removes it from the pool.
3. A worker sees each held bundle as a separate item and reports per bundle.
4. Over-report (good+defects > allocated) is **hard-blocked** with a clear message; a worker
   cannot report a colour+size pair not allocated to them.
5. Money still only at settlement; reassignment still append-only/auditable; a NEW stitching
   stage still works with zero business-logic change.

## Recommendation
The current engine is well-built for what it is (clean, generic, money-safe) but implements a
**different business model** (divisible quantity pool) than the owner's (**indivisible bundle
ownership**). This is not a bug to patch — it is a **data-model + UI + validation change** that
needs an owner-approved design before build. Per the owner's own instruction, I am stopping
here for that decision rather than force-fitting.

## Data footprint (Phase 1/1A, all DEV)
- 3-PATTI-013 advanced to Cutting (layering/pattern complete; cutting started + breakup, not completed).
- 3-PATTI-009 overlock: split-test allocations (ov1 6 pc + ov2 4 pc, Black/Free Size) + ov1
  over-report contribution (good=10) left as evidence.

## ⏸ STOP — Phase 1 done; Phase 1A FAILED with a defined architecture gap. Awaiting owner decision:
**(1)** approve the bundle-ownership rebuild (§11–14) then continue the FAT past Cutting, or
**(2)** amend the business rule to accept the current quantity-pool model (then I'd just flip
`ENFORCE_ALLOCATION_BOUND` on + fix the pair-validation gap and continue). Also tell me whether
to reuse 3-PATTI-013 or start a fresh cert adda for the post-Cutting stitching run.

