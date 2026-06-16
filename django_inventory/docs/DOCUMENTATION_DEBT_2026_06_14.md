# Documentation Debt — from /find-canonical audit (2026-06-14)

**Status: LOGGED, NOT EXECUTED.** This file records the canonical-audit findings as deferred
cleanup. **No audited doc was modified; no doc archived; no manifest edited.** Execute as a
single docs-sync sprint when scheduled. **S6 (`reported_quantity` column DROP) is out of scope** —
the column stays; the (c) items below only fix docs that *teach* the wrong payable surface.

## Foundation stream — CLOSED 2026-06-14
S1 ✅ · S1.1 ✅ · S3 ✅ · S4 ✅ · F1–F4 ✅ · Browser E2E ✅ · S5 ✅ · **S6 intentionally deferred**
(post-deploy + soak + MT-1 backup + rollback review). Current-state: [FOUNDATION_STATUS_SUMMARY](FOUNDATION_STATUS_SUMMARY_2026_06_14.md).
Audit basis: 641 tests green; prod 0037–0042 + expense 0010/0011; every built fact verified vs code.

---

## 1. ARCHIVE (→ `docs/archive/`; superseded design or frozen build-done receipts)
Superseded design chain (claims contradict shipped 0040–0042):
- `docs/PRODUCTION_TRUTH_FOUNDATION_ROADMAP.md` *(highest — reported_quantity alias, allocation_mode strict/open, WorkerStageAllocationHistory all absent from build)*
- `docs/PRODUCTION_TRUTH_FOUNDATION_REVIEW.md`
- `docs/PRODUCTION_TRUTH_FOUNDATION_FINAL.md`
- `docs/PRODUCTION_TRUTH_FOUNDATION_LOCKED.md`
- `docs/IMPLEMENTATION_MASTER_PLAN.md` (v1) · `docs/IMPLEMENTATION_RISK_REVIEW.md`
- `docs/M1_M4_REVIEW_2026_06_14.md` · `docs/FOUNDATION_DESIGN_CHALLENGE_2026_06_14.md`
- `docs/ARCH_READINESS_REVIEW_2026_06_12.md`

Frozen build-done receipts (build committed; keep readable in archive):
- `docs/S1_HOSTILE_REVIEW_2026_06_14.md` · `docs/S1_S4_HOSTILE_REVIEW_2026_06_14.md` · `docs/S1_S4_E2E_REVIEW_2026_06_14.md`
- `docs/S3_DESIGN_RECEIPT_2026_06_14.md` · `docs/S4_IMPLEMENTATION_RECEIPT_2026_06_14.md`
- `docs/S4_PHASE3_RECEIPT_2026_06_14.md` · `docs/S4_PHASE4_RECEIPT_2026_06_14.md` · `docs/S4_PHASE5_RECEIPT_2026_06_14.md`
- `docs/S5_DESIGN_RECEIPT_2026_06_14.md`

Low-priority / optional: `docs/audit_phases/*` (11 files — pre-staging audit; historical input).

**Keep live (never archive):** `FOUNDATION_STATUS_SUMMARY_2026_06_14.md`, `S4_DESIGN_CORRECTION_ADDENDUM_2026_06_14.md`,
`IMPLEMENTATION_MASTER_PLAN_V2.md`, `R1_STAGE_DOMAIN_REVIEW.md`, all 17 manifest canonicals,
forward-looking staging/deploy docs (DEPLOYMENT_PACKAGE, ENFORCEMENT_ROLLOUT_RUNBOOK, STAGING_READINESS,
STAGING_OBSERVATION_FRAMEWORK, SOAK_TRACKER).

## 2. UPDATE (keep, fix stale claims)
| Doc | Fix | Sev |
|---|---|---|
| `docs/LEARNING/02_DATABASE_RELATIONSHIPS.md` | **manifest CANONICAL data-model** still teaches WSC = `reported_quantity (IMMUTABLE)`; add good (NOT NULL, payable)/alter/missing; note reported = dual-written legacy | **HIGH** |
| `CHANGELOG.md` | frozen 2026-06-02 "uncommitted"; add released V2 + S1–S5 + F1–F4 sections | MED |
| `SYSTEM_DESIGN.md` | mark "AddaSettlement design-only / earnings credit at allocation" bullet historical → ARCHITECTURE_V2 | MED |
| `docs/adr/0005-…option-b.md` | mark "DESIGN-ONLY, not built" + "credit at allocation" lines historical (locked ADR — **update, never archive**) | MED |
| `docs/PRE_S1_DESIGN_ADDENDUM.md` | banner: APSCPB-reuse premise overridden, StagePoolSnapshot = new table, prod 0037-0042 built → S4_DESIGN_CORRECTION | MED |
| `docs/REMEDIATION_PLAN.md` | test baselines 305/389 → 641; V2 past-tense | LOW |
| `README.md` | Django 5.2 → 5.0.1 | LOW |

## 3. `reported_quantity` "stale payable-truth" (c) — UPDATE before S6
These present `reported_quantity` as the production/settle quantity with no good/alter/missing.
(Column still exists + dual-written = good, so all are non-urgent until S6 retirement.)

