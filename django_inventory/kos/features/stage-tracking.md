---
id: feature-stage-tracking
type: feature
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "How does the system record who did what work on a stage — and keep that record correctable until money books?"
related: [feature-settlement, feature-allocation, concept-two-truths, flow-worker-gets-paid]
---

# Stage Tracking — production truth, one door

> 📂 [Features](README.md) · [KOS home](../README.md) — *pehle yeh page, phir code.*

## Business Purpose

Every claim of work ("Meena stitched 38 red-L pieces on cutting") must be
recorded by the worker themself, verifiable by a manager, and immutable as
history — because this record is what settlement later turns into money.
Stage tracking is the **production-truth half** of the two-truths split:
who was assigned, what they reported, what management verified.

## Mental Model

> **One door, two hands.** All work-capture — manual phone reports today,
> barcode scans tomorrow — enters through ONE service (`worker_task_service`,
> the C-TM convergence law). And every quantity has two hands on it: the
> worker's `reported_quantity` (never touched by anyone else) and
> management's `verified_quantity` (a correction that never overwrites the
> report). Truth = both hands visible, forever.

## 💡 Samjho Aise

Hazri-register + supervisor ki laal kalam. Worker apni entry khud likhta
hai ("40 kiye"). Supervisor ko galti dikhi to wo worker ki entry NAHI
kaat'ta — bagal mein laal se likhta hai ("38 sahi"). Dono hamesha dikhte
hain: kisne kya bola, kisne kya maana. Paisa laal wale number par banta
hai, par kaala kabhi mit'ta nahi.

## Technical Deep Dive

**The two models** (production app; sole writer `worker_task_service`, CI gate 4/4):

- `WorkerStageTask` (WST) — the assignment lifecycle:
  `assigned → in_progress → completed → [verified] / cancelled`.
  ≤1 ACTIVE per (stage_record, worker); un-assigning = CANCELLED, never
  deleted (append-only citizenship).
- `WorkerStageContribution` (WSC) — the dimensional line under a task:
  (color, size) × quantities. Since S3: **good / alter / missing** observed
  counts (good = payable basis; alter/missing = immutable observations;
  DB CHECK `wsc_gam_nonneg_sum_positive`).

**The lifecycle, in service verbs:**

1. `set_stage_workers(sr, ids)` — manager sets the roster (the ONLY roster
   source, PDD amendment 4). Removed workers' open tasks → CANCELLED with note.
2. `report_contributions(task, lines)` — worker's phone submits lines;
   `save_draft_contributions` holds unfinished entry.
3. `complete_worker_task(task)` — THE freeze moment (walkthrough below).
4. `set_verified_quantity(contribution, qty)` — management's red pen.
5. `void_submitted_report(task, reason)` — audited un-submit, pre-money.

**Walkthrough: `complete_worker_task` — five guards before one freeze**
(read the real function; its comments are a concurrency course):

```
lock own WST row, re-read status FROM DB        # P0-5: the stale-instance race
 → refuse if CANCELLED (manager's concurrent stage-complete won)
 → refuse if already COMPLETED
 → pool_service.check_allocation_bound(task)    # S4: good+alter+missing ≤ allocated
 →                                              # (flag-gated, capacity-only, no money)
 → FIXED-pay stage? refuse a SECOND completed report, naming who
   already reported                             # R8: fixed amount pays ONCE
 → freeze expected_rate/expected_earning per line
   from the Adda-frozen AddaStageRoleRate for the worker's CURRENT role
   (S2: later rate edits / role changes never re-price this work)
 → NO ledger entry                              # Option B — visibility, not money
```

The P0-5 story deserves respect: the view read `task` earlier; meanwhile a
manager's stage-complete cancelled it under ITS lock. Completing from the
stale in-memory status would resurrect a cancelled task into COMPLETED
frozen money-visibility. Fix: lock the row, trust only the DB's status.
**Never trust an instance you read before the lock.**

**The red pen: `set_verified_quantity`** — management-only; task must be
completed; **refuses if the line is already settled** (names the ADST —
reverse the settlement first, same armor philosophy as reopen/void);
locks the WSC `of=('self',)` (nullable `settlement_line` FK → LEFT JOIN →
PG refuses FOR UPDATE on the nullable side). `quantity=None` clears back
to reported.

**Who reads which number** (the resolver, applied per concern):
- Settlement money: `verified ?? reported` (settlement_resolver)
- Next stage's pool: `Coalesce(verified, good)` (pool_service, same rule)
- Worker's Expected ladder: frozen `expected_*`
One manager correction flows everywhere from one truth — because everyone
derives, nobody copies.

## Debugging Guide

