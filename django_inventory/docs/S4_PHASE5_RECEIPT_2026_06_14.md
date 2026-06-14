# S4 Phase 5 Design Receipt — Era-A reopen guard + pool-clear wiring (2026-06-14)

Governed by [S4_DESIGN_CORRECTION_ADDENDUM](S4_DESIGN_CORRECTION_ADDENDUM_2026_06_14.md)
(M-4) + [S4_PHASE3_RECEIPT](S4_PHASE3_RECEIPT_2026_06_14.md). **Design receipt only — no
code.** Service + tests only. **No migration** (logic only). The final S4 phase.

## What Phase 5 adds
1. A **uniform downstream-consumer guard** in the reopen skeleton (`_shared.reopen_stage_record`)
   — refuse reopen of a stage S while a downstream **consumer** of S's output exists. Applies
   to **every** stage (resolves M-4-3 — today only layering/cutting_pattern use the coarser
   `downstream_started_guard`; cutting/barcode have custom guards).
2. Wire **`pool_service.clear_stage_pool(sr)`** into the skeleton so a reopened pool-producing
   stage's `StagePoolSnapshot` is cleared (re-complete refreezes). No-op for cutting (its APSCPB
   is cleared by cutting's own teardown) and for NONE stages.

### The consumer guard (uniform, in the skeleton)
Reopen of stage S is **REFUSED** if any stage with `order > S.order` in the same Adda has:
- (a) a **non-voided `WorkerStageAllocation`** (downstream work was allocated against the pool
  S feeds), OR
