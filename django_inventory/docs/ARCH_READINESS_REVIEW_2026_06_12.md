---
id: docs-arch-readiness-review-2026-06-12
type: receipt
status: active
owner: append-only
scope: project
anchors: —
verified: 2026-07-18
---

# Architecture Readiness Review — final pre-deployment validation (2026-06-12)

Owner-requested whole-system validation against the original factory vision.
Baseline locked: V2-1 → V2-3, C-1, P1/P2/P3, ADR-0005..0010, TM requirement.
No redesign performed; one cross-decision interaction found (§3, TM-1×P2 —
build note, not a contradiction). Evidence: this session's foundation audit,
workflow audit, live walkthroughs, 496-test gate.

---

## 1) Worker answerability matrix

| Question | Source of truth | Where visible today | Status |
|---|---|---|---|
| What work performed | WSC lines (color/size/qty per stage) | My Earnings "Earnings by Adda" + recent work; mgmt worker detail | ✅ |
| On which Addas | WST (assignment truth) + WSC | My Earnings + worker detail rollups | ✅ |
| On which stages | WST per stage_record | stage-wise earnings rollup | ✅ |
| How much reported | `reported_quantity` (immutable) | report screen (own), review page, settlement draft | ✅ |
| How much verified | `verified_quantity` (P1 surface) | per-Adda review page; ✓ marks on settlement draft | ✅ per-Adda (cross-Adda per-worker rollup = derivable, no dedicated screen — acceptable) |
| Expected earnings | frozen `expected_*`, era-aware `unsettled_expected` | "Expected (unsettled)" on My Earnings + worker detail | ✅ |
| Settled earnings | ledger STAGE_EARNING (net of reversals) | "Earned (settled)" | ✅ |
| Payments made | PayrollSettlement (payment-only) | "Paid (cash)" + payment history on worker detail | ✅ |
| Advances outstanding | live SUM (reversed-aware) | worker detail + settlement draft caps | ✅ |

Every answer is also non-overlapping by construction (Expected → Earned →
Paid ladder, V2-3 PR-C tests).

## 2) Adda answerability matrix

| Question | Source | Where visible | Status |
|---|---|---|---|
| Production progress | stage records, auto-durations, status | Adda dashboard + workspaces | ✅ |
| Worker participation | WST roster (cancel-not-delete) | workspace Section 01 + report statuses | ✅ (none-mode noise until TM-1 — known) |
| Expected labor cost | Σ frozen expected of uncredited lines | settlement queue "Expected ₹" + draft preview | ✅ |
| Settled labor cost | ADST chain + Σ non-voided SWA (both eras) | settlement history + costing "Worker Earnings" col | ✅ |
| Advance recoveries | PSI rows per settlement (reversed-aware) | settlement detail recoveries table | ✅ |
| Missing quantities | frozen variance counts at settlement ONLY | settlement snapshot | ⚠️ partial BY DESIGN — pre-settlement operational record = the MissingPiece phase; nothing blocks it (denominators + seam ready) |
| Manufacturing cost today | Σ processing_cost (honest-NULL) + duality hint + unpriced-rolls banner | costing dashboard | ✅ labor-side; material labeled "incomplete" honestly until G1 |
| G1–G7 compatibility | foundation audit, per-area | ADRs 0008–0010 + gap registry | ✅ all seams verified; G6 ordering + locks in place |

The one composition gap — all of the above on ONE page — is G4, scheduled as
the soak instrument. Data-complete today.

## 3) Contradiction sweep (every locked decision × every principle)

Checked pairs across V2-1/2/3, C-1, P1/P2/P3, TM locks, ADR-0008/9/10 against
the nine principles. Result: **no hidden contradictions. One interaction
found, two known tensions re-confirmed as documented-and-decaying:**

- **NEW — TM-1 × P2 (build note, not a contradiction).** P2's
  `pending_report_workers` counts assigned/in_progress tasks. Under TM-1
  none-mode, tasks intentionally stay unreported — the completion dialog
  would warn about workers who are not supposed to report. The TM-1 build
  must make the helper tracking-mode-aware (one filter). Recorded here so the
  TM-1 implementation review inherits it.
- Era-A coarse exclusion grain (worker+stage) — documented, population frozen
  since V2-3, decays to a display concern, dies at the soak-gated deletion.
- Workspace visibility (T1/D-T5) — accepted policy, future F7-family.
- Verified everything else clean, notably: P1's settled-line guard ALIGNS
  with (not contradicts) settlement-first — production-truth corrections
  behind money now route through reversal, same as reopen/void;
  Model A's worker-centric payment does not break Adda-centricity (settlement
  is the Adda-centric event; cash is deliberately fungible);
  rework case-scoping (0010 §4) preserves first-pass WSC truth AND leaves the
  settlement seam open for a future rework-pay decision (Alter design opens
  with it — already on its phase sheet);
  C-TM convergence holds for every shipped capture path (manual report,
  draft, verified correction — all через worker_task_service).

