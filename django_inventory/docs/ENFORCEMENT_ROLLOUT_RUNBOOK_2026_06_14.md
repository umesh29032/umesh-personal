---
id: enforcement-rollout-runbook-2026-06-14
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# Enforcement Rollout Runbook — allocation bound + settlement reconciliation (2026-06-14)

Two foundation enforcement gates ship **OFF** and are enabled later, after evidence. This is
the operator procedure for turning each on safely. **Deploy with both flags OFF**; gather
evidence; resolve violations; enable.

| Flag (env) | Gate | Default | Kill-switch |
|---|---|---|---|
| `ENFORCE_ALLOCATION_BOUND` | complete refuses if Σ(good+alter+missing) > Σ allocated (per worker/stage/dims) | `False` | set `False`, no migration |
| `ENFORCE_SETTLEMENT_RECONCILIATION` | finalize refuses if a stage settled more than produced (beyond tolerance) | `False` | set `False`, no migration |
| `SETTLEMENT_RECONCILIATION_TOLERANCE` | allowed over-allocation margin (absolute pieces) | `0` | — |

Neither moves money. Both are quantity-only integrity gates. `WorkerStageAllocation` stays
production-only; settlement remains the only money boundary.

---

## A. Before enabling `ENFORCE_ALLOCATION_BOUND` (the complete-time bound)

1. **Run the pre-flip audit:**
   ```
   env/bin/python config/manage.py preview_allocation_bound          # all Addas
   env/bin/python config/manage.py preview_allocation_bound --adda <CODE>
   ```
   - Exit 0 + "Clean" → safe to enable.
   - Exit 1 → it lists every COMPLETED contribution that would be refused, each tagged:
     - **`unallocated`** — a pool-stage completion with no `WorkerStageAllocation` (allocate the
       worker, or keep the flag off until allocation is wired for that stage);
     - **`over_bound`** — Σ good+alter+missing > Σ allocated (allocate more, or correct the
       reported quantity via Review Reports).
2. **Resolve** every violation (allocate / correct), re-run until clean.
3. **Soft-warn is already live** (flag off): the worker report screen warns when a report
   exceeds the allocation — so over-allocation surfaces during the ramp without blocking.
4. **Enable:** set `ENFORCE_ALLOCATION_BOUND=True`. Only then will pool-stage completions be
   refused beyond their allocation. **Roll back instantly** by setting it `False` (no migration).

> Note (2026-06): on the current 4-stage flow there is **no piece-consuming stage downstream
> of cutting**, so this gate is normally inert. `preview_allocation_bound` may still flag legacy
> cutting contributions as `unallocated` (cutting is COLOR_SIZE but allocation isn't wired for
> it) — expected; keep the flag off until a real allocated consumer stage (e.g. stitching) ships.

## B. Before enabling `ENFORCE_SETTLEMENT_RECONCILIATION` (the finalize BLOCK)

1. **Run the pay reconciliation report:**
   ```
   env/bin/python config/manage.py reconcile_pay --all
   ```
   It lists `over_allocated` stages (settled > produced — the B-1 leak). Exit 1 if any HARD flag.
2. **Resolve** each over-allocation before enabling: correct the verified quantity (Review
   Reports), or void the over-allocation. For a legitimately-accepted overage (e.g. recovered
   rework settled elsewhere), plan to use the audited override (step 4).
3. **Set the tolerance** if a small margin is acceptable: `SETTLEMENT_RECONCILIATION_TOLERANCE`
   = absolute pieces (default `0` = strict). A stage blocks only when `settled − produced >
   tolerance`.
4. **Enable:** set `ENFORCE_SETTLEMENT_RECONCILIATION=True`. Now `finalize` **refuses** an
   over-allocated settlement with an actionable diagnostic (which stage, settled vs produced,
   over-by, tolerance). To finalize anyway, a **super-admin** uses the **override field** on the
   settlement screen with a **mandatory reason** — recorded append-only on
   `SettlementReconciliationEvidence` (`override_reason` + `overridden_by`). **Roll back
   instantly** by setting it `False`.

## Recommended rollout order
1. Deploy — both flags **OFF**.
2. Soak; run `preview_allocation_bound` + `reconcile_pay --all` periodically; collect the
   persisted `SettlementReconciliationEvidence` rows (the B-1 frequency metric).
3. Resolve violations as they surface.
4. Enable `ENFORCE_SETTLEMENT_RECONCILIATION` first (settlement is the money boundary; the
   BLOCK is the highest-value gate), with a tolerance if needed.
5. Enable `ENFORCE_ALLOCATION_BOUND` once a real allocated consumer stage exists and the
   preview is clean.

Both flags are independent, reversible, and never alter money — only whether an integrity
violation blocks the action.
