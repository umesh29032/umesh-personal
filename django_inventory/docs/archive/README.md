# docs/archive — historical, superseded docs

These are **point-in-time snapshots** (dated audits, build-session logs, shipped design
plans). They are kept for provenance only — **not** current contracts. For the live state
read the root [SYSTEM_DESIGN.md](../../SYSTEM_DESIGN.md) + [ARCHITECTURE.md](../../ARCHITECTURE.md)
and the active docs under [docs/production/](../production/).

> Durable architectural *decisions* extracted from these (and from the live design docs)
> live as formal records in [docs/adr/](../adr/).

| File | What it was | Superseded by |
|---|---|---|
| `AUDIT_2026_05_29.md` | 2026-05-29 read-only audit | folded into `docs/REMEDIATION_PLAN.md` |
| `ARCHITECTURE.md` | older/smaller duplicate of the root ARCHITECTURE.md | root `ARCHITECTURE.md` + `SYSTEM_DESIGN.md` |
| `QA/AUDIT_2026_06_02.md` | QA of the then-uncommitted costing/payroll stack | bugs fixed; current architecture |
| `QA/STAGE_A_REAUDIT_2026_06_02.md` | master-spec re-audit (all crit/high refuted) | — |
| `QA/audit_log.md` · `QA/bugs_found.md` · `QA/fixes_applied.md` | 2026-06-02 QA session ledgers | all listed bugs fixed |
| `production/LAYERING_AUDIT_2026_06_02.md` | dated Layering structural audit | `production/LAYERING_STAGE.md` |
| `production/PAYROLL_GAP_ANALYSIS.md` | 2026-06-02 gap list (next-ship) | `production/PAYROLL_ARCHITECTURE.md` |
| `production/CHAT_LOG.md` | chronological build-session log | `production/DECISION_LOG.md` |
| `production/CUTTING_DESIGN.md` | cutting design spec (shipped 2026-05-29) | `production/OVERVIEW.md` + `CUTTING_PATTERN.md` |
| `production/CUTTING_REVIEW.md` | cutting master-prompt coverage report | — |
| `production/BARCODE_STAGE_PLAN.md` | barcode_generation plan (shipped) | `production/BARCODE_GENERATION.md` |
| `PRE_REFACTOR_INVENTORY.md` | pre-remediation file inventory (the "nothing vanished" oracle) | — |
