---
id: s3-design-receipt-2026-06-14
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# S3 Design Receipt — good / alter / missing + constraint sequencing (2026-06-14)

**Architecture checkpoint, NOT a coding task.** Scope locked by owner: **thin slice —
columns + resolver only; worker report UI UNCHANGED.** Governed by
[PRE_S1_DESIGN_ADDENDUM](PRE_S1_DESIGN_ADDENDUM.md) + [MASTER_PLAN_V2 §Sprint 2/S3 + RC-3](IMPLEMENTATION_MASTER_PLAN_V2.md).
No code until approved.

## 0. What S3 is (and is NOT)
S3 establishes the **production-truth data model** for good/alter/missing and the
**migration path** — nothing more.

- **IS:** add `good_quantity` / `alter_quantity` / `missing_quantity` to
  `WorkerStageContribution`; swap the legacy positivity constraint (RC-3); dual-write
  `reported_quantity = good_quantity`; migrate reads → `good_quantity`; golden fixtures
  incl. non-zero alter+missing.
- **IS NOT:** worker-UI capture of alter/missing (stays one quantity = good);
  allocation bound `good+alter+missing ≤ allocation` (that's **S4/S5** — crystallize-at-
  complete enforcement); the M-6 finalize BLOCK (S5); `reported_quantity` drop (**S6**,
  one-way, soak-gated). Recovered-alter / reappeared-missing **pay nothing** here — the
  S4 pool accessors (`recovered_alter`, `found_missing`) return 0 until the Rework/Missing
  modules ship (addendum M-7).

## 1. Locked semantics (addendum)
- `good_quantity` = the payable-good count. `alter_quantity` / `missing_quantity` =
  **immutable count observations** at the stage's grain. Soundness limit (documented):
  count-based netting is valid only **same-stage, same-grain, same-Adda**.
- **Settlement pays `good`** (via the resolver), never the raw claim — this is the B-1
  leak fix (pay 105 good, not 120 claimed).
- In the **thin slice** (no separate capture): `good = the one quantity the worker
  submits`, `alter = 0`, `missing = 0`. The numbers only diverge once the future
  Missing/Alter modules observe defects — S3 just makes the columns exist + settle
  against `good`.
- Relationship is **NOT** constrained to `good+alter+missing = reported` — `good` is the
  payable, alter/missing are independent observations (future modules may set them without
  reducing a stored claim). S3 only constrains each ≥ 0 and the sum > 0.

## 2. Schema + migration plan (RC-3, ONE migration; gates MT-1, MT-7)
`WorkerStageContribution` (all `Decimal(12,2)`, matching `reported_quantity`):
| field | null | default | note |
|---|---|---|---|
| `good_quantity` | NO (after backfill) | — | payable-good; dual-written = reported until S6 |
| `alter_quantity` | NO | 0 | immutable observation |
| `missing_quantity` | NO | 0 | immutable observation |

**Single migration, ordered (RC-3 "same migration"):**
1. `AddField good_quantity (null=True)`, `alter_quantity (default=0)`, `missing_quantity (default=0)`.
2. `RunPython` **batched backfill** (`.iterator()` + chunked `bulk_update`, prod-scale safe):
   `good_quantity = reported_quantity` for **all** rows; alter/missing stay 0. Reverse = no-op.
3. `AlterField good_quantity → null=False`.
4. **`RemoveConstraint wsc_reported_quantity_positive`** (the legacy `reported > 0`).
5. **`AddConstraint wsc_gam_nonneg_sum_positive`**: `good≥0 ∧ alter≥0 ∧ missing≥0 ∧ (good+alter+missing) > 0`.

`reported_quantity` stays `NOT NULL` (dual-written) but is **allowed to be 0** in the
allocation era (good=0, all alter/missing) — which is exactly why the old `reported>0`
check must be dropped in the same migration (else a good=0 row fails on insert).

**MT-1:** DB backup taken + restore-tested before this runs (Decimal column adds + a
batched backfill on a prod-scale dump). **MT-7** per the gate table.

## 3. Dual-write strategy (RC-3)
Every WSC write sets **`reported_quantity = good_quantity`** (both populated, equal)
until S6. In the thin slice the worker submits one number → `good = submitted`,
`reported = good`, `alter = missing = 0`.
- `report_contributions`: write `good_quantity = line['reported_quantity']` (the input
  key stays — worker UI unchanged), `alter=0`, `missing=0`, `reported_quantity = good`.
- `save_draft_contributions`: unchanged (delegates to `report_contributions`).
- **Invariant (tested):** for every row through S3→S5, `reported_quantity == good_quantity`.
- The capture **input key** in the stage `contribution_schema` (`'reported_quantity'`)
  is a UI/form contract → **unchanged**; the service maps it to `good_quantity`.

## 4. Resolver transition (the one money line)
`settlement_resolver.STAGE_GOOD`:
```
verified_quantity if set else good_quantity      # was: else reported_quantity
```
`good_quantity` is `NOT NULL` + backfilled, so no `reported` fallback is needed. Because
backfill + dual-write guarantee `good == reported`, this is **behavior-preserving** — the
golden ₹225 supersede chain must reconcile **byte-identical** (the merge gate).

