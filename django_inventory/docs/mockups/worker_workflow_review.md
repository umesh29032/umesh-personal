# Worker Self-Report — Workflow Review (V2-1c-iii)

> Companion to [worker_report.html](worker_report.html) (the screen mockup) + [../V2_1_REVIEW.md](../V2_1_REVIEW.md).
> **Status: PAUSED for owner review BEFORE wiring.** Maps the worker workflow to the V2 architecture across
> the 8 dimensions you asked to validate. Legend per item: **[BUILT]** in code (committed) · **[MOCKED]** in
> worker_report.html · **[TO-DESIGN]** decision needed · **[TO-WIRE]** code to write after approval.

---

## 1. Worker journey (end-to-end)
```
login → DASHBOARD (only my assigned Addas/stages)         [BUILT V2-1b/1c-iv]
      → open an assigned stage  → STAGE PANEL              [BUILT gate; TO-WIRE the report UI]
           → enter contribution lines (colour/size/qty)   [MOCKED]
           → Save draft   (keep editing later)            [BUILT service; TO-WIRE]
           → Submit & complete (freeze + lock)            [BUILT service; TO-WIRE]
      → stage shows "done for me"; manager advances when ALL workers done   [BUILT readiness rule; TO-WIRE indicator]
      → earnings appear later via My Earnings + Adda settlement (V2-2)       [later wave]
```
- **What's solid:** the worker only ever sees their own assigned work (isolation), and money never appears on the report path (Option B).
- **Open:** does the worker reach the report screen via the **dashboard accordion (embedded panel)**, the **standalone stage panel**, or both? (Today both routes exist; the report UI drops into the same panel.) → decision D1.

## 2. Draft vs Submit & Complete  [BUILT + tested]
| | Save Draft | Submit & Complete |
|---|---|---|
| Service | `save_draft_contributions` (replace) | save lines → `complete_worker_task` (freeze) |
| Task status | `in_progress` (`is_draft = True`) | `completed` (`is_draft = False`) |
| Editable by worker? | yes (replace anytime) | **no** — locked |
| In costing/settlement/earnings/readiness? | **excluded** | included |
| Lines | deletable (not history) | frozen `expected_rate` + `expected_earning` (immutable) |
- **Principle honoured:** drafts = operational convenience; **business truth begins at Submit & Complete.** No draft engine, no new table.
- **Open:** can a worker **re-open their OWN completed task** to fix a mistake, or is that manager-only? (Current design: worker locked after submit; only manager corrects.) → decision D2.

## 3. Assignment visibility  [BUILT V2-1b + V2-1c-iv]
- Dashboard `my_active_stages` + `active_addas` are scoped to **the worker's active `WorkerStageTask`** — a worker sees ONLY Addas/stages they're assigned to.
- A skilled-but-unassigned worker **cannot open** a stage panel (403) — the V2-1c-iv security gate.
- **Open:** should the dashboard show a clear **"⏳ Report needed"** badge on stages awaiting the worker's submission (vs already-submitted)? Mockup doesn't cover the dashboard list. → decision D3 (a small dashboard badge).

## 4. Contribution line entry (colour / size / qty)  [MOCKED]
- One line card per colour+size; colour chip-picker (swatch dots) + size chip-picker + cream qty input; `+ Add line`; per-line remove.
- **Data sources (to wire):** colour chips = the Adda's cloth colours; size chips = the product's `ProductSize` set. `bundle_item` (piece precision) is optional/cutting-only — **not** shown in the worker mockup (kept simple). → confirm D4.
- **Open:** are colour/size **required** on every line, or allowed blank for "dimensionless" stages (e.g. a stage with no colour split)? Model allows null; mockup assumes both chosen. → decision D4.

## 5. Locking behaviour after submit  [BUILT rule; TO-WIRE view]
- After Submit & Complete: worker sees a **read-only** version of their lines (no inputs, no buttons) + a "Submitted ✓" state. `save_draft_contributions` / `complete_worker_task` both reject further worker edits.
- **TO-WIRE:** the locked/read-only rendering of the same panel (mockup currently shows only the editable state). → I'll add a locked state to the mockup if you want to see it (D5).

## 6. Manager edit / correction flow  [model BUILT; UI TO-DESIGN]
- The model supports it: `verified_quantity` (manager/super_admin only) is the correction channel — the worker's `reported_quantity` stays as the immutable claim; the manager's correction lives beside it.
- Manager also bypasses the assignment gate (can open any panel) and could re-open a completed task (super_admin reopen exists for stages).
- **TO-DESIGN:** the manager correction UI (set `verified_quantity` per line) — likely a manager-only column on the same panel, or a separate review screen. Not in this mockup. → decision D6 (defer to a manager-review sub-step?).