- (b) a **completed/verified `WorkerStageContribution`** (downstream production truth —
  good/alter/missing — that depended on S's output), OR
- (c) (future) an **`AlterCase`** on a downstream stage (hook; returns nothing until the Rework
  module ships).

Conservative by design: the pool chain is transitive, so **any** downstream consumer blocks
(not just the immediate next stage). Existing guards stay (the skeleton block on S's OWN
settlement; the coarser `downstream_started_guard` where already used) — the consumer guard is
the uniform M-4 backstop layered beneath them.

## The six reopen scenarios (explicit behaviour)

| # | Scenario | Behaviour |
|---|---|---|
| **1** | Source reopen + downstream **active allocations** | **BLOCKED** by (a) — a non-voided downstream `WorkerStageAllocation` exists. Error names the downstream stage + "void its allocations / reverse first." |
| **2** | Source reopen + downstream **completed good/alter/missing** | **BLOCKED** by (b) — a completed/verified downstream contribution exists (its production truth depended on S's output). |
| **3** | Source reopen **after all downstream allocations voided** | (a) no longer fires. **ALLOWED** *iff* (b) is also clear (no downstream completed contributions) and S's own settlement (if any) is reversed. If downstream completed contributions remain → still BLOCKED by (b) until that downstream stage is reopened. |
| **4** | Source reopen **after settlement reversal** | `reverse_adda_settlement` voids the **SWA** (settlement earning line) → clears the skeleton's **own-settlement** block for the reversed stage. But it does **NOT** void `WorkerStageAllocation` (production-truth, untouched) and does **NOT** un-complete contributions. So if S has downstream consumers, (a)/(b) still BLOCK — reversal alone is insufficient; the downstream WSA must be voided + the downstream stage reopened too (scenario 6). Reversal unblocks only the *settled stage's own* era-B block. |
| **5** | Multi-stage chain (Cutting → Stitching → Finishing) | The guard checks **all** stages with `order > S` (the whole downstream tail). Reopening **Cutting** is blocked if **Stitching OR Finishing** has a non-voided WSA or completed contribution. Reopening **Stitching** checks only **Finishing** (Cutting is upstream → never a "consumer" of Stitching). A consumer anywhere downstream blocks (transitive dependency). |
| **6** | Owner/admin recovery when reopen is blocked | **Reverse-first, peel from the furthest downstream inward** — see below. |

## Recovery workflow (scenario 6) — strict but recoverable
To reopen source stage S, unwind its downstream tail **last-stage-first**. For each downstream
stage D (furthest from S inward), in order:
1. **Reverse D's settlement** if D is settled — *Adda Settlements* screen → Reverse (audited;
   voids D's SWA earning lines). Clears D's own era-B settled block.
2. **Void D's `WorkerStageAllocation` rows** — `pool_service.void_allocation` (audited;
   `voided_at` set, qty returns to the pool). Clears (a) for D.
3. **Reopen D** — its own `reopen_*` (which clears D's completed contributions / typed record
   per its destructive/soft semantics, and clears D's `StagePoolSnapshot` via the new
   `clear_stage_pool` wiring). Clears (b) for D. D's reopen is itself guarded by *its*
   downstream — so the peel naturally proceeds end→inward.
Repeat until **no** stage downstream of S has a non-voided WSA or a completed contribution.
**Then reopen S.** Every step is append-only audited (reverse → ledger compensating entries;
void → `voided_at`; reopen → `AddaHistory.STAGE_REOPENED`). Nothing is ever permanently stuck:
each blocker has an explicit, audited reverse/void/reopen path.

### Why this is both STRICT and RECOVERABLE
- **Strict (pool integrity):** S's `pool_good` cannot change while any downstream allocation or
  production truth depends on it → no orphaned allocations, no pool drift, no paid-more-than-
  produced via a silent upstream edit. The guard is conservative (any downstream consumer).
- **Recoverable (operationally):** every blocking condition maps to a concrete, audited owner
  action (reverse settlement / void allocation / reopen downstream). The system guides the
  operator from the downstream end inward (each reopen blocked until its own downstream is
  clear), so a mistake is always correctable — just never silently.

## Enumerations
- **New model / migration:** NONE.
- **Service:** `_shared._downstream_consumer_guard(adda, sr, wf)` (new, called uniformly in the
  reopen skeleton after the own-settlement block, before the per-stage guard) + a
  `pool_service.clear_stage_pool(sr)` call wired into the skeleton (after teardown / alongside
  the era-A void). No new writer; reuses Phase-2/3 helpers.
- **Invariant:** I-6 (reverse-first; upstream reopen refused while downstream consumers exist) —
  now enforced uniformly across all stages.
- **Lock:** unchanged — reopen already `select_for_update`s the SR; the consumer guard is a read
  (runs before mutate). No new lock; never locks `AddaStageRecord` beyond the existing SR lock.
- **Settlement-boundary:** unchanged — reopen still refuses on the stage's own settlement
  (reverse-first); golden ₹225 byte-identical.
- **Rollback:** additive logic; `git revert` restores the prior reopen behaviour. Inert in the
  current flow (no downstream stage has WSA/completed-WSC yet — barcode is auto, NONE-grain).
- **Test strategy** (synthetic cutting→stitching[→finishing] chain with WSA + contributions):
  scenario 1 (downstream WSA blocks) · 2 (downstream completed contribution blocks) · 3 (void
  all → reopen allowed) · 4 (settlement reversal alone insufficient; full peel succeeds) · 5
  (chain: Cutting blocked by Finishing two stages down; Stitching not blocked by upstream
  Cutting) · 6 (full recovery sequence reopens S) · uniform-across-stages (the guard fires
  regardless of which stage) · current-flow (cutting reopen NOT newly blocked — barcode has no
  WSA/WSC) · golden ₹225 byte-identical.
- **DOCS-SYNC:** `_shared`/reopen doc, `pool_service.md` + `worker_task_service.md` chokepoints
  (the reopen guard + clear_stage_pool), FILE_MAP, PENDING_BACKLOG (Phase 5 + S4 COMPLETE),
  CLAUDE.md, ARCHITECTURE_V2 reopen contract.

**Current-flow note:** cutting's only downstream is barcode (NONE-grain, auto, no WSA/WSC) → the
consumer guard does **not** newly block any reopen in the live 4-stage flow. It activates with
future self-reporting pool-consuming stages (stitching). The `clear_stage_pool` wiring is
likewise dormant (no SPS-backed stage). Consistent with S4 landing ahead of its consumers.

---
**STOP — awaiting approval before any Phase 5 code.** On approval: the uniform consumer guard +
`clear_stage_pool` wiring + tests (golden gate) + DOCS-SYNC. Phase 5 completes S4 — after it,
**S4 is done** (the pool/allocation foundation is fully built, gated, and reopen-protected,
ahead of its first real consumer stage).
