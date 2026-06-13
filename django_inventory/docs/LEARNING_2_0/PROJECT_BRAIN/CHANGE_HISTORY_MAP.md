# CHANGE HISTORY MAP — phase → what changed → files/docs

## TL;DR
"When did X come in / what shipped in phase Y" without `git log` archaeology.
Full reviews archived under docs/archive/reviews/ (each with a superseded-by banner).

| Phase (date 2026-06) | What shipped | Key files | Doc |
|---|---|---|---|
| V2-1a→1d (06-09→11) | worker truth (WST/WSC), M2M dropped (mig 0035) | production/models/worker_task.py, worker_task_service.py | ARCHITECTURE_V2; archive/reviews/V2_1* |
| P2 + validation | schema-driven worker report UI (phone) | worker_report_views.py, worker_report.html | archive/reviews/P2_* |
| R1 stage-domain | locked Stage Contract, archetypes, scan seam | (design) | R1_STAGE_DOMAIN_REVIEW |
| V2-2 PR-A→D (06-11) | AddaSettlement event + mgmt UI | expense/models.py, adda_settlement_service.py, expense/views.py | ARCHITECTURE_V2 §11; archive/reviews/V2_2_* |
| V2-3 (06-11) | settlement-first cutover + money armor + Expected/Earned/Paid | base.py (lever), _shared.py (reopen guard), allocation_service (void guard) | archive/reviews/V2_3_*; ADR-0007 |
| C-1 (06-11) | grouped-member guard, leftover write path, ADR-0009/0010 | cost_service.py, roll_service.consume_leftover, adr/0009,0010 | archive/audits/ARCH_AUDIT_FOUNDATION |
| P1/P2/P3 (06-12) | verified-qty surface, completion warning, duality hint | worker_task_service.set_verified_quantity, AddaReportReviewView, stage panels | OWNER_WORKFLOW_AUDIT (archived) |
| Frontend S1+A-scope (06-12) | mobile table fix (F1), vendor central, base canonicals | accounts/base.html, expense templates | UI_COMPONENTS; archive/audits/FRONTEND_* |
| Docs initiative (06-12) | single-source docs, app READMEs/GUIDEs, LEARNING/, PDFs | docs/, config/*/README | archive/audits/DOC_AUDIT |
| PKALS (06-12, ongoing) | LEARNING_2_0 academy + living system + PROJECT_BRAIN | docs/LEARNING_2_0/ | archive/reviews/WORK_LOG |

**Pre-V2 history** (batch system, etc.): docs/archive/ (ARCHITECTURE_ROOT, QA/,
production/CHAT_LOG). Roadmap ahead: ROADMAP_REVIEW + PENDING_BACKLOG.

### Verification Sources
Phase list from this session's commits + archived reviews. Confidence: High.
