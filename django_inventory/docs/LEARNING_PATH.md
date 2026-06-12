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

## Owner shortcut
Steps 1→3→5 + the My Earnings/settlement screens = enough to RUN the factory.
The rest deepens at your pace.
