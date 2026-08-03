---
id: retro-tag-sync-audit-2026-07-05
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# Audit: `sync_layering_workers_for_skill` (pre-freeze loose end)

> **STATUS: ✅ REMOVED (C-1 freeze closeout, 2026-07-05, owner-approved).**
> Function + `sync_user_skills` wrapper + all 3 trigger sites + pins deleted;
> the accounts→production edge is GONE (import-linter ignore rule dropped —
> contract now stricter; REMEDIATION COUP-5 resolved). Permanent business rule
> registered in the PDD amendments: "Manager assignment is the ONLY source of
> truth for worker rosters." This document remains the decision record.

> Owner-ordered read-only audit, 2026-07-05 (post pre-R10-polish). NOTHING
> changed. Method: main-thread code reads + git archaeology, cross-checked by
> a 4-reader + adversarial-verify workflow (per the sub-agent honesty rule,
> every load-bearing claim below was re-verified in the main thread).

## 1) What it is / why it exists

`production/stages/layering/service.py:296` — for a user holding
cutting_master/helper skill, ensure an ACTIVE `WorkerStageTask` on **every**
active Layering stage record in the factory (`add_stage_worker`, additive).

Born **2026-05-20** in the original production-tracking commit (`e72a1d9f`,
Phase 4) — same commit as `create_adda`'s auto-populate. The Phase-4 roster
model was *"roster == all current skill-holders"* (spec D1: helpers see a new
Adda instantly). Two halves kept that invariant:
- `create_adda` auto-assigned everyone at Adda start (**removed by F-2**);
- the retro-tag handled the converse: someone hired/skilled AFTER the Adda
  started still had to appear on in-flight layerings. Originally an
  `m2m_changed` signal; converted to the explicit
  `user_service.sync_user_skills` call by ADR-0001 (no-signals rule) — the
  deliberately-kept ONE accounts→production edge (P4.1).

## 2) When it fires today (all three sites verified)

| Trigger | File | Condition |
|---|---|---|
| Team Members → create user | `accounts/views.py:326` | every create with skills |
| Team Members → edit user | `accounts/views.py:365` | **EVERY save** ("Skills may have changed" — unconditional) |
| Django admin user save | `accounts/admin.py:34` (`save_related`) | every admin save |

## 3) Is it obsolete after F-2? — YES, and worse: it now fights F-2

The invariant it maintains ("roster == skill-holders") no longer exists.
Post-F-2 the roster contract is *manager intent only*. The retro-tag now:

- **Silently overrides manager roster decisions.** `add_stage_worker`
  (`worker_task_service.py:134-144`): *"a prior cancelled task does not
  block"* → it creates a **fresh ACTIVE task**. Concrete replay: manager trims
  3-PATTI-011 layering to dev.monthly (utest's task → cancelled) → anyone
  later saves utest's profile from Team Members (fixing a phone number is
  enough — the edit hook is unconditional) → utest is re-added to **every**
  active layering in the factory.
- **Re-grows the phantom population F-2 just removed**, one user-save at a
  time: false "Report needed" cards on worker dashboards, inflated Operations
  "PENDING REPORTS", A360 open-task counts, `pending_report_workers`
  completion warnings, and auto-cancel debris at stage complete.
- Is **non-atomic by design** (docstring; lock-free loop) — a mid-loop failure
  leaves a partially re-tagged factory.
- Is **one-directional**: removing a skill never removes rosters — only
  re-addition, never cleanup.

## 4) Money safety (verified)

None. It writes `WorkerStageTask` rows only (via the sanctioned single
writer). A bare task carries no quantities: no `WorkerStageContribution` → no
expected freeze → invisible to `_settleable_lines` → no settlement line, no
ledger. Pure production-noise, zero money surface.

## 5) Does anything depend on it? (census)