| Doc | Stale claim | Sev |
|---|---|---|
| `docs/LEARNING/02_DATABASE_RELATIONSHIPS.md` | (see §2 HIGH) | HIGH |
| `docs/LEARNING/05_PRODUCTION_TRUTH.md:9` | "three quantities" omits good/alter/missing | MED |
| `docs/LEARNING_2_0/DATABASE_GUIDE/worker_stage_contribution.md:11,27` | schema ref missing 3 cols + swapped constraint; settle SQL `COALESCE(verified,reported)` | MED |
| `config/production/README.md:408` | "WSC = PRODUCTION truth (reported_quantity immutable…)" | MED |
| `docs/LEARNING_2_0/REQUEST_JOURNEYS/settlement_finalize.md:18,68` | "settle qty = verified else **reported**" → `?? good` | MED |
| `docs/LEARNING_2_0/REQUEST_JOURNEYS/worker_reporting.md:2,22,25` | reported framing + dead constraint `reported_quantity > 0` | MED |
| `docs/LEARNING_2_0/ARCHITECTURE_EXPLAINED/02_why_workerstagecontribution.md:7,11` | "3 quantities" omits good/alter/missing | MED-LOW |
| `docs/LEARNING/09_SQL_BEGINNER_TO_ADVANCED.md:71,102,127` | `SUM(reported)` = pieces; `COALESCE(verified,reported)` = settle | LOW |
| `docs/LEARNING_2_0/PROJECT_BRAIN/DEBUGGING_INDEX.md:10` | "settle uses verified-else-reported" | LOW |
| `docs/LEARNING_2_0/DATA_FLOWS/worker_reporting_flow.md:14,21` | reported framing + dead `qty>0` constraint | LOW |
| `docs/STAGING_OBSERVATION_FRAMEWORK_2026_06_14.md:5,62,73` | billed qty `verified ?? reported` → `?? good` (equal via dual-write; forward correctness) | LOW |

**Already S3-aware — no change (reference):** `LEARNING_2_0/CHOKEPOINTS/worker_task_service.md`,
`LEARNING_2_0/APPS/production/FILE_MAP.md`, `IMPLEMENTATION_MASTER_PLAN_V2.md`.
**(b) dual-write legacy / still-true rules — keep:** `AI_AGENT_GUIDE/README.md:42`, `DJANGO_GUIDE/README.md:45`,
`PROJECT_BRAIN/SEARCH_INDEX.md:26`, `ARCHITECTURE_EXPLAINED/09_why_verified_quantity.md`,
`PROJECT_KNOWLEDGE_MAP.md:54`, `REQUIREMENT_REVIEW_STAGE_TRACKING.md:28`.

## 4. `canonical_manifest.json` — 5 missing S1–S5 topics
`version: 2026-06-13` predates the build; 17 topics route only to pre-foundation canonicals.
**CI-guarded** (`core.tests.PkalsNavigationGuardTests` — dead path fails build); all paths below verified to exist.
Append to `topics[]`, bump `version` → `2026-06-14`:

```json
{ "match": ["good quantity","alter quantity","missing quantity","payable quantity","good/alter/missing"],
  "canonical": "docs/LEARNING_2_0/CHOKEPOINTS/worker_task_service.md",
  "also": ["docs/S3_DESIGN_RECEIPT_2026_06_14.md","docs/FOUNDATION_STATUS_SUMMARY_2026_06_14.md"] },
{ "match": ["pool","stage allocation","WorkerStageAllocation","StagePoolSnapshot","allocation bound","allocation_dimensions"],
  "canonical": "docs/LEARNING_2_0/CHOKEPOINTS/pool_service.md",
  "also": ["docs/S4_DESIGN_CORRECTION_ADDENDUM_2026_06_14.md","docs/FOUNDATION_STATUS_SUMMARY_2026_06_14.md"] },
{ "match": ["adda role rate","resolved pay rate","AddaStageRoleRate","rate correction","rerate","settlement rate resolver"],
  "canonical": "docs/ARCHITECTURE_V2.md",
  "also": ["docs/FOUNDATION_STATUS_SUMMARY_2026_06_14.md","docs/LEARNING_2_0/CHOKEPOINTS/cost_service.md"] },
{ "match": ["current foundation state","what S1-S5 built","production-truth foundation","enforcement flags"],
  "canonical": "docs/FOUNDATION_STATUS_SUMMARY_2026_06_14.md",
  "also": ["docs/IMPLEMENTATION_MASTER_PLAN_V2.md"] },
{ "match": ["enforcement rollout","soak","ENFORCE_ALLOCATION_BOUND","ENFORCE_SETTLEMENT_RECONCILIATION","deploy off then enable"],
  "canonical": "docs/ENFORCEMENT_ROLLOUT_RUNBOOK_2026_06_14.md",
  "also": ["docs/STAGING_READINESS_2026_06_14.md"] }
```
No manifest entry needs removal. The `data model` topic route is correct; its target is stale (§2 HIGH) — fix the doc, not the route.

## Execution gating
Run as one docs-sync sprint (own branch). Order: (1) §2/§3 HIGH+MED content fixes, (2) §4 manifest add
+ `manage.py test core` to confirm the navigation guard passes, (3) §1 archive moves last (update any
inbound links — CLAUDE.md, DOCUMENTATION_INDEX, LEARNING_PATH — when moving). Re-run the audit after.
