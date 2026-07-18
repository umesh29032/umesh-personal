---
id: learning-path
type: topic-canonical
status: active
owner: handwritten
scope: learning — ordered route
anchors: —
verified: 2026-07-13
---

# LEARNING PATH — from zero to productive (developer or owner)

> Order matters. Each step: what to read + what to DO on the dev server.
> Deep-dive topic lessons live in [docs/LEARNING/](LEARNING/README.md).
> Estimated: developer ~2 days to productive · owner ~4 short sittings.

## 1. Business domain (½ sitting)
Read: [GLOSSARY.md](../GLOSSARY.md) → [ERP_MASTER_CONTEXT.md](ERP_MASTER_CONTEXT.md).
Do: open the dashboard as manager; click into one Adda.

## 2. The map (½ sitting)
Read: [PROJECT_KNOWLEDGE_MAP.md](PROJECT_KNOWLEDGE_MAP.md) — all of it.
Do: trace one click (worker report submit) through its §2 request flow.

## 3. Adda lifecycle (1 sitting)
Read: [LEARNING/08_ADDA_LIFECYCLE.md](LEARNING/08_ADDA_LIFECYCLE.md) +
[production/OVERVIEW.md](production/OVERVIEW.md) + [STAGE_FLOW.md](production/STAGE_FLOW.md).
Do: start a fresh Adda on dev, walk it to barcode generation.

## 4. Production truth (1 sitting)
Read: [LEARNING/05_PRODUCTION_TRUTH.md](LEARNING/05_PRODUCTION_TRUTH.md) +
[ARCHITECTURE_V2.md](ARCHITECTURE_V2.md) (skip §11 for now) +
[config/production/README.md](../config/production/README.md) status card.
Do: assign yourself, report on a phone-sized window, complete; leave one
worker unreported and watch the completion warning (P2).

## 5. Financial truth + settlement (1–2 sittings — the heart)
Read: [LEARNING/06_FINANCIAL_TRUTH_AND_SETTLEMENT.md](LEARNING/06_FINANCIAL_TRUTH_AND_SETTLEMENT.md)
+ ARCHITECTURE_V2 §11 + ADR-0005/0007 +
[config/expense/README.md](../config/expense/README.md).
Do: settle your dev Adda; reverse & settle again; watch the chain + ledger
rows; pay cash. Note Expected/Earned/Paid moving without overlap.

## 6. Tracking & identity (½ sitting)
Read: [config/tracking/README.md](../config/tracking/README.md) +
[production/TRACKING.md](production/TRACKING.md).
Do: open an Adda timeline; print a QR sheet.

## 7. Costing (½ sitting)
Read: [LEARNING/07_COSTING.md](LEARNING/07_COSTING.md) +
[ADR-0009](adr/0009-cost-truth.md) — especially NEVER-ADD.
Do: find an unpriced roll/stage; see honest-NULL on the costing dashboard.

## 8. Future roadmap (½ sitting)
Read: [ROADMAP_REVIEW_POST_C1_2026_06_11.md](ROADMAP_REVIEW_POST_C1_2026_06_11.md)
+ ADR-0008/0010 (the fences future phases inherit).

## 9. Django architecture as used HERE (1 sitting, developer)
Read: [LEARNING/01_DJANGO_CONCEPTS.md](LEARNING/01_DJANGO_CONCEPTS.md) →
[03_TRANSACTIONS_AND_LOCKS.md](LEARNING/03_TRANSACTIONS_AND_LOCKS.md) →
[04_SERVICE_LAYER.md](LEARNING/04_SERVICE_LAYER.md) + SYSTEM_DESIGN §6–7.
Then read these five files top-to-bottom — they ARE the architecture:
`worker_task_service.py` · `adda_settlement_service.py` · `ledger_service.py`
· `cost_service.py` · `production/services/_shared.py`.
Do: run `bash scripts/check.sh`; break a single-writer rule in a scratch
branch and watch gate 4b/4c fail.

## 10. SQL (parallel track, any time)
Read: [LEARNING/09_SQL_BEGINNER_TO_ADVANCED.md](LEARNING/09_SQL_BEGINNER_TO_ADVANCED.md)
— levels 1–9 on this project's real tables. Do: `manage.py dbshell`, run the
Level-3 balance SUM, then `print(qs.query)` on any queryset.

## 7-day pacing (developer survival map)
If you want a day-by-day cadence instead of "sittings", pace the steps above:
- **Day 1** — steps 1–2 (business + the map) + [ARCHITECTURE_EXPLAINED](LEARNING_2_0/ARCHITECTURE_EXPLAINED/README.md) §1–6: cloth→Adda→stages→report→settle→pay + the two truths.
- **Day 2** — step 3 + run it: walk a worker report (phone-size), settle an Adda, pay; match each screen to a [REQUEST_JOURNEY](LEARNING_2_0/REQUEST_JOURNEYS/README.md).
- **Day 3** — the money: step 5 + [CHOKEPOINTS](LEARNING_2_0/CHOKEPOINTS/README.md); read `adda_settlement_service.py` + `ledger_service.py` with the chokepoint docs open.
- **Day 4** — production truth: step 4 + the open-closed stage engine (`production/stages/base/`).
- **Day 5** — data: step 10 (SQL) + [LEARNING/02](LEARNING/02_DATABASE_RELATIONSHIPS.md); `dbshell`, run the live-balance SUM, `print(qs.query)`.
- **Day 6** — your app: its [APPS/<app>/](LEARNING_2_0/APPS/) page + GUIDE + README.
- **Day 7** — change safely (see below).

## Common beginner mistakes (avoid from day 1)
Writing a model in a view (services own writes) · reading `expected_*` as money
(it's visibility; real money is the ledger at settlement) · adding a stage with
if/else instead of a handler package (open-closed) · a new menu item without a
`SidebarItemRule` (URL left unprotected) · a UI without 360/768/1280 verification
(rule 11) · forgetting docs-sync (rule 12). For the NEVER-modify list, the safe
bug-trace path, and the safe add-a-feature path, the canonical reference is the
[AI_AGENT_GUIDE](LEARNING_2_0/AI_AGENT_GUIDE/README.md) (it serves humans too);
mandatory ADR order is the [DECISION_GRAPH](LEARNING_2_0/PROJECT_BRAIN/DECISION_GRAPH.md).

## Owner shortcut
Steps 1→3→5 + the My Earnings/settlement screens = enough to RUN the factory.
The rest deepens at your pace.