## 4) Architecture Readiness Review

### Strengths (what the system gets right that most ERPs don't)
1. Append-only financial truth, single-writer enforced in CI (gates 4/4b/4c).
2. Production truth ≠ financial truth, joined only at an explicit, reversible,
   owner-approved closing event with frozen snapshots.
3. Corrections are lifecycle events everywhere money or truth is involved
   (reverse/supersede; verified-vs-reported; cancel-not-delete) — history is
   never edited, and every guard names the document blocking it.
4. Honest-NULL discipline across costing (unpriced stages, unpriced rolls,
   material-incomplete labels) — unknown never reads as zero.
5. Open-closed stage engine: capability (handler) vs policy (WorkflowStage)
   — TM-1 and future stages are data, not code.
6. Era transitions are structural (FK markers, frozen stamps), making the
   roadmap's remaining migrations bounded instead of forensic.
7. Worker phone flow measured at ~4 taps with plain language — the adoption
   surface is not the obstacle.
8. Every future phase (Missing/Alter/G1–G7) opens with its constraints
   pre-locked in an accepted ADR rather than discovered mid-build.

### Weak points (honest, none blocking)
1. Zero real-user evidence — every invariant is developer-proven only. The
   soak is the validation, not a formality.
2. Variance counts are typed numbers until MissingPiece; their quality is
   operator-dependent.
3. The cutting workspace is the system's hardest screen — training cost
   concentrates on one person (mirrors the real job; not fixable by UI).
4. God-files (stage_views, expense/views) — maintainability tax, parked
   consciously.
5. mypy ratchet drift (257 errors) — the one undisciplined trend line.
6. Single-brain risk: the owner is the only fluent reader of this
   architecture; the doc/ADR discipline mitigates, succession would solve.

### Remaining assumptions (stated so they cannot ambush)
- One factory, one operational tempo (ADR-0010 converts growth to a bounded
  migration — but the assumption stands today).
- Workers will report within the stage's lifetime (F3/F8 + P2 dialog manage
  the failure mode; soak measures the rate).
- `completed_at` is an acceptable work-date proxy for analytics.
- Cloth is the only modeled material; kg is the only costed unit.
- Settlement cadence is human-driven (no auto-settle anywhere — by design).
- Dev-server-grade ops until the deploy stack is live (no error reporting yet).

### Hidden debt (small, named, scheduled)
- Era-A rows live forever in SWA (accepted ADR-0007 cost; reader confusion
  ~once a year).
- 8 lever-pinned legacy test classes await the soak-gated deletion PR.
- TM-1×P2 helper filter (this review, §3).
- F7 assignable-pool policy duplication; D-T5 workspace visibility refinement.
- Dual provenance paths (WSC.settlement_line vs item.earning_assignment) —
  documented redundancy.

### Future-phase risks (carried from prior audits, unchanged)
- Alter/Rework: rework-pay decision + case-scoped records — fenced by 0010 §4.
- G5: the first new truth domain; must inherit ledger discipline from birth.
- G6 SKU shape: the keystone decision for everything commerce.
- Barcode module: payload permanence locked; H3/H5 wait for its review.
- Overhead: undefined; must arrive era-stamped or it rewrites history.

### Expensive to change AFTER real production data begins (decide before/at deploy)
1. **DB-init choice — the immediate one.** Migrating the dev DB carries
   3-PATTI test Addas, ADST-0001→0003 demo settlements, ₹-ledger rows for
   test users, and demo barcode ranges into PRODUCTION financial history —
   append-only means they can never be deleted, only lived with. **Recommend
   FRESH production DB** (workers/products/flows re-entered — hours of setup)
   or, second-best, an explicit pre-launch scrub executed BEFORE the first
   real row, never after. Reference sequences (ADST-XXXX) start clean on a
   fresh DB and are globally permanent thereafter (ADR-0010 §1).
2. Rate semantics (`cost_rate` dual duty as standard cost + default pay) —
   splitting later means re-explaining every frozen historical rate.
3. `reported`/`verified` meaning — any future "third quantity" must be a new
   field; redefining these two after real disputes reference them is a trust
   event, not a migration.
4. Stage codes (`Stage.code` = stable identity) — rename discipline holds
   only if honored from day one of real flows.
5. Barcode payloads — physically permanent the day the first real label
   prints (already locked, restated because deployment makes it real).

## Verdict

**The system still matches the original factory vision — strengthened, not
drifted.** Every owner question in §1/§2 has a truth source and (with two
honest, scheduled partials: pre-settlement missing records, the G4
composition page) a screen. The contradiction sweep found no structural
issue — only one cross-feature build note inherited by TM-1. Nothing requires
a new phase. The single decision this review elevates: **choose fresh-DB (or
pre-launch scrub) at deployment — it is the last cheap day for that choice.**

Architecture readiness: **CONFIRMED. Proceed to deployment.**
