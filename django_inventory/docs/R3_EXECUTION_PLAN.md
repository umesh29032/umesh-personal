---
id: r3-execution-plan
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# R3 EXECUTION PLAN — Stage-Completion Guard (C3: block with Super-Admin override)

> Phase R3 of [IMPLEMENTATION_ROADMAP_PDD_V1.md](IMPLEMENTATION_ROADMAP_PDD_V1.md),
> implementing 🔒 PDD §27-C3 (owner-resolved): *default — a stage cannot complete
> while assigned workers are pending; Super-Admin may override with a MANDATORY
> reason recorded in the audit trail.* Replaces the default silent F3 auto-cancel.
> STATUS: **✅ ACCEPTED by owner 2026-07-04 (uncommitted — checkpoint
> policy).** Owner P-1/P-2/P-3 confirmed + enriched audit metadata.
> **Mid-phase business-rule conflict found + owner-resolved ("B now + A
> later"):** `create_adda` legacy auto-assigns every skilled user → strict
> ASSIGNED-blocking would block every Adda. TRANSITIONAL guard blocks only
> workers who ENTERED the workflow (IN_PROGRESS = any draft/report); untouched
> ASSIGNED keep legacy F3 auto-cancel. Documented as a compatibility layer in
> the guard comment + pinned by test; PDD unchanged (it remains correct); the
> explicit-assignment migration is a new gated-backlog item — when it lands,
> the guard goes fully strict.
> **Bonus fix:** `complete_layering` was missing `@transaction.atomic` (other
> 3 completes have it; ATOMIC_REQUESTS is OFF) — a post-mutation failure
> (PAY-2/C3/DB error) would have PERSISTED a half-completed stage. Found by
> the R3 lifecycle test, fixed.
> Results: gate PASS 734 (+8 R3 tests, 1 lifecycle test updated to
> block-then-override) · golden OK · LIVE browser E2E on 3-PATTI-007:
> block message named "Worker Two", override completed the stage, task
> cancelled with reason stamped, COMPLETION_OVERRIDE event carries
> actor/timestamp/stage/pending names+count/reason.
> Anchors verified against code 2026-07-04 (post-R2).

## 1) Current behavior vs target

| | Today (F3, owner-locked 2026-06-11) | R3 target (C3, PDD §27) |
|---|---|---|
| Stage completes with unreported assigned workers | silently AUTO-CANCELS their tasks (note stamped) | **REFUSES** with an actionable error naming the pending workers |
| Escape hatch | none needed | Super-Admin + mandatory reason → cancel proceeds, override AUDITED |
| Fully-reported stage | completes | unchanged — completes |
| Explicit un-assign before complete | allowed (manager) | unchanged |

F3's cancel mechanics are RETAINED — they now run only behind the override
(or trivially, when nothing is pending). C-TM, PAY-2, freeze order all untouched.

## 2) Design — one guard at the single funnel (open-closed)

Every stage's `complete_*` funnels through `adda_service.advance_to_next_stage`
(verified: layering 842 · cutting_pattern 521 · cutting 1158 · barcode_gen 346 ·
cutting-legacy 1042). The guard lives THERE — before the cost freeze, beside
PAY-2 — so every current and future stage inherits it with zero per-stage code.

```
advance_to_next_stage(adda, user, *, enforce_worker_credit=True,
                      override_pending_reason: str | None = None)
   pending = leaving_sr active tasks in (assigned, in_progress)
   if pending:
       if override_pending_reason is None:
           raise ValidationError("Cannot complete <stage>: N worker(s) have not
               submitted: <names>. Un-assign them, wait for reports, or
               (Super-Admin) override with a reason.")
       require super_admin (permission_service) — else PermissionDenied
       require non-empty reason — else ValidationError
       log_adda(COMPLETION_OVERRIDE, user, metadata={workers, reason})   ← audit
   resolve_stage_tasks_on_complete(sr, cancel_note=derived-from-reason)  ← existing F3
   ... (freeze, advance — unchanged)
```

- New `AddaHistory.ChangeType.COMPLETION_OVERRIDE` — TextChoices value only,
  **no migration** (no DB enum constraint on change_type; verified).
- `resolve_stage_tasks_on_complete` gains optional `cancel_note` (default =
  today's AUTO_CANCEL_NOTE) so cancelled tasks carry the override reason.
- Writer discipline: history via `log_adda` (single-writer ✓); task cancel via
  `set_stage_workers` chokepoint (unchanged ✓).

## 3) Files to modify

| File | Change |
|---|---|
| `config/production/services/adda_service.py` | the C3 guard + override param + audit log |
| `config/production/services/worker_task_service.py` | `cancel_note` param on `resolve_stage_tasks_on_complete` |
| `config/tracking/models.py` | `COMPLETION_OVERRIDE` ChangeType choice |
| 4 stage services (`layering/cutting_pattern/cutting/barcode_generation` service.py) | thread `override_pending_reason` passthrough to `advance_to_next_stage` |
| 4 complete views (`stage_views.py`, `pattern_stage_views.py`, `barcode_gen_views.py`) | read POST override fields, pass to service |
| `config/production/templates/production/_completion_override.html` (new shared partial) + 4 panel templates include it | Super-Admin-only reason box + override checkbox on each complete form (hidden for everyone else) |
| `config/production/tests/test_r3_completion_guard.py` (new) + `test_f3_pending_reports.py` (update) | see §6 |

## 4) Database migrations
**NONE.** New TextChoices value is app-level only (verified: no CheckConstraint
on `AddaHistory.change_type`).

## 5) Prerequisites / owner confirmations ❓

| ID | Question | Recommendation |
|---|---|---|
| P-1 | Guard applies to ALL stages incl. the legacy cutting path (`enforce_worker_credit=False` caller)? | yes — C3 is about production truth, not payability; one rule everywhere |
| P-2 | Override actor strictly super_admin (not manager)? | yes — matches PDD §27-C3 text |
| P-3 | Reopen-then-complete replays the guard (pending workers re-block after reopen)? | yes — guard is stateless, runs every advance |

## 6) Tests

1. Funnel unit tests on `advance_to_next_stage`: pending → blocked, error names
   workers; no-pending → advances; completed+verified only → advances.
2. Override: super-admin + reason → advances, tasks CANCELLED with reason note,
   `COMPLETION_OVERRIDE` history row with {workers, reason} metadata.
3. Override refusals: empty reason → ValidationError; manager/worker actor →
   PermissionDenied; nothing logged, nothing cancelled on refusal.
4. PAY-2 interplay: payable stage, one completed + one pending → C3 blocks
   (stricter guard wins); override → completes (PAY-2 satisfied by the one).
5. Per-stage smoke through one non-layering funnel caller (cutting-pattern) to
   prove the passthrough threading.
6. **Update `test_f3_pending_reports.py`**: assertions of silent auto-cancel on
   complete become block-then-override assertions (F3 mechanics still asserted
   AFTER override). This is the C3-mandated behavior change, not a regression.
7. Full suite + golden ₹225 byte-identical (no money code touched).

## 7) Risks

| Risk | Mitigation |
|---|---|
| Operational: stages now hard-block (behavior change owner explicitly chose) | error is actionable (names + 3 exits: un-assign / wait / override); pending-reports dashboard already exists |
| Existing F3 tests fail | updated deliberately (§6-6), reviewed as part of this plan |
| Legacy cutting path blocked too | P-1 decision; its tests adjusted the same way |
| Override UI leaking to non-super-admins | partial rendered only under `is_super_admin`; view re-checks role server-side (never trust the form) |
| Reason quality ("ok") | mandatory non-empty is the contract; content quality is owner discipline, not code |

## 8) Rollback strategy
No migration ⇒ `git revert` restores exactly. Behavioral rollback without revert:
pass `override_pending_reason` from views unconditionally? NO — not built;
rollback = revert. (A settings flag was considered and rejected: C3 is an
owner-locked default, not an experiment — YAGNI.)

## 9) Acceptance criteria

- [ ] Stage with pending assigned worker refuses completion; error names the
      worker(s) and the three exits. Verified in browser (360 + desktop).
- [ ] Super-Admin override with reason completes the stage; cancelled tasks
      carry the reason; Adda timeline shows the COMPLETION_OVERRIDE event.
- [ ] Empty reason / non-super-admin override rejected server-side.
- [ ] Fully-reported stage completes exactly as before.
- [ ] `bash scripts/check.sh` PASS (updated F3 tests included); golden intact.
- [ ] Docs synced (stage_earnings_flow note: PAY-2 §6 + C3 guard; GUIDE rows;
      PDD §16/§29 already state the target — no PDD change needed).

## 10) Implementation order (estimated)

1. ChangeType + guard + `cancel_note` param + funnel unit tests — ~1.5 h
2. Threading through 4 stage services + views — ~1 h
3. Shared override partial + 4 panel includes (super-admin-gated) — ~45 min
4. F3 test updates + full suite — ~45 min
5. Browser verify (block as manager, override as super-admin, 360/desktop) + docs — ~45 min

Total ≈ half a working day. Uncommitted (owner checkpoint policy).
