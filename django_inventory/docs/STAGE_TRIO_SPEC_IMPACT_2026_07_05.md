---
id: stage-trio-spec-impact-2026-07-05
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# Stage-Trio Spec — impact analysis (Layering → Pattern Design → Cutting)

> Owner business specification 2026-07-05 (10 sections) = the gating spec the
> roadmap was waiting on for R8/R9, PLUS a rename and a layering-payment
> reversal. **Analysis only — nothing implemented.** This document is the
> spec-of-record; the roadmap R8/R9 entries now point here. Because it changes
> workflow/payment rules, it functions as the owner-approved **PDD §15/§16
> amendment** (PDD change control: owner spec = the approval; PDD text itself
> stays frozen, this addendum governs).

## A) What ALREADY exists (verified against code 2026-07-05 — reuse, don't rebuild)

| Spec requirement | Existing implementation | Verdict |
|---|---|---|
| §2 layering production inputs (layers, colour-wise via rolls, roll usage/breakdown, wastage, layer length) | `LayeringRecord` + `LayeringRollEntry` (per-roll layers/width/weight) + `RemainingClothOfClothRoll` (mandatory leftovers) + colour from roll's cloth | **REUSE as-is** |
| §2 monthly workers can report | R4: reporting is pay-agnostic (browser-proven) | **REUSE** |
| §3 "Product's Pattern Designs" checklist data | `ProductPattern` → `ProductPatternAssignment` → `CuttingPatternVerification` (per-pattern verified rows; the operator console already completes with "verified N/N") | **REUSE** (the checklist MODEL is built) |
| §3 optional reference images | `ProductPattern.reference_image` (per design) + `CuttingPatternPhoto` (multiple per-Adda photos, upload path exists) | **REUSE** |
| §3 fixed-per-Adda payment | `cost_method='fixed'` exists; per-Product rate via Flow Editor; freeze/settle engine unchanged (stage_earnings_flow recipe: config + schema override, zero earning code) | **REUSE** |
| §6 bundles group pattern pieces per garment size | `CuttingBundle` = "size-grouped container of cut pieces" (size header + `CuttingBundleItem` rows) — literally the requirement | **REUSE as-is** |
| §7 cutting per-piece pay | LIVE today (`credits_workers=True`, settled in production data); ₹100 test rate = Flow Editor config, no hardcode | **REUSE (config only)** |
| §4/§6 admin snapshots | `_layering_summary.html` partial (rolls/layers/lengths) already renders on dashboards + Adda detail; pattern/size/colour data all queryable | **REUSE partial + new gated blocks** |
| §8 three different workers per stage | Already structural: per-stage rosters (`WorkerStageTask` per stage_record), skill-gated stage access; nothing assumes one person spans stages | **ALREADY TRUE** (legacy layering auto-assign is the known transitional item, R3 backlog — unchanged by this spec) |

## B) What actually needs building

1. **Rename (§1)** — `Stage.name` "Cutting Pattern" → **"Pattern Design"** =
   DATA + display strings (~10 templates/docstrings) + docs.
   **Recommendation: keep the internal identifier `cutting_pattern` frozen**
   (registry key, handler package, URLs, seeded flows, 5 test modules, stage
   constants — renaming it is pure risk with zero business value; the owner's
   "where appropriate" clause). Existing Addas: display-only change ⇒ zero
   behavioral risk; verified in browser after.
2. **Pattern-master worker report → verification checklist (§3/§5)** — the one
   real feature. The phone report engine is schema-driven (`contribution_schema`
   kinds: `quantity`, `choice`); add a **`check` kind** rendering the Adda's
   `ProductPatternAssignment` rows as a tick-list (+ optional photo upload →
   `CuttingPatternPhoto`; reference images shown read-only). Submission goes
   through the SAME C-TM chokepoint: syncs `CuttingPatternVerification` via the
   existing pattern service and books ONE contribution (`good_quantity=1`) —
   fixed pay = rate × 1. Worker sees ONLY checklist + images (§5) — the report
   page is already minimal/self-scoped.
