---
id: r6-execution-plan
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# R6 EXECUTION PLAN — verified-quantity audit trail (F6)

> Phase R6 of [IMPLEMENTATION_ROADMAP_PDD_V1.md](IMPLEMENTATION_ROADMAP_PDD_V1.md),
> implementing 🔒 PDD §31.1-F6 + §29: *`set_verified_quantity` emits a history
> event (who / old / new / when) via the history chokepoint.* Closes the
> production-audit "documented-not-fixed: verified-qty no-audit" item (Phase 10).
> STATUS: **✅ ACCEPTED by owner 2026-07-05 (uncommitted,
> checkpoint policy).** Built exactly as planned; gate PASS **779** (+4
> test_r6_verified_qty_audit); golden byte-identical; NO migration.
> ONE anticipated deviation (§7 risk materialized): the timeline's generic
> fallback rendered the raw code `verified_qty_corrected` while every other
> event shows a verb phrase — added 'corrected verified qty' to
> `activity_service.verb_map` (+ 'overrode stage completion' for R3's
> COMPLETION_OVERRIDE, same one-line label debt).
> LIVE browser E2E on 3-PATTI-008 (utest's 20-layer report): corrected 20→18
> via review-reports → timeline event (actor + "utest@gmail.com: reported →
> 18" + metadata old=None/new=18/reported=20.00/stage/worker_id); cleared →
> second event (old=18.00, new=None); DB final state verified_quantity=None,
> reported 20.00 untouched (DEV data restored); 360px timeline no-overflow.
> Anchors verified against code 2026-07-05 (post-hostile-review fixes, gate 775).

## 1) Current behavior vs target

| | Today | R6 target (F6) |
|---|---|---|
| Management corrects a reported quantity (`set_verified_quantity`, worker_task_service:307) | row updated + a LOG LINE only | + an `AddaHistory` event on the Adda timeline: who, old, new, worker, stage, when |
| Clearing a correction (`quantity=None`) | silent (log only) | same event, `new=None` ("correction cleared, back to reported") |
| Investigations | depend on application logs | DB-resident (owner standing principle — R3/R4 posture) |

Everything else UNCHANGED: guards (management-only, completed-task-only,
settled-line REFUSES), settlement resolver, the worker's untouched
`reported_quantity` — R6 adds ONE append-only event, no behavior change.

## 2) Design — one event at the existing chokepoint

- New `AddaHistory.ChangeType.VERIFIED_QTY_CORRECTED` — TextChoices value
  only, **no migration** (same as R3's COMPLETION_OVERRIDE; no DB constraint
  on change_type).
- In `set_verified_quantity`, AFTER the row save (same atomic txn):
  capture `old` before assignment; **skip the event when old == new**
  (no-op corrections make timeline noise, not audit value); then
  `log_adda(adda, VERIFIED_QTY_CORRECTED, actor, stage_record=…, note=…,
  metadata={'contribution': id, 'worker': name, 'worker_id': id,
  'stage': name, 'reported': str, 'old': str|None, 'new': str|None})`.
- Writer discipline: history via `log_adda` (tracking history_service — the
  single writer, rule 5). Event appears on the Adda-360 timeline
  automatically (the activity feed already renders AddaHistory generically —
  verified during implementation; adjust label rendering only if the generic
  path chokes on the new type).

## 3) Files

| File | Change |
|---|---|
| `config/tracking/models.py` | `VERIFIED_QTY_CORRECTED` ChangeType |
| `config/production/services/worker_task_service.py` | capture old → log_adda after save (skip no-op) |
| `config/production/tests/test_r6_verified_qty_audit.py` (new) | §5 |

## 4) Database migrations
**NONE** (TextChoices only — verified, same precedent as R3).

## 5) Tests
1. Set 20→18: ONE event; metadata carries old='20.00', new='18.00', reported,
   worker name+id, stage; actor + created_at on the row.
2. Clear (18→None): event with new=None.
3. No-op (18→18): NO event.
4. Refusal paths (settled line / not-completed / non-management): NO event,
   row untouched (existing guards regression-pinned).
5. Full gate + golden (no money code touched).

## 6) Browser verification (DEV data)
On 3-PATTI-008 layering (utest's completed 20-layer report): management
corrects 20→18 via the review-reports page → Adda timeline shows the event
with old/new/worker; clear back to reported → second event. 360 + desktop
timeline render check.

## 7) Risks
| Risk | Mitigation |
|---|---|
| Timeline template can't render the new type | activity feed is generic over AddaHistory; verified in browser — worst case a label branch, cosmetic |
| Event noise | no-op skip; corrections are rare management actions |

## 8) Rollback
`git revert` — no migration, no data.

## 9) Acceptance criteria
- [ ] Correction + clear each produce a DB-resident timeline event
      (who/old/new/when) — browser-verified on the Adda timeline.
- [ ] No-op and refused corrections produce nothing.
- [ ] `bash scripts/check.sh` PASS; golden byte-identical.
- [ ] Docs synced (worker_task_service chokepoint doc + production GUIDE row).

## 10) Order (estimated)
ChangeType + event + tests ~45 min · browser verify + docs ~30 min.
Total ≈ 1.5 h. Uncommitted (checkpoint policy).
