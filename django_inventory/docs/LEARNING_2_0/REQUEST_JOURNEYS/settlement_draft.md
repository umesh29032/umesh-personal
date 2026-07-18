---
id: l2-request-journeys-settlement-draft
type: request-journey
status: active
owner: handwritten
scope: settlement_draft (request-journey)
anchors: —
verified: 2026-07-13
---

# Journey: Settlement Draft (open the scratchpad)

## TL;DR (1 min)
Open/resume a recomputable draft for a ready Adda. NO money yet; discardable.

**URL** `expense:adda-settlement-start` POST `/expense/settlements/start/<adda_pk>/`.
**View** `expense/views.py:AddaSettlementStartView` (resumes existing draft or
creates). **Service** `adda_settlement_service.create_draft(adda, user)`. **Models
read** AddaStageRecord (payable + completed gate), existing AddaSettlement (draft?).
**Models written** AddaSettlement (status=draft) — nothing else. **Tx** atomic +
advisory lock for reference allocation. **RBAC** management. **ADRs** 0005/0007.
**Tables** expense_addasettlement. **Before→after** none → AddaSettlement(draft,
ADST-XXXX); resume = no new row.

### How would I debug this in production?
- **First file:** `adda_settlement_service.py:create_draft`. **Breakpoint:** payable-stages-completed gate.
- **First query:** `SELECT reference,status FROM expense_addasettlement WHERE adda_id=<id>;`
- **First log:** `adda_settlement.draft`.
- **Failure modes:** "payable stage not completed yet" (names the stage); duplicate draft (resume should prevent — check the start view).
- **Expected DB state:** at most one draft per Adda at a time; draft carries no money/items.
- **Recovery:** discard the draft (no money, safe) → start fresh.

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (create_draft+; start view). Tests: test_adda_settlement_service.py, test_adda_settlement_views.py.