3. **Fixed-pay double-guard** — `fixed` × qty means two assigned workers each
   reporting 1 would double the fixed amount. Guard at the chokepoint: a
   `fixed`-method stage refuses a second COMPLETED report (actionable error).
   Small, single-writer intact.
4. **Layering→Pattern duration analytics (§3)** — store minutes on the pattern
   stage record at complete (`pattern_design_lead_minutes` or similar; one
   nullable column, production migration). Analytics only; also fits the
   standing auto-duration rule (2026-06-03).
5. **Admin snapshot blocks (§4/§6)** — management-gated, read-only, LIVE reads
   (no frozen tables — they're reference views, YAGNI on snapshots-as-rows):
   pattern panel gets the layering summary (reuse partial + widths/weights);
   cutting panel gets pattern-designs-completed + sizes/colours block. Workers
   never see them (template + ctx gates, leak-tested like R1 My Work).
6. **Config (Flow Editor, no code):** layering → `credits_workers=False`
   (see conflict C-1); pattern_design → `fixed`, rate per product,
   `credits_workers=True`; cutting → rate ₹100 for testing.

## C′) OWNER DECISIONS (resolved 2026-07-05)

- **C-1 → delete-and-rebuild.** Test data is NOT preserved for its own sake:
  DEV/test Addas and fixtures that conflict with the final business design are
  DELETED and recreated correctly ("business correctness > historical test
  fixtures"). Settle old layering earnings ONLY if part of a flow worth
  preserving; otherwise purge + rebuild fresh 3-PATTI data. This dissolves the
  frozen-expected problem (those Addas go away) → layering flips to
  `credits_workers=False` cleanly.
- **C-2 → display-only rename, NOW (in R8).** Internal `cutting_pattern`
  identifier frozen; every user-facing string becomes **Pattern Design**.
- **C-3 → phone checklist for workers**; operator console stays the management
  surface; BOTH write the same `CuttingPatternVerification` rows (single truth).
- **NEW REQUIREMENT — generic stage-snapshot architecture:** admin snapshots
  are NOT built per-stage. Every stage handler can expose a read-only
  `admin_snapshot`; the NEXT stage's panel automatically consumes the previous
  stage's snapshot (registry/order-driven). Standard for all future stages
  (Bundling, Sewing, Checking, Packing) and reused verbatim by Adda-360.
  Reference views ONLY — live reads, no frozen tables, no duplicated data.
  Foundation verified in code: the handler contract already has registry-driven
  `snapshot(adda)` (base/handler.py:86, consumed generically at
  adda_views.py:166) — the generic admin snapshot extends this existing seam.
- **Testing rule reaffirmed:** real 3-PATTI product/workflow only; stale
  DEV/test Addas deleted + fresh 3-PATTI test data created.

## C) Conflicts / owner decisions — original analysis (superseded by C′) ⚠️

| ID | Conflict | Options |
|---|---|---|
| **C-1** | **Layering-pay reversal.** R2 (your P-3, 2026-07-04) configured 3-PATTI layering at ₹10/layer; §2 now says layering is NOT an earning stage. **4 unsettled layering lines with frozen expected ₹ exist** (real reported work under the old rule — 3-PATTI-006/007/008 + DEV data). Flipping `credits_workers=False` makes them permanently unsettleable (stage no longer payable) while their frozen "Expected ₹" keeps showing to workers. | (a) **Settle those Addas first, then flip** (honours work done under the old rule — recommended); (b) flip now and accept phantom Expected on old lines (they never pay); (c) keep layering paying on 3-PATTI only for existing Addas — flip applies naturally to NEW Addas since payability is read per-Adda at settlement... it is NOT (credits_workers is per-WorkflowStage, product-wide) — so (c) = settle-first anyway. **Recommend (a).** |
| **C-2** | Rename scope: display-name only (recommended) vs internal identifier too (high-risk churn: registry/URLs/tests/seeds). | Recommend display-only; identifier documented as frozen legacy code. |
| **C-3** | Pattern master's surface: new phone checklist report (recommended — mobile-first rule, workers use phones) vs pointing him at the existing operator console. The checklist report SYNCS the same `CuttingPatternVerification` rows either way (one truth). | Recommend phone checklist; console remains the management surface. |

## D) The six answers

1. **Roadmap phase:** this = **R8 + R9 combined scope**, delivered as two
   sub-phases in one stream: **R8 = rename + Pattern Design redesign +
   layering config/reversal (bulk of work); R9 = cutting admin snapshot +
   ₹100 config + full 3-PATTI E2E validation** (cutting engine itself already
   pays — R9 is thin).
2. **R8/R9 redesigned?** Yes — roadmap entries re-pointed to this spec (this
   was exactly the owner-spec gate they were waiting for).
3. **A360:** stays AFTER this work (your existing sequencing). This spec makes
   A360 better — the pattern checklist and snapshots feed its worker board.
4. **Reused code:** table A — the entire pattern/verification/photo/bundle
   model layer, the earning recipe, the schema-driven report engine, the
   layering summary partial, Flow Editor.
5. **Screens changing:** worker report page (new check-kind), pattern stage
   panel (admin snapshot + label), cutting stage panel (admin snapshot),
   Flow Editor (config only), Adda detail/stage labels (rename via data),
   docs. NO settlement/payroll screen changes.
6. **Architecture conflicts:** none structural — C-1..C-3 above are business
   decisions, not architecture breaks. The earning engine, single-writer
   discipline, ADR-0009/0011, and the money-write STOP rule are untouched;
   the fixed-pay double-guard is the only new money-adjacent guard and lives
   in the existing chokepoint.

## E) Testing (§9 — new standing rule, saved to memory)
All validation on the REAL 3-PATTI workflow: fresh 3-PATTI Adda, stages
configured via Flow Editor (₹100 cutting rate as data, never hardcoded),
browser E2E through Layering → Pattern Design (checklist + images + fixed pay)
→ Cutting (bundles + per-piece pay) → settlement. No more synthetic products.

## F) `lead_minutes_from_layering` — precise current behavior (owner follow-up, R8 acceptance)

**Formula (as built, cutting_pattern/service.py `complete_pattern_stage`):**
```
lead_minutes_from_layering =
    floor( (pattern_SR.completed_at − latest_completed_layering_SR.completed_at)
           .total_seconds() / 60 ),  clamped ≥ 0
```
- **Timestamps used:** the two STAGE records' `completed_at` stamps — nothing
  worker-level. "Latest completed layering SR" = `order_by('-completed_at').first()`
  (relevant after reopen/re-complete cycles).
- **When stamped:** once, inside `complete_pattern_stage`, right after the
  pattern SR's own `completed_at` is set (same atomic txn). Re-completing after
  a reopen re-stamps (honest latest value). `None` when layering never
  completed or for pre-R8 records. ANALYTICS ONLY — no payment reads it.

**Future split (owner intent, NOT built):**
- *Waiting Time* = layering `completed_at` → worker starts.
- *Working Time* = worker starts → worker completes.
- **Gap to know now:** there is NO dedicated "worker started" timestamp today.
  Candidates when the split is built: the pattern SR's `started_at` (= stage
  opened, usually management), the worker task's assigned→in_progress
  transition (exists as a status flip, but only `updated_at` moves — not a
  dedicated stamp), or the first draft contribution's `created_at`. The clean
  future evolution = one nullable `worker_started_at` on WorkerStageTask
  stamped at the first draft/report (additive migration; current
  lead-minutes then = waiting + working by construction). Documented so the
  split lands without reinterpreting old rows.

### Verification sources
Code reads 2026-07-05: cutting.py models (ProductPattern:47,
reference_image:71, CuttingPatternPhoto:147-188, CuttingBundle:410-415,
ProductPatternAssignment:88, CuttingPatternVerification:268), cutting_pattern
handler (cost_quantity→None), worker_report_views parser kinds, layering
models/services, live 3-PATTI flow config + unsettled-line count (4).
Confidence: High.