| Symptom | Start |
|---|---|
| Worker: "mera report gayab" | WST status — CANCELLED with note? (roster change) · draft not submitted? |
| "Can't complete task" | Read the refusal — cancelled? already done? fixed-pay already reported (it names who)? allocation bound (flag on)? |
| "Verified number won't save" | Line settled? The error names the ADST — reverse first |
| Quantities differ across screens | Check WHICH number each reads (reported vs verified vs expected vs pool) — table above |

## Change Impact

Settlement funnel (`_settleable_lines` reads WSC) · pool materialization
(verified-else-good) · Expected ladder (`unsettled_expected`) · Report
Review UI · reopen guards · tests `test_worker_task.py`,
`test_s3_good_alter_missing.py` · goldens.

## AI Implementation Pitfalls

- ❌ Writing WST/WSC outside `worker_task_service` — C-TM is LOCKED; barcode
  or any future capture path converges here, no second door.
- ❌ Editing `reported_quantity` to "fix" a report — owner rule: reported is
  the worker's, immutable; corrections = `verified_quantity`.
- ❌ Completing a task without re-reading status under lock — reintroduces P0-5.
- ❌ Letting a rate/role change recompute frozen `expected_*` — frozen means frozen.
- ✅ Always verify: both-hands visibility (reported AND verified) survives
  any UI change; settled-line refusal test stays green.

## Interview Notes

*Interview Signal: 🟡 Mid — FSM modeling — a favorite mid-level design probe.*

**Q. "Design a work-reporting system where reports get corrected but audits must hold."**
- *Short:* Two fields — immutable self-report + nullable management correction; all consumers derive via `correction ?? report`.
- *Senior:* Never overwrite the source claim; corrections are a second channel with its own permissions. Freeze derived values (rates) at event time so later config changes can't rewrite history. Gate corrections once downstream commitment exists (settled-line refusal). Lock-and-re-read status to stop stale-instance races.
- *Project example:* reported vs verified on WSC; expected_* frozen at complete; the P0-5 lock; the ADST-naming refusal.
- *Follow-ups:* "Why not versioned rows instead of two fields?" (two-party semantics need exactly two channels; versions blur WHO said what) · "How does the same correction reach pay AND capacity?" (shared resolver rule, derived everywhere).

## 🧠 Remember This

Ek darwaza (worker_task_service), do haath (reported kaala, verified laal),
teen taale (row-lock + settled-refusal + fixed-pay-once), aur freeze ka
matlab freeze. Kaala kabhi mat mitao; laal sirf paisa banne se pehle chal
sakta hai — uske baad pehle settlement ulto.

## 30-Second Revision

- WST lifecycle: assigned→in_progress→completed→[verified]/cancelled; cancel ≠ delete
- WSC: (color,size) × good/alter/missing (S3); `wsc_gam_nonneg_sum_positive`
- Complete = freeze expected_* (Adda-frozen role rate) + NO ledger (Option B)
- P0-5: lock row, re-read status from DB — never trust pre-lock instances
- FIXED-pay: second completed report refused, names the first reporter
- Verified: management red pen; settled line refuses (reverse first); of=('self',)
- Resolver everywhere: verified ?? reported/good — one correction, all consumers

## DSA & Complexity

`WorkerStageTask` is a textbook **finite state machine**: states
{assigned, in_progress, completed, verified, cancelled}, transitions only
via service verbs, illegal moves REFUSED (complete-a-cancelled, cancel-a-
completed). The FSM discipline is why concurrency is tractable: the P0-5
lock protects one thing — *reading the current state atomically before
transitioning*. Interview framing: "model workflows as explicit state
machines with guarded transitions; never as booleans that drift"
(`is_done`+`is_cancelled` = 4 combinations, 2 meaningless — the FSM makes
them unrepresentable).

## Implementation References

- Design: [ADR-0005](../../docs/adr/0005-production-truth-vs-financial-truth-option-b.md) · S3 receipt [docs/S3_DESIGN_RECEIPT_2026_06_14.md](../../docs/S3_DESIGN_RECEIPT_2026_06_14.md) · C-TM: [docs/REQUIREMENT_REVIEW_STAGE_TRACKING.md](../../docs/REQUIREMENT_REVIEW_STAGE_TRACKING.md)

## Code References
- `config/production/services/worker_task_service.py` (`complete_worker_task`, `set_verified_quantity`, `report_contributions`)
- Tests: `config/production/tests/test_worker_task.py` · `test_s3_good_alter_missing.py`

## Related Concepts

[two-truths](../concepts/architecture/two-truths.md) · [allocation](allocation.md) ·
[settlement](settlement.md) · [pg/locks](../concepts/postgresql/locks.md) ·
[single-writer](../concepts/architecture/single-writer.md)
