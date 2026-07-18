> **ARCHIVED 2026-07-13** — 2026-06 production-readiness audit; findings closed, superseded by the current frozen architecture ([../../MANUFACTURING_V1_FREEZE.md](../../MANUFACTURING_V1_FREEZE.md)). Kept for history (Phase-7 DOCCLEAN-D).

# Financial Policy Decisions — B-1, A-5, B-3 (decision-support, not implemented)

Three business-policy choices to lock before UX work. Each: recommended solution → alternatives → pros/cons → effort → long-term impact on the garment workflow. Evidence is in [PHASE_B](PHASE_B_costing_financial.md).

---

## B-1 — Output reconciliation policy

**Problem (proven):** workers were paid for 120 pieces; cutting recorded 105 (`pieces_cut`). ₹45 paid for 15 non-existent pieces. Finalize never compares Σ(worker reports) to the stage's own output.

### Recommended — **Option 1: Finalize-time reconciliation gate (hard-warn, override-with-reason)**
At finalize, compute Σ(billed contributions) per stage and compare to the stage handler output (`pieces_cut` / `lay_count` / bundle count — the system already stores it). If they differ beyond a tolerance (e.g. >2% or >N pieces), **block** with the exact numbers; allow a management **override that records a reason** (audit trail).
- **Pros:** catches the leak at the one money moment; zero per-line manual work; uses data already captured; override keeps legitimate cases (re-cut, scrap) unblocked but logged.
- **Cons:** needs a per-stage "expected output" accessor; tolerance is a tuning decision; override can be rubber-stamped if undisciplined.

### Alternatives
- **Option 2: Mandatory verification on every payable contribution before finalize.** Block finalize until each line has a `verified_quantity`.
  - *Pros:* strongest control; forces a human to look at every number. *Cons:* heavy daily friction for a small team; the reason it's optional today; doesn't itself compare to physical output (a manager could still verify-to-a-wrong-number).
- **Option 3: Soft-warn only.** Show "reports 120 vs output 105" on the draft screen; allow finalize freely.
  - *Pros:* zero friction, full visibility. *Cons:* warnings get ignored; the ₹45 still leaks; relies on discipline.
- **Option 4: Keep current (no reconciliation).** *Pros:* nothing to build. *Cons:* silent, repeatable over-pay; fraud vector; understated true labor cost.

**Effort:** Option 1 = **M** · Option 2 = **M–L** (UI + workflow) · Option 3 = **S** · Option 4 = none.

**Long-term impact:** as stages multiply (stitching/finishing/packing/G1-G7) and headcount grows, un-reconciled piece-rate pay compounds — every new payable stage is a new leak surface. A reconciliation gate is a **reusable invariant** that every future stage inherits for free (the handler already reports output). Without it, payroll trust degrades exactly as the factory scales. Option 1 is the scalable floor; Option 2 layers on top only if fraud risk proves high.

---

## A-5 — Unpriced-stage settlement policy

**Problem:** an unpriced payable stage freezes `processing_cost = NULL` and pays workers **₹0** silently; production and settlement both proceed.

### Recommended — **Option 1: Block the MONEY event, not the floor**
Keep production progression unblocked. **Block `create_draft`/`finalize`** when any `credits_workers=True` stage on the Adda has `cost_rate IS NULL`: "Cutting is unpriced — set a rate before settling." Keep/strengthen the flow-editor "unpriced" badge as the early warning.
- **Pros:** converts a silent ₹0-payout into a caught, fixable error at the moment money is booked; floor never stops for a pricing oversight; one guard, cheap.
- **Cons:** an Adda can be fully produced before anyone notices the missing rate (caught at settlement, not at stage start).

### Alternatives
- **Option 2: Block stage progression until priced.** Can't start/complete an unpriced payable stage.
  - *Pros:* impossible to do unpriced work. *Cons:* halts the production floor for an admin oversight — bad for a running factory; couples pricing-admin to shop-floor flow.
- **Option 3: Warn only (louder).** Banner on the Adda + settlement screen; still allow ₹0 settle.
  - *Pros:* no blocking. *Cons:* ₹0-payout still possible; workers can be silently unpaid.
- **Option 4: Keep current (silent ₹0).** *Cons:* worst — workers unpaid without signal, product under-costed.

**Effort:** Option 1 = **S–M** · Option 2 = **M** (touches every stage start/complete) · Option 3 = **S** · Option 4 = none.

**Long-term impact:** the workflow is explicitly designed to add stages over time (TM-1, new production teams). Each new stage is a fresh chance to forget a rate. Blocking at the money event (Option 1) means **every future stage is safe by default** without constraining the floor — the right separation of "production truth" from "money truth" that the codebase already follows (Option B / settlement-first). Option 2 fights that separation.

---

## B-3 — Variance policy (missing / rejected pieces)

**Problem:** `variance_policy` field exists with choices but is **read nowhere**; finalize hardcodes `factory_absorbs` (variance_amount = 0). Missing **and rejected/defective** pieces are always paid in full. No lever to deduct.

### Recommended — **Option 1: Make the field real — `factory_absorbs` (default) + `deduct_rejected`**
Keep `factory_absorbs` as default (current behavior, no surprise). Add a `deduct_rejected` policy that subtracts `rejected_quantity × rate` from the worker's expected at finalize (missing still absorbed — missing ≠ worker's fault; rejected = quality fault). Surface the chosen policy + the deduction on the settlement screen.
- **Pros:** gives the owner a real quality lever without changing today's default; the variance counts are already captured (just unused); transparent.
- **Cons:** raises "who owns the reject?" disputes (cutting vs stitching defect attribution); needs a policy selector in the UI.

### Alternatives
- **Option 2: Document factory-absorbs as the deliberate rule; remove the dead field.** Make the code honest: one policy, clearly intended.
  - *Pros:* simplest; no false affordance. *Cons:* permanently forecloses deducting rejects — every defective piece is paid forever.
- **Option 3: Always deduct rejected (no policy choice).** Defects never paid, factory-wide.
  - *Pros:* strongest quality incentive. *Cons:* blunt; punishes workers for upstream/material defects they didn't cause; attribution problem.

**Effort:** Option 1 = **M** (branch + UI selector) · Option 2 = **S** (delete field + doc) · Option 3 = **M** (branch, no selector).

**Long-term impact:** garment quality control becomes material as volume grows and as finishing/QC stages (G1-G7) come online — that's where "rejected" becomes a real, attributable number. A working `variance_policy` (Option 1) lets quality economics be tuned per the factory's maturity without a rewrite. Option 2 is fine **if** the owner is certain the factory will always absorb defects; otherwise it's a door bricked shut. Note: deduction only makes sense paired with B-1 (you must trust the reject *count* before you deduct on it).

---

## The three decisions (summary)

| # | Decision | Recommended | If yes, effort |
|---|----------|-------------|----------------|
| B-1 | Output reconciliation | Finalize-time gate, hard-warn + logged override | M |
| A-5 | Unpriced stage | Block finalize (not production) | S–M |
| B-3 | Variance | Make field real: absorb default + deduct_rejected option | M |

**Dependency:** B-3 deduction is only trustworthy *after* B-1 (don't deduct on reject counts you haven't reconciled). Suggested order: **B-1 → A-5 → B-3.**
