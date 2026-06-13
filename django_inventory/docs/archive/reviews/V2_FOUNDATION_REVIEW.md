> **📦 ARCHIVED 2026-06-12.** Historical record — do not update.
> Superseded by / live truth: [docs/ARCHITECTURE_V2.md](../../ARCHITECTURE_V2.md) (F1 attributes-JSONB lock recorded there).

# V2 Foundation Review — stage-agnostic & future-proof assessment

> Requested 2026-06-09: review the V2 foundation assuming **stage definitions will evolve, stages will be
> renamed/split/merged, Missing-Pieces + Alter/Rework become first-class domains, and reporting grows**.
> Architectural feedback only — not implementation. Companion to [ARCHITECTURE_V2.md](ARCHITECTURE_V2.md)
> §11 (🔒LOCKED) + [V2_1_REVIEW.md](V2_1_REVIEW.md).

## 🔒 LOCKED DECISIONS (owner, 2026-06-09)
- **F1 → lock the pattern, DEFER the column.** No speculative schema today.
  - Contribution rendering stays stage-driven via **`StageHandler.contribution_schema()`**.
  - **`WorkerStageContribution` is the canonical production-contribution entity.**
  - Future stage-specific attributes belong to the **contribution-schema layer**, never hardcoded into a
    stage implementation.
  - **Only if** a future stage needs an attribute the current model can't represent do we add a nullable
    `attributes` JSONB — via an additive migration, at that time. (Avoid a generic JSON dumping ground; avoid
    designing for hypothetical stages.)
- **Cutting is a REFERENCE implementation of the framework, not the final shape of any stage.** A larger
  stage-taxonomy review (stages, machine sub-stages, costing, missing/alter, reporting, settlement deps)
  happens later. Everything built now must stay stage-agnostic / open-closed / config-driven.
- **Confirmed: no remaining gap forces a schema rewrite.** With F1 handled as a locked-pattern-+-deferred-
  column, every future need (stage redesign · new contribution schemas · Missing-Pieces domain · Alter/Rework
  domain · machine sub-stages · reporting · settlement refinements) is reachable by an ADDITIVE change off
  the already-captured adda/stage/worker/colour/size grain. Seam-by-seam confirmation in §2 + §5 below.

## Verdict (TL;DR)
The foundation is **sound and largely future-proof.** Production-truth ≠ financial-truth, the immutable
ledger, the data-driven stage/skill/assignment model, and the settlement design all hold up against the
"stages will change" stress test. **Almost every future need is an ADDITIVE change (a nullable column, a
new child table, a new handler) — NOT a rewrite.**

**One real gap to lock now:** `WorkerStageContribution` is currently **cutting-shaped** (dedicated
`color`/`size`/`bundle_item` + a single `reported_quantity`). For stages that measure *other* things (roll
weight, fabric length, machine hours, defect count, QC attributes, packing qty) there is **no home**. The
fix is small and additive (a stage-specific `attributes` slot driven by the stage's `contribution_schema`),
but it should be the **locked extension pattern** before more stages exist. Details in Finding F1.

Everything else = healthy seams. Specifics below, answering your 5 questions.

---

## 1. Foundational weaknesses

### F1 — Contribution model is cutting-shaped (the one that matters) 🟠
`WorkerStageContribution` = `color` + `size` + `reported_quantity` + `bundle_item` + frozen `expected_*`.
That fits Cutting/Layering. It does **not** carry roll-weight, fabric-length, machine-hours, defect-count,
operation-count, packing-qty, or QC attributes. Three sub-issues:
- **(a) No stage-specific attribute slot.** A stitching/QC/packing stage has nowhere to store its own
  measures. → **Seam: add a nullable `attributes` JSONField** (Postgres `JSONB`), populated per the
  handler's `contribution_schema`. Additive, no rewrite. Recommend locking this pattern now (even if the
  column is added when the first non-cutting stage lands).