**Read-site sweep (master plan "reads → good_quantity"). Functional sites to migrate:**
| site | change |
|---|---|
| `settlement_resolver.settlement_quantity` | `reported` → `good` (money) |
| `worker_task_service.complete_worker_task` | `expected_earning = good × rate` |
| `stage_rate_service.rerate_stage_role` | `expected_earning = good × rate` |
| `payroll_service` pieces stat (`Σ reported`) | `Σ good_quantity` (the 120-vs-105 display fix; good=reported now → unchanged) |
| `worker_report_views` display qty | `good_quantity` (display) |
| `WorkerStageContribution.__str__` | `good_quantity` |

A full `grep reported_quantity` sweep at implementation confirms completeness; each
site is behavior-preserving today (good==reported).

## 5. Golden fixtures (the proof the split is correct)
1. **Existing ₹225 golden — byte-identical** (good=reported, alter=missing=0). Merge gate.
2. **NEW: non-zero alter+missing golden.** A contribution with `good=105, alter=10,
   missing=5` (set directly — simulates the post-Missing/Alter world the UI can't yet
   produce) → settlement pays **105** (not 120). Proves the resolver + settlement math
   honor `good` and that the B-1 leak is structurally closed. Variant: `verified=100` set
   → pays **100** (management trump preserved).
3. **RC-3 proof test (mandatory):** insert a WSC with `good=0, alter=3, missing=2`
   (sum=5>0) → **succeeds** under the new constraint; would have FAILED the dropped
   `reported>0` check. Confirms the constraint swap + that an allocation-era "only good
   set (=0)" insert is legal. Run on a prod-scale dump (no failure) per the master plan.
4. **Dual-write invariant test:** after `report_contributions`, `reported == good`.

## 6. Rollback + compatibility
- **Rollback (S3 is reversible — unlike S6):** reverse migration drops the new
  constraint, re-adds `wsc_reported_quantity_positive`, drops the three columns. Safe in
  S3 because no row has `good=0` yet (no alter/missing capture) → `reported == good > 0`,
  so the re-added `reported>0` holds. Services/resolver revert to `reported`. Forward-only
  caveat: reverting discards good/alter/missing data, but `reported` (preserved, immutable)
  **is** the truth in S3 → nothing lost.
- **Compatibility:** historical completed/settled rows → backfilled `good=reported` →
  settlement math unchanged (already-settled lines see no money change). In-flight rows →
  dual-written on their next write. Legacy reads of `reported_quantity` keep working
  through S3→S5 (dual-write keeps it valid).

## 7. Hostile-review readiness (the post-S3 attack surface)
Pre-stage the review to attack:
- **Backfill completeness** on a prod-scale dump — any completed/settled row left with
  `good` NULL → the `NOT NULL` alter fails (good catch) → migration must backfill 100%.
- **Constraint-swap atomicity** — drop + add in one migration; partial apply on failure?
  (Django wraps a migration in a transaction on PostgreSQL → all-or-nothing.) Verify.
- **`good=0` settlement** — a fully-alter/missing contribution pays 0; does the SWA
  earning-line writer + recon handle a 0-qty line cleanly (no div-by-zero, no skip)?
- **Dual-write drift** — any WSC write path that sets `reported` but not `good` (or vice
  versa) breaks the invariant. Sweep every writer (the single chokepoint helps).
- **expected_earning semantics** — now `good × rate`; confirm no reader assumes it equals
  `reported × rate` once they can diverge (post-Missing/Alter).
- **Read-site completeness** — did the sweep miss a `reported_quantity` reader (reporting,
  admin, export)? Grep + the 18-site checklist.
- **Resolver `good` NOT-NULL assumption** — if any completed row reaches the resolver with
  `good` NULL (backfill gap), the resolver returns NULL → settlement math breaks. The
  NOT-NULL constraint is the guard; the review confirms it can't be bypassed.

## Migrations / files touched (preview — for scope, not built)
- `production/migrations/0039_*` — the RC-3 schema + constraint swap + batched backfill.
- `production/models/worker_task.py` — 3 fields + constraint swap + `__str__`.
- `production/services/worker_task_service.py` — dual-write in `report_contributions`;
  `complete_worker_task` freezes `expected_earning = good × rate`.
- `production/services/stage_rate_service.py` — `rerate_stage_role` recalc → `good`.
- `expense/services/settlement_resolver.py` — the one resolver line.
- `expense/services/payroll_service.py` + `production/views/worker_report_views.py` — read migration.
- Tests: new non-zero alter/missing golden + RC-3 proof + dual-write invariant + the
  byte-identical ₹225 gate.
- DOCS-SYNC: FILE_MAP, GUIDE, worker_task chokepoint, model docstring, PENDING_BACKLOG,
  CLAUDE.md, ARCHITECTURE_V2 §5 (truth model).

---
**STOP — awaiting approval of this design before any S3 code.** Open questions for you, if
any: (a) confirm `good_quantity` **NOT NULL** (vs nullable like `expected_*`) — I recommend
NOT NULL since dual-write always populates it and the resolver depends on it; (b) confirm
the payroll "pieces" stat should move to `good` now (display) vs stay on `reported` until
the Missing/Alter UI ships.