- **Business flows: nothing.** The need it served ("new hire sees work
  immediately") is met correctly post-F-2/F-4: the new skill-holder appears in
  every stage picker instantly (live queryset), manager assigns, worker sees
  the task. No view/flow/UI copy promises auto-appearance.
- **Code:** sole business caller = `user_service.sync_user_skills` (the three
  trigger sites above). Facade export list entry. Nothing else.
- **Tests:** `test_phase4.RetroTagTests` (3 tests pinning the behavior itself),
  `accounts/tests.py:508` (smoke: no-skill user → returns 0),
  `test_facade_contract` row. All pins OF the feature, not users of it.
- **Docs:** LAYERING_STAGE.md table row, AUDIT_SYSTEM_MAP entries, ADR-0001
  example — descriptive only.
- **The roadmap already sentences it:** the gated-backlog row
  ([IMPLEMENTATION_ROADMAP_PDD_V1.md:212]) defines the "explicit-assignment
  migration" as removing **exactly this pair** — `create_adda` auto-assign
  (done, F-2) + `sync_layering_workers_for_skill` (this function) — after
  which the R3 completion guard may drop its transitional IN_PROGRESS-only
  filter (PDD-strict C3). The C3 guard's own comment
  (`adda_service.py:195-203`) says the transitional filter exists *because*
  of auto-assignment.
- **Architecture bonus:** removal deletes the ONE deliberate
  accounts→production runtime edge outright — REMEDIATION_PLAN P4.1/COUP-5
  wanted this edge gone and could only propose relocating it; deletion beats
  relocation.

## 6) Recommendation — REMOVE, in this freeze

It is the second half of F-2: leaving it means the polish is incomplete (the
phantom population re-grows on every user save, now **against** explicit
manager intent — post-F-2 that's a bug, not a legacy behavior). Removal is
small, mechanical, money-free, and un-blocks a known remediation item:

1. Delete `sync_layering_workers_for_skill` + facade export row.
2. Delete `user_service.sync_user_skills` + its three call sites (accounts
   views ×2, admin `save_related` override becomes unnecessary).
3. Delete `RetroTagTests` (they pin the removed behavior), the accounts smoke
   test, the facade-contract row; update LAYERING_STAGE / AUDIT_SYSTEM_MAP /
   ADR-0001 mention (historical note).

**Kept SEPARATE on purpose:** the strict-C3 flip (block completion on bare
ASSIGNED) that the roadmap row sequences *after* this removal. It is a real
behavior change to stage completion and deserves its own explicit owner go —
removal above is safe with the transitional guard exactly as it stands.

## 7) Adversarial verification (workflow) — honest record

4 independent readers (history / callers / dependents / behavior) ran to
completion, every fact cited + high-confidence. The refute-oriented verify
pass partially failed on an API session limit: **3 verifier verdicts landed
(all CONFIRMED: the original commit intent quote · the b09b77f3
signal→explicit-call conversion · the ADR-0001/rule-#4 rationale); 9
verifiers died before reporting.** Per the audit-honesty standing rule, the
failed verifications do NOT count as confirmations — instead every
load-bearing claim in this document was independently re-verified by
MAIN-THREAD reads/greps/git (sources below), so nothing here rests on an
unverified sub-agent claim.

Extra facts the archaeology added (main-thread spot-checked):
- The original in-code spec tag was **"Spec D8"** (deleted signal's docstring)
  — a spec list that never existed in any committed doc; the behavior's only
  written contract is the commit message itself.
- Evolution: born as signal+function (e72a1d9f, 2026-05-20) → ORM sweep for
  the Stage library (1bba7571) → routed through the `add_stage_worker`
  chokepoint (e4953ef9, V2-1a) → M2M dropped, WST-only (e01f0c4b, V2-1d) →
  signal deleted for the explicit `sync_user_skills` call (b09b77f3,
  2026-06-09, remediation phases 1-13). **Semantics unchanged since
  2026-06-11** — it predates the PDD, the explicit-assignment decision, and
  F-2 by weeks.

### Verification sources
Main-thread: layering/service.py:296-320 · worker_task_service.py:129-144 ·
user_service.py:98-112 · accounts/views.py:318-370 · accounts/admin.py:28-38 ·
adda_service.py:195-215 · test_phase4 · test_facade_contract:27 ·
accounts/tests.py:507-512 · git e72a1d9f (2026-05-20) · roadmap:212 ·
REMEDIATION_PLAN:187 · lint-imports run. Confidence: High.