- **(b) `reported_quantity` is `NOT NULL` + `> 0`.** Assumes every contribution has exactly one positive
  primary measure. A stage with no single "quantity" (pure QC pass/fail, or hours-only) breaks the
  constraint. → Treat `reported_quantity` as **"the stage's billable measure"** (pieces / hours / kg / m).
  If a future stage has none, the `>0` check forces a migration. Low risk; flagged.
- **(c) `bundle_item` is a cutting concept on the generic model.** Harmless (nullable), but it's a leak.
  Acceptable; if it bothers later, fold piece-precision into `attributes`.

**Why this is not a crisis:** color/size stay as **common dimensional columns** (the owner-locked,
un-backfillable grain that color/size-wise reporting + missing/alter tracing depend on). The *only* missing
piece is the open-ended attribute slot — and adding a JSONField is a one-line additive migration. So the
foundation is safe; we just must commit to the pattern.

### F2 — `expected_earning = qty × rate` assumes piece-rate pay 🟡
The freeze formula (`complete_worker_task`) is piece-rate. Time-rate (hours × hourly) works if `qty` = hours.
But **fixed-fee** or **tiered** pay has no per-unit rate. → The *fields* are fine (`expected_rate` nullable;
`expected_earning` is the stored truth — a fixed-fee stage sets earning directly, rate null). Only the
**computation** varies → it belongs in the stage handler / a pay-policy, not hardcoded. Flag: keep the
earning computation swappable per stage; don't bake piece-rate into the core.

### F3 — No weaknesses found in the parts that would be expensive to fix
Production/financial separation, immutable ledger, single-writer discipline, dual-write chokepoint,
assignment isolation, settlement (Option B / Model A / frozen item) — all structurally sound.

---

## 2. Missing extension points (seams)