## 7. Mobile usability (factory workers on phones)  [MOCKED]
- Form-shell is responsive: line cards stack, chip rows wrap, qty inputs full-width-friendly, sticky CTA pins to the bottom and goes full-width on small screens (matches `_form_styles.html` breakpoints).
- Big tap targets (chips are pill buttons; qty is a large numeric input).
- **Open:** worker phones often = numeric keypad — qty input is `type="number"` (numeric keypad). Confirm chip tapping vs a native select is preferred on small screens. → decision D7.

## 8. Readiness / completion indicators  [rule BUILT; indicator TO-WIRE]
- Stage advance gate (V2 §3): **`ready_for_advance` = all active tasks `completed`** (verification NOT required). Draft/in-progress tasks block advance — so a worker's unsubmitted draft correctly holds the stage.
- **TO-WIRE:** a per-stage progress indicator for the manager ("3 / 5 workers submitted") on the stage panel / adda detail, derived from `WorkerStageTask` statuses (no stored counter).
- **Open:** show the worker a simple **"You're done — waiting on others"** vs a count? (Worker should NOT see other workers' details — only "submitted, waiting for the stage to advance".) → decision D8.

---

## Decisions — RESOLVED (owner, 2026-06-09)
- **D1 → BOTH routes** — dashboard-embedded panel + standalone stage panel (same report UI in both).
- **D2 → Worker CANNOT re-open** a completed task. Corrections are manager/super-admin only.
- **D3 → Dashboard badges:** `Report Needed` (assigned, no submission) · `Draft Saved` (in_progress draft) ·
  `Submitted` (completed). Derived from the worker's `WorkerStageTask` status + whether draft lines exist.
- **D4 → colour/size requirement is STAGE-DRIVEN, not globally hardcoded** (see open-closed note below);
  `bundle_item` does NOT appear in the worker UI.
- **D5 → DONE** — locked/read-only state added to the mockup (STATE ②) for review.
- **D6 → Manager correction UI DEFERRED** to a later step; the `verified_quantity` model support suffices now.
- **D7 → Keep chip selectors** (better than dropdowns for factory workers on mobile).
- **D8 → No other-worker progress shown.** Worker sees only: *"Your work report has been submitted. Waiting
  for stage completion."* (manager gets the N/M progress, not the worker).

## Open-closed: the report form is STAGE-DRIVEN (owner architectural requirement)
This mockup is the **Cutting** stage's contribution schema (colour + size + qty). It is **not** a universal
form. The stage engine must stay open-closed: a future stage declares its own contribution fields without
editing the worker view. **Wiring plan to honour this:**
- The `StageHandler` gains a `contribution_schema(adda)` (or similar) hook returning the fields/options for
  that stage (Cutting → colour options + size options + qty; another stage → its own). Default = qty-only.
- The worker view + template render fields **from the handler's schema**, not a hardcoded colour/size form.
- `save_draft_contributions` / `complete_worker_task` already take generic `lines` (colour_id/size_id/qty/
  bundle_item_id all optional) — so the service layer is already stage-agnostic; only the **render** must be
  handler-driven. (This is a small addition to the registry, consistent with the M2 stage-engine.)

## Settlement wording (owner-approved, used in both states)
> "Your work report has been submitted. This report will be used for production tracking and future Adda
> settlement. Payment is processed separately."

## What I will build once the locked state is approved (V2-1c-iii pt.2 — TO-WIRE)
- **Stage `contribution_schema` hook** on the handler (Cutting returns colour/size/qty) — keeps it open-closed.
- **Form/view** (assignment-gated; Save Draft → `save_draft_contributions`, Submit & Complete → save +
  `complete_worker_task`); worker-reopen blocked (D2).
- **Template** = approved mockup, both states (editable + locked), rendered from the handler schema; reachable
  via dashboard-embedded + standalone (D1).
- **Dashboard badges** (D3): Report Needed / Draft Saved / Submitted.
- **Tests** (draft save/replace, submit freeze+lock, worker-reopen blocked, isolation, schema-driven render).
- **No new models/migrations** — backend (model, services, draft, freeze, isolation) already committed.
- **Deferred:** manager correction UI (D6); manager N/M progress indicator (D8 manager side).
