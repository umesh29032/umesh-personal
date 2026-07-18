# docs/archive — historical, superseded docs

These are **point-in-time snapshots** (dated audits, build-session logs, shipped design
plans). They are kept for provenance only — **not** current contracts. For the live state
read the root [SYSTEM_DESIGN.md](../../SYSTEM_DESIGN.md) (the root `ARCHITECTURE.md` was merged
into SYSTEM_DESIGN.md 2026-06-12; the older copy is archived here as `ARCHITECTURE.md`)
and the active docs under [docs/production/](../production/).

> Durable architectural *decisions* extracted from these (and from the live design docs)
> live as formal records in [docs/adr/](../adr/).

| File | What it was | Superseded by |
|---|---|---|
| `AUDIT_2026_05_29.md` | 2026-05-29 read-only audit | folded into `docs/REMEDIATION_PLAN.md` |
| `ARCHITECTURE.md` | older/smaller architecture doc | merged into root `SYSTEM_DESIGN.md` (2026-06-12; no standalone root ARCHITECTURE.md) |
| `audit_phases_2026_06/PHASE_{B,C,D,E,F,G,H}_*.md` + `POLICY_DECISIONS_B1_A5_B3.md` | 2026-06 production-readiness audit phases (8 files, moved from docs/audit_phases/ at Phase-7 DOCCLEAN-D) | findings closed; current frozen architecture (`../MANUFACTURING_V1_FREEZE.md`) |
| `patterns_ai_phase_reports/` (70 files) | patterns_ai shipped-phase reports/reviews (M-reports, PHASE reports, DESIGN_REVIEWs, DIGITAL_FABRIC/PDM reviews) — moved from docs/AI_PATTERN_INTELLIGENCE/ at DOCCLEAN-D (D-OR-1); the KEEP set (PRODUCT_VISION_V2 · ROADMAP_V2 · PLATFORM_STATUS · freezes · ADR pack · design contracts) stays active | live truth = `../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md` + `PRODUCT_VISION_V2.md` + `../apps/patterns_ai/GUIDE.md` |
| `design_system_working/` (5 files: A2_TC1_MIGRATION_PLAN · B3_MIGRATION_CHECKLIST · B4_BTN_SM_SPEC · DESIGN_SYSTEM_MASTERPLAN · TOKEN_MIGRATION_SPEC) | design-system era build docs, moved at DOCCLEAN-D (D-OR-4) | live vocabulary `../../UI_COMPONENTS.md`; frozen reference DESIGN_SYSTEM_SPEC + UI_COMPONENTS_CATALOG (KEEP, active) |
| `foundation_receipts_2026_06/` (2 files: ERP_PRESTAGING_AUDIT · STAGING_OBSERVATION_FRAMEWORK) | 2026-06 foundation/pre-staging receipts, moved at DOCCLEAN-D (D-OR-5) | current frozen architecture + locked-foundation pair |
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