| Future need | Seam status | Note |
|---|---|---|
| **Stage-specific contribution data** | ⚠ **ADD** (F1) | nullable `attributes` JSON + `contribution_schema` hook |
| **Per-stage render of the report form** | ✅ planned | `StageHandler.contribution_schema(adda)` (V2-1c-iii pt.2) |
| **Missing-Pieces domain** | ✅ present | FK to adda/stage_record/**color/size** (the locked dims) + `WorkerStageTask` anchor; contributions immutable once completed → traceable. Settlement consumes a summary (§11.10/11.11) |
| **Alter/Rework domain** | ✅ present | same anchors + defect_type/defect_stage on the future `AlterCase`; dims already captured |
| **Machine / QC SUB-stages** | 🟡 partial | `WorkflowStage` is a **flat ordered list** — no parent/child. Hierarchical sub-stages would need a nullable `parent` FK on WorkflowStage (additive) OR model sub-stages as ordinary stages. Decide when first needed |
| **Settlement ↔ contribution audit link** | 🟡 optional | `AddaSettlementItem` ties to a settlement SWA, not directly to the contributions it settled. A direct link aids "which lines did this settlement pay" (additive) |
| **New stage end-to-end** | ✅ open-closed | new `Stage` row + skill mapping + handler folder; registry auto-discovers; **zero edits** to auth/costing/dispatch (proven by the M2.10 open-closed test) |

---

## 3. Future redesign risks (ranked)

1. **F1 (contribution attributes)** — if we keep adding stage data into ad-hoc columns instead of the
   `attributes` seam, the table bloats + each stage becomes a migration. **Mitigation: lock the JSON-attributes
   + `contribution_schema` pattern now.** Risk after mitigation: low.
2. **Stage rename/split/merge** — `Stage.code` is the stable key, `Stage.name` the display (already
   separated ✅). **Renaming = change `name`, keep `code` → no break.** Splitting/merging = a data migration
   (unavoidable for ANY model; not a foundation flaw). Risk: low, *provided* code is never treated as the
   display label. **Discipline to hold: `code` is immutable identity; never rename a code, never show it as
   the human name.**
3. **Sub-stage hierarchy** — flat `WorkflowStage.order` can't express "Cutting → machine A / machine B"
   as children. Additive `parent` FK later. Risk: low (additive).
4. **Pay model beyond piece-rate** (F2) — swappable computation needed. Risk: low (fields already generic).
5. **Reporting on stage-specific measures** — depends entirely on F1's `attributes` existing (you can't
   report on machine-hours you never stored). Risk folds into F1.

---

## 4. Assumptions that could force schema rewrites — and whether they hold

| Assumption baked in today | Could it force a rewrite? | Verdict |
|---|---|---|
| Every contribution has color/size (or null) | No — they're nullable common dims | ✅ safe |
| Every contribution has one positive `reported_quantity` | Only if a stage has no measure at all | 🟡 watch (F1b) |
| Contribution data = color/size/qty | **Yes, IF no attributes seam** | ⚠ add JSON seam (F1) |
| Pay = qty × rate | No — earning is stored; formula swappable | ✅ safe (F2) |
| Stages are a flat ordered list | Only if sub-stage hierarchy needed | 🟡 additive `parent` FK |
| `Stage.code` is stable identity | No — code≠name already | ✅ safe (hold discipline) |
| Ledger is the only money truth, written at settlement | No — this is the strength | ✅ safe |
| Missing/rejected/alter are settlement counts now | No — source-agnostic seam; modules feed later | ✅ safe |
| Access = Skill ∧ Assignment, data-driven | No — new stages need no auth code | ✅ safe |

**Net: exactly one assumption (contribution = color/size/qty) carries real rewrite risk, and its fix is a
single additive JSON column. No other assumption forces a rewrite.**

---

## 5. Is the foundation truly stage-agnostic & future-proof?

| Layer | Stage-agnostic? |
|---|---|
| `WorkerStageTask` (lifecycle + assignment) | ✅ fully — no stage-specific fields |
| Stage engine (registry / handlers / per-stage folder) | ✅ open-closed (M2.10 proven) |
| Access (Skill ∧ Assignment, data-driven) | ✅ new stage = data + handler, no auth change |
| Settlement / ledger / advances (financial truth) | ✅ stage-agnostic (reads completed contributions + dims) |
| `save_draft` / `complete` services | ✅ already take generic `lines` (optional color/size/qty/bundle_item) |
| `WorkerStageContribution` (storage) | 🟠 **partly** — generic qty + common dims, but **no stage-specific attribute slot** (F1) |
| Report UI render | ⚠ becomes agnostic once `contribution_schema` hook lands (planned) |

**Conclusion:** The foundation **is** stage-agnostic everywhere except the contribution *storage* schema,
which is cutting-shaped. Close that one gap (the `attributes` seam + `contribution_schema` hook) and the
foundation is genuinely future-proof: stages can be renamed (code≠name), added (open-closed), split/merged
(data migration), and gain machine/QC/rework sub-flows (additive), and Missing-Pieces + Alter/Rework can
become first-class domains hanging off the already-captured adda/stage/worker/color/size grain — **all
without a schema rewrite.**

---

## Recommended foundation actions (before deeper build)
1. **LOCK the contribution-extension pattern (F1):** stage-specific data → a nullable `attributes` (JSONB)
   on `WorkerStageContribution`, declared + rendered via `StageHandler.contribution_schema(adda)`. Add the
   column now (cheap seam) or at the first non-cutting stage (additive) — but commit to the pattern so no one
   adds ad-hoc per-stage columns. Document it like the `credits_workers`-placement lock.
2. **Write the discipline down:** `Stage.code` = immutable identity, `Stage.name` = display (renaming-safe);
   earning computation lives in the stage/pay-policy, not the core; missing/rejected/alter always flow
   through the settlement *summary* seam, never a competing money path.
3. **Note the deferred-but-additive seams** (no build now): WorkflowStage `parent` FK (sub-stages),
   settlement↔contribution audit link, verified-attributes for manager corrections of non-qty measures.
4. Proceed with V2-1c-iii pt.2 (worker report UI) **built on `contribution_schema` from day one**, so the
   very first wired screen is already stage-driven, not cutting-hardcoded.
