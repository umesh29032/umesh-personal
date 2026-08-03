---
id: document-discovery-report
type: evidence-cert
status: active
owner: append-only
scope: all — the entire documentation corpus (docs/** + root companions + app READMEs + deploy)
anchors: docs/campaign_contracts/PHASE_06_DOCUMENTATION_DISCOVERY.md
verified: 2026-07-13
---

# DOCUMENT DISCOVERY REPORT — Phase 6 evidence document

> **The single evidence doc for Phase 6 (Documentation Discovery).** Created at DOCDISC-0
> per [campaign_contracts/PHASE_06_DOCUMENTATION_DISCOVERY.md](campaign_contracts/PHASE_06_DOCUMENTATION_DISCOVERY.md)
> §9 — the phase's only new file. Measured against **the Standard**:
> [DOC_STANDARDS.md](DOC_STANDARDS.md) (🔒 `frozen-v1` 2026-07-13; wins over parent §6.1
> defaults where R1–R12 were amended — dated amendments A1/A2). Discovery ONLY: every
> deviation becomes a typed finding; **nothing is repaired, rewritten, moved, archived,
> deleted, or generated in this phase.** Closed sections are append-only; corrections land as
> dated amendments. This report is Phase 7's SOLE work-source.
>
> Born `append-only` ownership class, `active` lifecycle (receipts/evidence skip `draft`,
> Standard §12). Second frontmatter adopter in docs/ (after the Standard itself, per the
> R2-ratified new-docs-immediately rule).

## Findings classification (normative — contract §6.1)

One class per finding; a file with multiple deviations gets multiple findings:
`Missing` · `Duplicate` · `Stale` · `Broken link` · `Wrong canonical source` ·
`Wrong ownership` · `Wrong tier` · `Wrong metadata` (per the R2 adoption rule — retrofit-scope
docs lacking the 7 fields = work-queue rows, not violations) · `Archive candidate` ·
`Generation candidate` · `KOS violation`. Every finding row: path · class · evidence ·
Standard clause (§-ref into DOC_STANDARDS.md) · proposed Phase-7 action · risk flag.

---

## DOCDISC-0 — Charter + inherited-standard validation (2026-07-13) ✅ mechanics; ⏸ DD-1..DD-3 AWAITING OWNER

### Execution gate — PASS (contract §4/§16.2)

| Check | Result |
|---|---|
| `docs/DOC_STANDARDS.md` exists | ✓ |
| Lifecycle status `frozen-v1` | ✓ — metadata block quoted below, read from disk 2026-07-13 |
| Entry-points wired | ✓ DOCUMENTATION_INDEX Entry-points row (3 references) · START_HERE map-of-maps pointer (1) · framework README parent-contract linkage live |
| Phase-5 §3 criteria spot-check | ✓ PHASE_05 Appendix A BOTH halves filled (R1–R12 "Default accepted" ×12, dated; Acceptance half 3/3 fields filled + dated amendments A1/A2) · §DOC-1 + §DOC-2 evidence sections on disk · status file Phase-5 row ✅ COMPLETE. (Sole remaining `_(pending)_` string in PHASE_05 = line 773, a DOC-2 evidence-narrative quote of the ENTRY state — not an unfilled field.) |

The Standard's metadata block as found on disk (gate proof):

```yaml
---
id: doc-standards
type: truth-lock
status: frozen-v1
owner: frozen
scope: all apps, all features — the documentation system itself
anchors: docs/campaign_contracts/PHASE_05_DOCUMENTATION_FOUNDATION.md
verified: 2026-07-13
---
```

### Parent §2.1 landscape facts — re-verified from disk (drift verdict: explained campaign growth, NOT material; §16.6 untriggered)

| Fact | Parent authoring (2026-07-12) | Now (2026-07-13) | Command |
|---|---|---|---|
| docs/ md | 496 | **519** (+22 campaign corpus through DOC-0, +1 DOC_STANDARDS.md at DOC-1) | `find docs -name "*.md" \| wc -l` |
| docs/ json | 2 | **2** | `find docs -name "*.json" \| wc -l` |
| docs/archive/ md | 104 | **104** (unchanged) | `find docs/archive -name "*.md" \| wc -l` |
| AI_PATTERN_INTELLIGENCE md | 104 | **104** (unchanged) | `find docs/AI_PATTERN_INTELLIGENCE -name "*.md" \| wc -l` |
| canonical_manifest.json version | "2026-06-13" (stale-as-documented) | **"2026-06-13"** — UNTOUCHED, read-only this phase (§10) | grep version key |
| docs/pkals_v2/ | 5 md | **5 md** ✓ | ls |
| docs/features/ | absent | **absent** ✓ (Phase-9 artifact) | ls |
| Frontmatter adoption | 0/496 | **1/519** = DOC_STANDARDS.md only (line-1 `---` census; this report becomes the 2nd) | head -1 loop |

### DD-1-default census-boundary baseline (mechanical, pre-report-creation)

| Boundary component | Count | Detail |
|---|---|---|
| `docs/**` md | 519 | includes archive 104 + AI_PATTERN_INTELLIGENCE 104 (family-depth per DD-2) |
| `docs/**` json | 2 | canonical_manifest.json + FRONTEND_DESIGN_SYSTEM_INVENTORY.partial.json (stray, B.3 item 9) |
| Repo-root companions | 7 | README.md · CHANGELOG.md · CLAUDE.md · GLOSSARY.md · SYSTEM_DESIGN.md · UI_COMPONENTS.md · ABOUT_THIS_PROJECT.md — all 7 present |
| `config/<app>/README.md` | 10 | accounts · core · expense · inventory · machines · patterns_ai · production · raw_materials · storefront · tracking (9 apps + core) |
| `deploy/README.md` | 1 | present |
| **Boundary total (pre-report)** | **539** | = 519 + 2 + 7 + 10 + 1. This report's creation makes docs/ md = 520 / boundary = 540; the report and the §9 allowlist are census-EXEMPT self-writes, disclosed here. |

Environment anchor: git HEAD `49404001` · 2 stashes (matches status file) · zero git writes.

### Design Record charter — DD-1..DD-3 presented with binding defaults ⏸ AWAITING OWNER

Presented per contract Appendix A; **no owner answer fabricated** — the execution order
("Execute DOCDISC-0 exactly according to the frozen Phase 06 contract") contained no
ratification language, so the decision half stays `_(pending)_` until the owner answers
(FIX-0 precedent). **DOCDISC-A is gated on these answers (contract §16.3).**

| # | Item | Binding default (unless overridden) |
|---|---|---|
| DD-1 | Census boundary | §2.1 as written: docs/** + 7 root companions + config/<app>/README.md ×10 + deploy/README.md; excludes .claude/, code docstrings, agent memory. Baseline above = this default, measured: **539 files** |
| DD-2 | AI_PATTERN_INTELLIGENCE + archive depth | Family-level census (per-file rows, staleness judgment at family granularity, mirroring DOCUMENT_ARCHIVE_REVIEW); full per-file judgment only where a family is mixed |
| DD-3 | Staleness threshold | Stale = contradicts current code/certified truth OR superseded-in-fact without banner; age/date alone never qualifies |

### Seeded-inputs table (contract §2.2 — every item must be re-verified + disposed before DOCDISC-G)

| # | Seed | Source | Enters at | Disposition |
|---|---|---|---|---|
| 1a | Parent Appendix B.2 (2026-07-11 audit findings: archive index 12 rows vs 104 files · manifest stale 17 topics · PKALS APPS missing machines+patterns_ai · 3 drifted app READMEs · 41 broken memory links → appendix note) | PHASE_05 B.2 | B/C/D/E | _(pending)_ |
| 1b | Parent Appendix B.3 (9-item fresh drift register: read-4-files terminology · roadmap canonical pointer · REQUEST_JOURNEYS rows 4–12 · CHOKEPOINTS history_service · archive README 12/104 + banner 42/104 + dead ARCHITECTURE.md pointer · apps README blurbs · PAGES backlog · pkals_v2 disposition · minor trio) | PHASE_05 B.3 | A–F per item | _(pending)_ |
| 2 | [DOCUMENT_ARCHIVE_REVIEW.md](DOCUMENT_ARCHIVE_REVIEW.md) (family-level KEEP/SUPERSEDED/ARCHIVE/REMOVE-LATER) | 2026-07-11 review | E (per-file reconciliation; KEEP-overrule = stop §16.8) | _(pending)_ |
| 3 | Backlog #6 (RBAC.md role-table drift) + pre-logged patterns_ai README drift | DEPLOYMENT_BACKLOG + status carry-over | Stale register (with certification citations) | _(pending)_ |
| 4 | The Standard's §6.2 register + Phase-5 evidence (applied, never re-litigated) | DOC_STANDARDS + PHASE_05 | all | _(pending)_ |
| 5 | **Worker-Certification meta-audit evidence** (survives only in agent memory, not in WORKER_ROLE_CERTIFICATION.md) — dated amendment 2026-07-13: DOCDISC-A registers a `Missing`-class finding against WORKER_ROLE_CERTIFICATION.md; Phase-7 queue carries its materialization; unrecoverable detail honestly marked | PHASE_06 Appendix A amendment | A | _(pending)_ |

### DOCDISC-0 scope discipline

Zero corpus mutations (census observed read-only; all counts from `find`/`grep`/`ls`/`head`).
Writes this sub-phase = this report (NEW) + DOCUMENTATION_INDEX report row + status file +
memory = the §9 allowlist exactly. canonical_manifest.json untouched. Battery NEVER runs this
phase (§13) — baseline 1530/1530 stands, not re-verified. No app login/passwords/dev server
used. U6 app-doc lookups: N/A phase-wide (no code changes) — stated once here per §11d.

---

## Owner directive (2026-07-13, post-DOCDISC-0, dated append) — SINGLE-CANONICAL-HOME OBJECTIVE

Owner clarification received after DOCDISC-0 close (recorded verbatim in PHASE_06 Appendix A
dated amendments): documentation must converge on **one canonical home per topic — the same
knowledge never permanently scattered**. Binding on this report's registers:

- **Duplicate/fragmentation finding rows carry 4 extra fields:** current locations ·
  recommended canonical location · why consolidation benefits · owning cleanup phase.
- Phase 6 = discover/classify/record ONLY (unchanged); Phase 7 = consolidate per the work
  queue; no duplicate LIVING documentation survives cleanup.
- KOS end-state: from one canonical document, navigate to every related URL, model, table,
  business rule, ADR, and implementation detail (Phases 8–9 graph/cards = the fabric).
- This operationalizes Standard §1.3 (one-canonical-per-topic); it answers none of DD-1..DD-3
  — DOCDISC-A remains gated on those.

---

## 1. Document census (DOCDISC-A, 2026-07-13) ✅

### DD-1..DD-3 ratified

Owner order 2026-07-13: **"I ACCEPT THE DEFAULTS exactly as defined by the Phase 6 contract"**
— DD-1 (boundary as §2.1, "Do not expand or reduce"), DD-2 (family-level
AI_PATTERN_INTELLIGENCE + archive), DD-3 (stale = contradicts truth or
superseded-without-banner; never age alone). Verbatim answers recorded in PHASE_06
Appendix A. Same order re-binds the Single-Canonical-Home directive onto every finding and
gates this session to DOCDISC-A only.

### Method (mechanical census scripted read-only from scratchpad; judgment main-thread)

Script `docdisc_a_census.py` (scratchpad; read-only over the repo) enumerated the DD-1
boundary and emitted per-file: path · size KB · mtime month · naming-style match ·
frontmatter presence. Tier/type/ownership/lifecycle assigned by **disclosed heuristic rules**
(directory + filename patterns encoding Standard §2 tiers / §3 typology / §11 classes / §12
states) — the census is the *inventory baseline*; hierarchy verification is DOCDISC-B's
mandate, ownership audit DOCDISC-C's. Naming styles matched against the Standard §14 closed
set. **Known heuristic imprecisions (spot-justified, main-thread; queued for B/C — not
silently wrong):**

1. `docs/README.md` heuristic-classed `topic-canonical`; probably `entry-index` (docs-dir
   front matter) → DOCDISC-B verifies.
2. AI_PATTERN_INTELLIGENCE receipts carry family default `owner: handwritten`; Standard §12
   would born-class them `append-only` → DOCDISC-C reconciles (family-level, DD-2).
3. `docs/audit_phases/*` heuristic-classed T2/topic-canonical; content is closed audit
   receipts (2026-06) → likely T7/receipt + archive candidates → DOCDISC-B/E adjudicate.
4. `docs/pkals_v2/*` lifecycle recorded `superseded?` — proposal pack, binds nothing
   (Standard §7); no banner exists; disposition = seeded B.3-8 → DOCDISC-E.
5. LEARNING_2_0 CHOKEPOINTS classed T2 (Standard §2 lists CHOKEPOINTS pages at T2) while the
   rest of LEARNING_2_0 is T6 academy — split is deliberate, per the Standard.
6. Campaign contracts classed `frozen` ownership with the standing exception of their
   designated fill sections (Design Records/evidence) — noted per row.

### Per-directory rollup (mechanical)

| Directory group | Files | Tiers | FM |
|---|---|---|---|
| (repo root) | 7 | T0:1 T2:3 T3:1 T5:1 T6:1 | 0 |
| config/<app> (10 groups) | 10 | T3:10 | 0 |
| deploy | 1 | T2:1 | 0 |
| docs (root level) | 130 | T0:3 T1:7 T2:31 T5:9 T7:79 T?:1 | 2 |
| docs/AI_PATTERN_INTELLIGENCE | 104 | T2:43 T7:61 | 0 |
| docs/LEARNING | 11 | T6:11 | 0 |
| docs/LEARNING_2_0 | 98 | T0:2 T2:8 T6:88 | 0 |
| docs/PAGES | 2 | T2:2 | 0 |
| docs/adr | 12 | T1:12 | 0 |
| docs/apps | 11 | T3:11 | 0 |
| docs/archive | 104 | T8:104 | 0 |
| docs/audit_phases | 11 | T2:11 | 0 |
| docs/campaign_contracts | 23 | T5:23 | 0 |
| docs/pkals_v2 | 5 | T5:5 | 0 |
| docs/production | 10 | T2:10 | 0 |
| docs/tracking | 1 | T2:1 | 0 |
| **TOTAL** | **540** | | **2** |

Naming-style distribution: ALL_CAPS 369 · lowercase_snake 52 · dated 46 · PHASE_NN_SLUG 21 ·
NN_TOPIC 16 · NNNN-kebab 11 · json-index 1 · **VIOLATION 24** (23 active-tree + 1 archive).

**Boundary-drift check vs DOCDISC-0 baseline (539):** 540 = 539 + 1 — the +1 is this report
itself (created at DOCDISC-0, disclosed there as the census-exempt self-write; it is
nonetheless ROWED below for §3.2 completeness). Drift EXPLAINED → DOCDISC-A stop-delta clear.

### Full census (one row per boundary file; file names relative to the group heading; ⟨notes⟩ inline)

#### (repo root) (7 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| ABOUT_THIS_PROJECT.md | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 12 | 2026-06 |
| CHANGELOG.md | T5 | status-anchor | handwritten | active | ALL_CAPS |  | 3 | 2026-06 |
| CLAUDE.md | T0 | entry-index | handwritten | active | ALL_CAPS |  | 15 | 2026-07 |
| GLOSSARY.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 9 | 2026-07 |
| README.md ⟨repo front door (Standard §4)⟩ | T3 | entry-index | handwritten | active | ALL_CAPS |  | 10 | 2026-06 |
| SYSTEM_DESIGN.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 55 | 2026-06 |
| UI_COMPONENTS.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 25 | 2026-07 |

#### config/accounts (1 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| README.md | T3 | app-readme | handwritten | active | ALL_CAPS |  | 19 | 2026-07 |

#### config/core (1 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| README.md | T3 | app-readme | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |

#### config/expense (1 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| README.md | T3 | app-readme | handwritten | active | ALL_CAPS |  | 17 | 2026-07 |

#### config/inventory (1 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| README.md | T3 | app-readme | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |

#### config/machines (1 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| README.md | T3 | app-readme | handwritten | active | ALL_CAPS |  | 3 | 2026-07 |

#### config/patterns_ai (1 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| README.md | T3 | app-readme | handwritten | active | ALL_CAPS |  | 1 | 2026-07 |

#### config/production (1 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| README.md | T3 | app-readme | handwritten | active | ALL_CAPS |  | 23 | 2026-07 |

#### config/raw_materials (1 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| README.md | T3 | app-readme | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |

#### config/storefront (1 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| README.md | T3 | app-readme | handwritten | active | ALL_CAPS |  | 2 | 2026-06 |

#### config/tracking (1 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| README.md | T3 | app-readme | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |

#### deploy (1 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| README.md ⟨THE deployment runbook (PHASE_19)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 4 | 2026-06 |

#### docs (130 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| A2_TC1_MIGRATION_PLAN.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 13 | 2026-06 |
| A360_EXECUTION_PLAN.md | T7 | receipt | append-only | active | ALL_CAPS |  | 13 | 2026-07 |
| ADDA_OVERVIEW_AUDIT_2026_07_05.md | T7 | receipt | append-only | active | dated |  | 12 | 2026-07 |
| ALLOCATION_WORKFLOW_AUDIT_2026_07_05.md | T7 | receipt | append-only | active | dated |  | 38 | 2026-07 |
| ARCHITECTURE_V2.md | T1 | truth-lock | frozen | frozen | ALL_CAPS |  | 44 | 2026-06 |
| ARCH_READINESS_REVIEW_2026_06_12.md | T7 | receipt | append-only | active | dated |  | 10 | 2026-06 |
| AUDIT_SYSTEM_MAP.md | T7 | receipt | append-only | active | ALL_CAPS |  | 142 | 2026-07 |
| AUTH_FAMILY_CONSOLIDATION_REPORT.md | T7 | receipt | append-only | active | ALL_CAPS |  | 12 | 2026-06 |
| B2_GEOMETRY_B_PROOF_PLAN.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 9 | 2026-06 |
| B3_MIGRATION_CHECKLIST.md | T5 | status-anchor | handwritten | active | ALL_CAPS |  | 7 | 2026-06 |
| B4_BTN_SM_SPEC.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 6 | 2026-06 |
| BARCODE_ARCHITECTURE_REVIEW.md | T7 | receipt | append-only | active | ALL_CAPS |  | 7 | 2026-07 |
| BARCODE_IDENTITY_REVIEW.md | T7 | receipt | append-only | active | ALL_CAPS |  | 7 | 2026-07 |
| BARCODE_IMPLEMENTATION_READINESS.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 3 | 2026-07 |
| BUNDLE_ASSEMBLY_ARCHITECTURE_REVIEW.md | T7 | receipt | append-only | active | ALL_CAPS |  | 15 | 2026-07 |
| BUTTONS_AUDIT_REPORT.md | T7 | receipt | append-only | active | ALL_CAPS |  | 9 | 2026-06 |
| BUTTONS_FOUNDATION_SPEC.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 8 | 2026-06 |
| BUTTONS_MIGRATION_MATRIX.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 10 | 2026-06 |
| CONFIRMED_FINDINGS_LEDGER.md | T7 | evidence-cert | append-only | active | ALL_CAPS |  | 49 | 2026-07 |
| CUTTING_CYCLES_ARCHITECTURE_CHALLENGE.md | T7 | receipt | append-only | active | ALL_CAPS |  | 18 | 2026-07 |
| CUTTING_STREAM_LIFECYCLE.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |
| DATE_FAMILY_CONSOLIDATION_REPORT.md | T7 | receipt | append-only | active | ALL_CAPS |  | 7 | 2026-06 |
| DEPLOYMENT_BACKLOG.md | T5 | status-anchor | handwritten | active | ALL_CAPS |  | 13 | 2026-07 |
| DEPLOYMENT_CAMPAIGN_STATUS.md | T5 | status-anchor | handwritten | active | ALL_CAPS |  | 103 | 2026-07 |
| DEPLOYMENT_PACKAGE_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 7 | 2026-06 |
| DESIGN_SYSTEM_IMPLEMENTATION_ROADMAP.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 16 | 2026-06 |
| DESIGN_SYSTEM_MASTERPLAN.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 14 | 2026-06 |
| DESIGN_SYSTEM_SPEC.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 19 | 2026-06 |
| DOCUMENTATION_DEBT_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 8 | 2026-06 |
| DOCUMENTATION_INDEX.md | T0 | entry-index | handwritten | active | ALL_CAPS |  | 34 | 2026-07 |
| DOCUMENT_ARCHIVE_REVIEW.md | T7 | receipt | append-only | active | ALL_CAPS |  | 7 | 2026-07 |
| DOCUMENT_DISCOVERY_REPORT.md ⟨this report⟩ | T7 | evidence-cert | append-only | active | ALL_CAPS | Y | 10 | 2026-07 |
| DOC_STANDARDS.md | T1 | truth-lock | frozen | frozen | ALL_CAPS | Y | 28 | 2026-07 |
| END_TO_END_BUSINESS_AUDIT_2026_07_05.md | T7 | receipt | append-only | active | dated |  | 13 | 2026-07 |
| ENFORCEMENT_ROLLOUT_RUNBOOK_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 4 | 2026-06 |
| ENGINEERING_EXCELLENCE_SWEEP_2026_07_06.md | T7 | receipt | append-only | active | dated |  | 8 | 2026-07 |
| ERP_MASTER_CONTEXT.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 20 | 2026-06 |
| ERP_PRESTAGING_AUDIT_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 14 | 2026-06 |
| FACTORY_OPERATIONS_MASTER.md | T1 | truth-lock | frozen | frozen | ALL_CAPS |  | 40 | 2026-07 |
| FAMILY_F_MODALS_REPORT.md | T7 | receipt | append-only | active | ALL_CAPS |  | 3 | 2026-06 |
| FAMILY_G_REMAINING_SURFACES_REPORT.md | T7 | receipt | append-only | active | ALL_CAPS |  | 7 | 2026-06 |
| FORMS_AUDIT_REPORT.md | T7 | receipt | append-only | active | ALL_CAPS |  | 6 | 2026-06 |
| FORMS_FOUNDATION_SPEC.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 6 | 2026-06 |
| FORMS_MIGRATION_MATRIX.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 5 | 2026-06 |
| FORM_CONTROL_CONSOLIDATION_REPORT.md | T7 | receipt | append-only | active | ALL_CAPS |  | 14 | 2026-06 |
| FOUNDATION_DESIGN_CHALLENGE_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 17 | 2026-06 |
| FOUNDATION_STATUS_SUMMARY_2026_06_14.md | T5 | status-anchor | handwritten | active | dated |  | 7 | 2026-06 |
| FRONTEND_AUDIT_2026_07_05.md | T7 | receipt | append-only | active | dated |  | 10 | 2026-07 |
| FRONTEND_DESIGN_SYSTEM_ARCHITECTURE.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 19 | 2026-06 |
| FRONTEND_DESIGN_SYSTEM_INVENTORY.partial.json ⟨stray artifact — finding⟩ | T? | machine-index | ? | ? | VIOLATION |  | 53 | 2026-06 |
| FRONTEND_DESIGN_SYSTEM_STATUS.md | T5 | status-anchor | handwritten | active | ALL_CAPS |  | 13 | 2026-06 |
| HTML_AUDIT_LEDGER.md | T7 | receipt | append-only | active | ALL_CAPS |  | 188 | 2026-06 |
| HTML_AUDIT_MASTER.md | T7 | receipt | append-only | active | ALL_CAPS |  | 26 | 2026-06 |
| HTML_CANONICAL_CANDIDATES.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 122 | 2026-06 |
| HTML_FIX_HISTORY.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 6 | 2026-06 |
| IMPLEMENTATION_MASTER_PLAN.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 14 | 2026-06 |
| IMPLEMENTATION_MASTER_PLAN_V2.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 16 | 2026-06 |
| IMPLEMENTATION_READINESS_PRE_PRODUCTION.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| IMPLEMENTATION_RISK_REVIEW.md | T7 | receipt | append-only | active | ALL_CAPS |  | 10 | 2026-06 |
| IMPLEMENTATION_ROADMAP_PDD_V1.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 15 | 2026-07 |
| LEARNING_PATH.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 5 | 2026-06 |
| M1_M4_REVIEW_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 9 | 2026-06 |
| MANAGEMENT_ROLE_CERTIFICATION.md | T7 | evidence-cert | append-only | active | ALL_CAPS |  | 73 | 2026-07 |
| MANUFACTURING_EXCELLENCE_AUDIT_2026_07_06.md | T7 | receipt | append-only | active | dated |  | 8 | 2026-07 |
| MANUFACTURING_V1_FREEZE.md | T1 | truth-lock | frozen | frozen | ALL_CAPS |  | 20 | 2026-07 |
| MULTISELECT_FAMILY_CONSOLIDATION_REPORT.md | T7 | receipt | append-only | active | ALL_CAPS |  | 7 | 2026-06 |
| OFFICE_SUPPORT_ROLE_CERTIFICATION.md | T7 | evidence-cert | append-only | active | ALL_CAPS |  | 61 | 2026-07 |
| OP1_EXECUTION_PLAN.md | T7 | receipt | append-only | active | ALL_CAPS |  | 8 | 2026-07 |
| OWNER_VISIBILITY_CERTIFICATION.md | T7 | evidence-cert | append-only | active | ALL_CAPS |  | 91 | 2026-07 |
| PENDING_BACKLOG.md | T5 | status-anchor | handwritten | active | ALL_CAPS |  | 20 | 2026-07 |
| PKALS_RELEASE_v1.md | T2 | topic-canonical | handwritten | active | VIOLATION |  | 4 | 2026-06 |
| PRE_FREEZE_FINAL_AUDIT_2026_07_05.md | T7 | receipt | append-only | active | dated |  | 15 | 2026-07 |
| PRE_PRODUCTION_ARCHITECTURE_FINAL_REVIEW.md | T7 | receipt | append-only | active | ALL_CAPS |  | 16 | 2026-07 |
| PRE_PRODUCTION_ARCHITECTURE_REVIEW.md | T7 | receipt | append-only | active | ALL_CAPS |  | 9 | 2026-07 |
| PRE_PRODUCTION_REDESIGN_PROPOSAL.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 8 | 2026-07 |
| PRE_R10_POLISH_EXECUTION_PLAN.md | T7 | receipt | append-only | active | ALL_CAPS |  | 13 | 2026-07 |
| PRE_S1_DESIGN_ADDENDUM.md | T1 | truth-lock | frozen | frozen | ALL_CAPS |  | 20 | 2026-06 |
| PRODUCTION_ARCHITECTURE_FINAL_IMPLEMENTATION_AUDIT.md | T7 | receipt | append-only | active | ALL_CAPS |  | 13 | 2026-07 |
| PRODUCTION_AUDIT_STATUS.md | T5 | status-anchor | handwritten | active | ALL_CAPS |  | 169 | 2026-06 |
| PRODUCTION_COMPONENT_ARCHITECTURE_REVIEW.md | T7 | receipt | append-only | active | ALL_CAPS |  | 12 | 2026-07 |
| PRODUCTION_ENGINE_FREEZE.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 7 | 2026-07 |
| PRODUCTION_READINESS_CHECKLIST.md | T5 | status-anchor | handwritten | active | ALL_CAPS |  | 16 | 2026-07 |
| PRODUCTION_TRUTH_FOUNDATION_FINAL.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 10 | 2026-06 |
| PRODUCTION_TRUTH_FOUNDATION_LOCKED.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 5 | 2026-06 |
| PRODUCTION_TRUTH_FOUNDATION_REVIEW.md | T7 | receipt | append-only | active | ALL_CAPS |  | 16 | 2026-06 |
| PRODUCTION_TRUTH_FOUNDATION_ROADMAP.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 14 | 2026-06 |
| PRODUCT_DESIGN_DOCUMENT.md | T1 | truth-lock | frozen | frozen | ALL_CAPS |  | 39 | 2026-07 |
| PROJECT_KNOWLEDGE_MAP.md | T0 | entry-index | handwritten | active | ALL_CAPS |  | 15 | 2026-07 |
| R10_EXECUTION_PLAN.md | T7 | receipt | append-only | active | ALL_CAPS |  | 16 | 2026-07 |
| R10_MACHINE_STAGES_ARCHITECTURE_2026_07_05.md | T7 | receipt | append-only | active | dated |  | 29 | 2026-07 |
| R1_EXECUTION_PLAN.md | T7 | receipt | append-only | active | ALL_CAPS |  | 6 | 2026-07 |
| R1_STAGE_DOMAIN_REVIEW.md | T7 | receipt | append-only | active | ALL_CAPS |  | 29 | 2026-06 |
| R2_EXECUTION_PLAN.md | T7 | receipt | append-only | active | ALL_CAPS |  | 8 | 2026-07 |
| R3_EXECUTION_PLAN.md | T7 | receipt | append-only | active | ALL_CAPS |  | 9 | 2026-07 |
| R4_EXECUTION_PLAN.md | T7 | receipt | append-only | active | ALL_CAPS |  | 13 | 2026-07 |
| R5_EXECUTION_PLAN.md | T7 | receipt | append-only | active | ALL_CAPS |  | 9 | 2026-07 |
| R5_HOSTILE_REVIEW_2026_07_05.md | T7 | receipt | append-only | active | dated |  | 11 | 2026-07 |
| R6_EXECUTION_PLAN.md | T7 | receipt | append-only | active | ALL_CAPS |  | 5 | 2026-07 |
| R7_EXECUTION_PLAN.md | T7 | receipt | append-only | active | ALL_CAPS |  | 12 | 2026-07 |
| R8_EXECUTION_PLAN.md | T7 | receipt | append-only | active | ALL_CAPS |  | 11 | 2026-07 |
| README.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 4 | 2026-06 |
| REMEDIATION_PLAN.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 22 | 2026-06 |
| REQUIREMENT_REVIEW_STAGE_TRACKING.md | T1 | truth-lock | frozen | frozen | ALL_CAPS |  | 14 | 2026-06 |
| RETRO_TAG_SYNC_AUDIT_2026_07_05.md | T7 | receipt | append-only | active | dated |  | 8 | 2026-07 |
| ROADMAP_REVIEW_POST_C1_2026_06_11.md | T7 | receipt | append-only | active | dated |  | 15 | 2026-06 |
| S1_HOSTILE_REVIEW_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 10 | 2026-06 |
| S1_S4_E2E_REVIEW_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 5 | 2026-06 |
| S1_S4_HOSTILE_REVIEW_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 8 | 2026-06 |
| S3_DESIGN_RECEIPT_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 10 | 2026-06 |
| S4_DESIGN_CORRECTION_ADDENDUM_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 22 | 2026-06 |
| S4_IMPLEMENTATION_RECEIPT_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 11 | 2026-06 |
| S4_PHASE3_RECEIPT_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 10 | 2026-06 |
| S4_PHASE4_RECEIPT_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 7 | 2026-06 |
| S4_PHASE5_RECEIPT_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 8 | 2026-06 |
| S5_DESIGN_RECEIPT_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 9 | 2026-06 |
| SELECT_FAMILY_CONSOLIDATION_REPORT.md | T7 | receipt | append-only | active | ALL_CAPS |  | 9 | 2026-06 |
| SOAK_TRACKER.md | T5 | status-anchor | handwritten | active | ALL_CAPS |  | 23 | 2026-07 |
| STAGE_TRIO_SPEC_IMPACT_2026_07_05.md | T7 | receipt | append-only | active | dated |  | 12 | 2026-07 |
| STAGING_OBSERVATION_FRAMEWORK_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 8 | 2026-06 |
| STAGING_READINESS_2026_06_14.md | T7 | receipt | append-only | active | dated |  | 5 | 2026-06 |
| START_HERE.md | T0 | entry-index | handwritten | active | ALL_CAPS |  | 3 | 2026-07 |
| STREAMS_IMPLEMENTATION_RECEIPT.md | T7 | receipt | append-only | active | ALL_CAPS |  | 7 | 2026-07 |
| TABLES_CONSOLIDATION_REPORT.md | T7 | receipt | append-only | active | ALL_CAPS |  | 12 | 2026-06 |
| TARGET_ARCHITECTURE.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 13 | 2026-06 |
| TOKEN_MIGRATION_SPEC.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 17 | 2026-06 |
| TRACKING_ARCHITECTURE_REVIEW.md | T7 | receipt | append-only | active | ALL_CAPS |  | 6 | 2026-07 |
| UI_COMPONENTS_CATALOG.md | T7 | receipt | append-only | active | ALL_CAPS |  | 15 | 2026-06 |
| WHOLE_SYSTEM_ARCHITECTURE_REVIEW.md | T7 | receipt | append-only | active | ALL_CAPS |  | 12 | 2026-06 |
| WORKER_PROFILE_AUDIT_2026_07_05.md | T7 | receipt | append-only | active | dated |  | 5 | 2026-07 |
| WORKER_ROLE_CERTIFICATION.md | T7 | evidence-cert | append-only | active | ALL_CAPS |  | 58 | 2026-07 |

#### docs/AI_PATTERN_INTELLIGENCE (104 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| ACCEPTANCE_REVIEW_VISUAL_PATTERN_MANAGEMENT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 9 | 2026-07 |
| ADR/ADR-A-nesting-engine.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | VIOLATION |  | 5 | 2026-07 |
| ADR/ADR-C-geometry-format.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | VIOLATION |  | 4 | 2026-07 |
| ADR/ADR-D-marker-lifecycle.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | VIOLATION |  | 4 | 2026-07 |
| ADR/ADR-D2-piece-grain.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | VIOLATION |  | 3 | 2026-07 |
| ADR/ADR-D3-capture-provenance.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | VIOLATION |  | 3 | 2026-07 |
| ADR/ADR-E-calibration-metrology.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | VIOLATION |  | 5 | 2026-07 |
| ADR/ADR-F-vendoring-isolation.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | VIOLATION |  | 3 | 2026-07 |
| ADR/ADR-G-media-lifecycle.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | VIOLATION |  | 3 | 2026-07 |
| ADR/ADR-H-app-boundary-governance.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | VIOLATION |  | 4 | 2026-07 |
| ADR/ADR_PACK_CERTIFICATION.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 7 | 2026-07 |
| ARCHITECTURE_AUDIT_2026_07_10.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | dated |  | 18 | 2026-07 |
| BUSINESS_ARCHITECTURE_FREEZE_REVIEW.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 16 | 2026-07 |
| D7_VALIDATION_PROTOCOL.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 3 | 2026-07 |
| DEMO_VALIDATION_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 6 | 2026-07 |
| DESIGN_REVIEW_CUTTING_TABLE_ARCHITECTURE.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 14 | 2026-07 |
| DESIGN_REVIEW_LAYOUT_COMPOSITION.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 10 | 2026-07 |
| DESIGN_REVIEW_REFINED_DIRECTION.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 11 | 2026-07 |
| DIGITAL_FABRIC_PLATFORM_ARCHITECTURE_REVIEW.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 16 | 2026-07 |
| DIGITAL_FABRIC_PLATFORM_FINAL_REVIEW.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 21 | 2026-07 |
| DOC_CLEANUP_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 3 | 2026-07 |
| FINAL_ARCHITECTURE_REVIEW_PDM_CUTTING_TABLE.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 12 | 2026-07 |
| FOUNDATION_V1_AUDIT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 11 | 2026-07 |
| IMPLEMENTATION_READINESS_REVIEW.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 10 | 2026-07 |
| LEGACY_CODE_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| M2_IMPLEMENTATION_PLAN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |
| M2_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 7 | 2026-07 |
| M4.5_IMPLEMENTATION_PLAN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | VIOLATION |  | 20 | 2026-07 |
| M4.5_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | VIOLATION |  | 7 | 2026-07 |
| M4_GENERIC_PLANNER_REVIEW.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 9 | 2026-07 |
| M4_IMPLEMENTATION_PLAN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 16 | 2026-07 |
| M4_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 7 | 2026-07 |
| M5_READINESS.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 2 | 2026-07 |
| M5_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 2 | 2026-07 |
| M6_IMPLEMENTATION_PLAN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 3 | 2026-07 |
| M6_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |
| M8_1_DRAFT_SAFETY_READINESS.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 3 | 2026-07 |
| M8_1_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 3 | 2026-07 |
| M8_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| MA1_IMPLEMENTATION_PLAN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 7 | 2026-07 |
| MANUFACTURING_GEOMETRY_ENGINE_MASTER_DESIGN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 12 | 2026-07 |
| MANUFACTURING_INTEGRATION_REVIEW.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 10 | 2026-07 |
| OWNER_ACCEPTANCE_VALIDATION_PLAN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 28 | 2026-07 |
| OWNER_ACCEPTANCE_VALIDATION_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 15 | 2026-07 |
| P2_GEOMETRY_PIPELINE.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| P5_DEPLOYMENT_RUNBOOK.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 3 | 2026-07 |
| PATTERN_HIERARCHY_FREEZE_REVIEW.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 8 | 2026-07 |
| PATTERN_OS_ARCHITECTURE_PROPOSAL.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 13 | 2026-07 |
| PATTERN_PLATFORM_VISION_REALIGNMENT.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 12 | 2026-07 |
| PDM_W1_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 3 | 2026-07 |
| PDM_W2R2_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 3 | 2026-07 |
| PDM_W2R_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |
| PDM_W2_REDESIGN_REVIEW.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 10 | 2026-07 |
| PDM_W2_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |
| PDM_WORKFLOW_SPLIT_REVIEW.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |
| PDM_WORKSPACE_IMPLEMENTATION_PLAN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 10 | 2026-07 |
| PHASE1_PATTERN_DASHBOARD_PLAN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 7 | 2026-07 |
| PHASE1_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |
| PHASE2_BLUEPRINT_PLAN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 6 | 2026-07 |
| PHASE2_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |
| PHASE3_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| PHASE3_UNIVERSAL_SIZE_PLAN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 7 | 2026-07 |
| PHASE4_COMPLETION_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |
| PHASE4_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 3 | 2026-07 |
| PHASE4_SHELL_PLAN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 7 | 2026-07 |
| PHASE4_WORKSPACE_DESIGN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 3 | 2026-07 |
| PHASE5_COMPLETION_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 6 | 2026-07 |
| PHASE5_INTERACTION_PLAN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 3 | 2026-07 |
| PHASE5_M1_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| PHASE5_M2_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |
| PHASE5_M3_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |
| PHASE5_M4_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| PHASE5_OPTIMIZE_DESIGN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 10 | 2026-07 |
| PHASE5_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| PHASE6A_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| PHASE6B_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| PHASE6C_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| PHASE6_COMPLETION_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |
| PHASE6_EXECUTION_PLAN.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 15 | 2026-07 |
| PHASE6_M1_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 2 | 2026-07 |
| PHASE6_M2_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| PHASE6_M3_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 7 | 2026-07 |
| PHASE6_M4_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |
| PHASE6_M5_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| PHASE6_M6_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 6 | 2026-07 |
| PHASE6_M7_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| PHASE6_M8_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |
| PHASE6_OPTIMIZATION_PLAN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| PHASE7_LAYOUT_LIBRARY_PLAN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 8 | 2026-07 |
| PHASE7_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 6 | 2026-07 |
| PHASE8A_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 3 | 2026-07 |
| PHASE8B_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| PHASE8C_REPORT.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| PHASE8_IMPLEMENTATION_PLAN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 12 | 2026-07 |
| PHASE8_MANUFACTURING_READINESS_REVIEW.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 9 | 2026-07 |
| PLATFORM_RESPONSIBILITY_FREEZE.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 3 | 2026-07 |
| PLATFORM_STATUS.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 16 | 2026-07 |
| PRODUCT_DESIGN_FREEZE.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 17 | 2026-07 |
| PRODUCT_INTEGRATION_DESIGN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 22 | 2026-07 |
| PRODUCT_PATTERN_WORKSPACE_DESIGN.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 13 | 2026-07 |
| PRODUCT_SIZE_PATTERN_ARCHITECTURE_REVIEW.md ⟨AI_PATTERN family (DD-2)⟩ | T7 | receipt | handwritten | active | ALL_CAPS |  | 9 | 2026-07 |
| PRODUCT_VISION_V2.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 2 | 2026-07 |
| ROADMAP_V2.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 6 | 2026-07 |
| UI_WORKFLOW_FREEZE.md ⟨AI_PATTERN family (DD-2)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 14 | 2026-07 |

#### docs/LEARNING (11 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| 01_DJANGO_CONCEPTS.md | T6 | lesson | handwritten | active | NN_TOPIC |  | 2 | 2026-06 |
| 02_DATABASE_RELATIONSHIPS.md | T6 | lesson | handwritten | active | NN_TOPIC |  | 10 | 2026-06 |
| 03_TRANSACTIONS_AND_LOCKS.md | T6 | lesson | handwritten | active | NN_TOPIC |  | 2 | 2026-06 |
| 04_SERVICE_LAYER.md | T6 | lesson | handwritten | active | NN_TOPIC |  | 4 | 2026-06 |
| 05_PRODUCTION_TRUTH.md | T6 | lesson | handwritten | active | NN_TOPIC |  | 1 | 2026-06 |
| 06_FINANCIAL_TRUTH_AND_SETTLEMENT.md | T6 | lesson | handwritten | active | NN_TOPIC |  | 2 | 2026-06 |
| 07_COSTING.md | T6 | lesson | handwritten | active | NN_TOPIC |  | 1 | 2026-06 |
| 08_ADDA_LIFECYCLE.md | T6 | lesson | handwritten | active | NN_TOPIC |  | 1 | 2026-06 |
| 09_SQL_BEGINNER_TO_ADVANCED.md | T6 | lesson | handwritten | active | NN_TOPIC |  | 8 | 2026-06 |
| 10_ONLINE_RESOURCES.md | T6 | lesson | handwritten | active | NN_TOPIC |  | 5 | 2026-06 |
| README.md | T6 | entry-index | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |

#### docs/LEARNING_2_0 (98 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| AI_AGENT_GUIDE/README.md ⟨AI entry⟩ | T0 | entry-index | handwritten | active | ALL_CAPS |  | 5 | 2026-06 |
| AI_AGENT_GUIDE/canonical_manifest.json ⟨hand-maintained until Phase-9 conversion (R5)⟩ | T0 | machine-index | handwritten | active | json-index |  | 6 | 2026-06 |
| APPS/README.md ⟨academy layer⟩ | T6 | entry-index | handwritten | active | ALL_CAPS |  | 2 | 2026-06 |
| APPS/accounts/APP_FLOW.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/accounts/FILE_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/accounts/REQUEST_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/core/APP_FLOW.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/core/FILE_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/core/REQUEST_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/expense/APP_FLOW.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 2 | 2026-06 |
| APPS/expense/FILE_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 3 | 2026-06 |
| APPS/expense/REQUEST_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/inventory/APP_FLOW.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/inventory/FILE_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/inventory/REQUEST_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/production/APP_FLOW.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 2 | 2026-06 |
| APPS/production/FILE_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 9 | 2026-06 |
| APPS/production/REQUEST_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 2 | 2026-06 |
| APPS/raw_materials/APP_FLOW.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/raw_materials/FILE_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/raw_materials/REQUEST_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/storefront/APP_FLOW.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/storefront/FILE_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/storefront/REQUEST_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/tracking/APP_FLOW.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/tracking/FILE_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| APPS/tracking/REQUEST_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| ARCHITECTURE_EXPLAINED/01_why_workerstagetask.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| ARCHITECTURE_EXPLAINED/02_why_workerstagecontribution.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| ARCHITECTURE_EXPLAINED/03_why_addasettlement.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| ARCHITECTURE_EXPLAINED/04_why_workerledgerentry.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| ARCHITECTURE_EXPLAINED/05_why_settlement_not_payment.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| ARCHITECTURE_EXPLAINED/06_why_two_truths.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| ARCHITECTURE_EXPLAINED/07_why_append_only.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| ARCHITECTURE_EXPLAINED/08_why_reversals.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| ARCHITECTURE_EXPLAINED/09_why_verified_quantity.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| ARCHITECTURE_EXPLAINED/10_why_eras.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| ARCHITECTURE_EXPLAINED/11_why_open_closed.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| ARCHITECTURE_EXPLAINED/README.md ⟨academy layer⟩ | T6 | entry-index | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| ARCHITECTURE_VALIDATION/README.md ⟨academy layer⟩ | T6 | entry-index | handwritten | active | ALL_CAPS |  | 4 | 2026-06 |
| CHOKEPOINTS/README.md | T2 | entry-index | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| CHOKEPOINTS/adda_settlement_service.md | T2 | chokepoint | handwritten | active | lowercase_snake |  | 5 | 2026-07 |
| CHOKEPOINTS/allocation_service.md | T2 | chokepoint | handwritten | active | lowercase_snake |  | 3 | 2026-06 |
| CHOKEPOINTS/cost_service.md | T2 | chokepoint | handwritten | active | lowercase_snake |  | 3 | 2026-06 |
| CHOKEPOINTS/ledger_and_payment.md | T2 | chokepoint | handwritten | active | lowercase_snake |  | 4 | 2026-06 |
| CHOKEPOINTS/pool_service.md | T2 | chokepoint | handwritten | active | lowercase_snake |  | 8 | 2026-07 |
| CHOKEPOINTS/worker_task_service.md | T2 | chokepoint | handwritten | active | lowercase_snake |  | 10 | 2026-07 |
| COVERAGE_REPORT.md ⟨COVERAGE_REPORT update mechanism → DOCDISC-F⟩ | T6 | machine-index | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |
| DATABASE_GUIDE/README.md | T6 | entry-index | handwritten | active | ALL_CAPS |  | 2 | 2026-06 |
| DATABASE_GUIDE/adda.md | T6 | database-guide | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| DATABASE_GUIDE/adda_settlement.md | T6 | database-guide | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| DATABASE_GUIDE/advance_profile.md | T6 | database-guide | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| DATABASE_GUIDE/barcode_batch.md | T6 | database-guide | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| DATABASE_GUIDE/cloth_roll.md | T6 | database-guide | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| DATABASE_GUIDE/stage_work_assignment.md | T6 | database-guide | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| DATABASE_GUIDE/worker_ledger_entry.md | T6 | database-guide | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| DATABASE_GUIDE/worker_stage_contribution.md | T6 | database-guide | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| DATABASE_GUIDE/worker_stage_task.md | T6 | database-guide | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| DATABASE_GUIDE/workflow_stage.md | T6 | database-guide | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| DATA_FLOWS/README.md | T6 | entry-index | handwritten | active | ALL_CAPS |  | 1 | 2026-07 |
| DATA_FLOWS/adda_settlement_flow.md | T6 | data-flow | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| DATA_FLOWS/advance_flow.md | T6 | data-flow | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| DATA_FLOWS/allocation_flow.md | T6 | data-flow | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| DATA_FLOWS/costing_flow.md | T6 | data-flow | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| DATA_FLOWS/fnf_business_flow.md | T6 | data-flow | handwritten | active | lowercase_snake |  | 6 | 2026-07 |
| DATA_FLOWS/material_flow.md | T6 | data-flow | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| DATA_FLOWS/payment_flow.md | T6 | data-flow | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| DATA_FLOWS/stage_earnings_flow.md | T6 | data-flow | handwritten | active | lowercase_snake |  | 7 | 2026-07 |
| DATA_FLOWS/worker_reporting_flow.md | T6 | data-flow | handwritten | active | lowercase_snake |  | 4 | 2026-07 |
| DJANGO_GUIDE/README.md ⟨academy layer⟩ | T6 | entry-index | handwritten | active | ALL_CAPS |  | 5 | 2026-06 |
| LIVING_DOCUMENTATION_SYSTEM/CHANGE_IMPACT_MATRIX.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 6 | 2026-06 |
| LIVING_DOCUMENTATION_SYSTEM/DRIFT_PREVENTION.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 2 | 2026-06 |
| LIVING_DOCUMENTATION_SYSTEM/FUTURE_AGENT_WORKFLOW.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| LIVING_DOCUMENTATION_SYSTEM/MAINTAINING_PKALS.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 4 | 2026-06 |
| LIVING_DOCUMENTATION_SYSTEM/OWNERSHIP_MATRIX.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 3 | 2026-06 |
| LIVING_DOCUMENTATION_SYSTEM/README.md ⟨academy layer⟩ | T6 | entry-index | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| PROJECT_ATLAS.md ⟨COVERAGE_REPORT update mechanism → DOCDISC-F⟩ | T6 | entry-index | handwritten | active | ALL_CAPS |  | 7 | 2026-07 |
| PROJECT_BRAIN/CHANGE_HISTORY_MAP.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 2 | 2026-06 |
| PROJECT_BRAIN/DEBUGGING_INDEX.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 2 | 2026-06 |
| PROJECT_BRAIN/DECISION_GRAPH.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 2 | 2026-06 |
| PROJECT_BRAIN/FEATURE_INDEX.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 4 | 2026-06 |
| PROJECT_BRAIN/README.md ⟨academy layer⟩ | T6 | entry-index | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| PROJECT_BRAIN/SEARCH_INDEX.md ⟨academy layer⟩ | T6 | topic-canonical | handwritten | active | ALL_CAPS |  | 3 | 2026-06 |
| README.md ⟨academy layer⟩ | T6 | entry-index | handwritten | active | ALL_CAPS |  | 2 | 2026-06 |
| REQUEST_JOURNEYS/README.md | T6 | entry-index | handwritten | active | ALL_CAPS |  | 2 | 2026-06 |
| REQUEST_JOURNEYS/adda_creation.md | T6 | request-journey | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| REQUEST_JOURNEYS/advance.md | T6 | request-journey | handwritten | active | lowercase_snake |  | 1 | 2026-06 |
| REQUEST_JOURNEYS/barcode_flow.md | T6 | request-journey | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| REQUEST_JOURNEYS/costing_flow.md | T6 | request-journey | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| REQUEST_JOURNEYS/login.md | T6 | request-journey | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| REQUEST_JOURNEYS/payment.md | T6 | request-journey | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| REQUEST_JOURNEYS/settlement_draft.md | T6 | request-journey | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| REQUEST_JOURNEYS/settlement_finalize.md | T6 | request-journey | handwritten | active | lowercase_snake |  | 4 | 2026-06 |
| REQUEST_JOURNEYS/settlement_reverse.md | T6 | request-journey | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| REQUEST_JOURNEYS/stage_completion.md | T6 | request-journey | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| REQUEST_JOURNEYS/worker_assignment.md | T6 | request-journey | handwritten | active | lowercase_snake |  | 2 | 2026-06 |
| REQUEST_JOURNEYS/worker_reporting.md | T6 | request-journey | handwritten | active | lowercase_snake |  | 3 | 2026-07 |
| URL_ATLAS.md ⟨interim route canonical (Standard §5)⟩ | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 5 | 2026-06 |

#### docs/PAGES (2 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| ACCESS_CONTROL.md | T2 | page-contract | handwritten | active | ALL_CAPS |  | 3 | 2026-06 |
| README.md | T2 | entry-index | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |

#### docs/adr (12 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| 0001-service-layer-owns-writes-no-signals.md | T1 | adr | frozen | frozen | NNNN-kebab |  | 1 | 2026-07 |
| 0002-single-writer-per-ledger-and-history-table.md | T1 | adr | frozen | frozen | NNNN-kebab |  | 1 | 2026-06 |
| 0003-three-concept-rbac-skill-gated-stages.md | T1 | adr | frozen | frozen | NNNN-kebab |  | 2 | 2026-06 |
| 0004-tracking-is-append-only-history-primitive.md | T1 | adr | frozen | frozen | NNNN-kebab |  | 1 | 2026-06 |
| 0005-production-truth-vs-financial-truth-option-b.md | T1 | adr | frozen | frozen | NNNN-kebab |  | 2 | 2026-07 |
| 0006-architect-for-scale-do-not-implement.md | T1 | adr | frozen | frozen | NNNN-kebab |  | 1 | 2026-06 |
| 0007-allocation-era-ledger-cutover.md | T1 | adr | frozen | frozen | NNNN-kebab |  | 11 | 2026-06 |
| 0008-commerce-manufacturing-boundary.md | T1 | adr | frozen | frozen | NNNN-kebab |  | 9 | 2026-06 |
| 0009-cost-truth.md | T1 | adr | frozen | frozen | NNNN-kebab |  | 3 | 2026-06 |
| 0010-growth-and-identity-policy.md | T1 | adr | frozen | frozen | NNNN-kebab |  | 3 | 2026-06 |
| 0011-monthly-salary-factory-level.md | T1 | adr | frozen | frozen | NNNN-kebab |  | 3 | 2026-07 |
| README.md ⟨ADR index⟩ | T1 | entry-index | handwritten | active | ALL_CAPS |  | 2 | 2026-07 |

#### docs/apps (11 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| README.md | T3 | entry-index | handwritten | active | ALL_CAPS |  | 1 | 2026-07 |
| accounts/GUIDE.md | T3 | app-guide | handwritten | active | ALL_CAPS |  | 2 | 2026-07 |
| core/GUIDE.md | T3 | app-guide | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |
| expense/GUIDE.md | T3 | app-guide | handwritten | active | ALL_CAPS |  | 5 | 2026-07 |
| inventory/GUIDE.md | T3 | app-guide | handwritten | active | ALL_CAPS |  | 4 | 2026-07 |
| machines/GUIDE.md | T3 | app-guide | handwritten | active | ALL_CAPS |  | 2 | 2026-07 |
| patterns_ai/GUIDE.md | T3 | app-guide | handwritten | active | ALL_CAPS |  | 35 | 2026-07 |
| production/GUIDE.md | T3 | app-guide | handwritten | active | ALL_CAPS |  | 29 | 2026-07 |
| raw_materials/GUIDE.md | T3 | app-guide | handwritten | active | ALL_CAPS |  | 1 | 2026-07 |
| storefront/GUIDE.md | T3 | app-guide | handwritten | active | ALL_CAPS |  | 1 | 2026-07 |
| tracking/GUIDE.md | T3 | app-guide | handwritten | active | ALL_CAPS |  | 1 | 2026-06 |

#### docs/archive (104 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| ARCHITECTURE.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 11 | 2026-06 |
| ARCHITECTURE_ROOT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 1 | 2026-06 |
| AUDIT_2026_05_29.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | dated |  | 19 | 2026-05 |
| FLOWS/README.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 2 | 2026-06 |
| PRE_REFACTOR_INVENTORY.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 5 | 2026-06 |
| QA/AUDIT_2026_06_02.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | dated |  | 5 | 2026-06 |
| QA/STAGE_A_REAUDIT_2026_06_02.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | dated |  | 7 | 2026-06 |
| QA/audit_log.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | lowercase_snake |  | 1 | 2026-06 |
| QA/bugs_found.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | lowercase_snake |  | 6 | 2026-06 |
| QA/fixes_applied.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | lowercase_snake |  | 12 | 2026-06 |
| README.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 2 | 2026-06 |
| audits/ARCH_AUDIT_FOUNDATION_2026_06_11.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | dated |  | 24 | 2026-06 |
| audits/ARCH_CHECKPOINT_2026_06_11.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | dated |  | 11 | 2026-06 |
| audits/ARCH_REASSESSMENT_POST_V2_2_2026_06_11.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | dated |  | 21 | 2026-06 |
| audits/DOC_AUDIT_2026_06_12.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | dated |  | 7 | 2026-06 |
| audits/FRONTEND_AUDIT_2026_06_12.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | dated |  | 11 | 2026-06 |
| audits/FRONTEND_CONSOLIDATION_REVIEW_2026_06_12.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | dated |  | 6 | 2026-06 |
| audits/OWNER_WORKFLOW_AUDIT_2026_06_11.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | dated |  | 12 | 2026-06 |
| audits/REMEDIATION_SCORECARD.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 5 | 2026-06 |
| patterns_ai_enterprise_era/01_RESEARCH.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | NN_TOPIC |  | 7 | 2026-07 |
| patterns_ai_enterprise_era/02_PROJECT_PLAN_DRAFT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | NN_TOPIC |  | 6 | 2026-07 |
| patterns_ai_enterprise_era/03_PLATFORM_BLUEPRINT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | NN_TOPIC |  | 28 | 2026-07 |
| patterns_ai_enterprise_era/04_KICKOFF_HOSTILE_REVIEW.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | NN_TOPIC |  | 13 | 2026-07 |
| patterns_ai_enterprise_era/05_BLUEPRINT_V2.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | NN_TOPIC |  | 23 | 2026-07 |
| patterns_ai_enterprise_era/06_BLUEPRINT_V3_FINAL.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | NN_TOPIC |  | 14 | 2026-07 |
| patterns_ai_enterprise_era/ADR-B-background-jobs.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | VIOLATION |  | 3 | 2026-07 |
| patterns_ai_enterprise_era/AI_PATTERN_INTELLIGENCE_KICKOFF.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 21 | 2026-07 |
| patterns_ai_enterprise_era/IMPLEMENTATION_MASTER_PLAN.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 18 | 2026-07 |
| patterns_ai_enterprise_era/IMPLEMENTATION_MASTER_PLAN_CERTIFICATION.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 4 | 2026-07 |
| patterns_ai_enterprise_era/IMPLEMENTATION_READINESS_CERTIFICATION.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 2 | 2026-07 |
| patterns_ai_enterprise_era/IMPLEMENTATION_READINESS_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 7 | 2026-07 |
| patterns_ai_enterprise_era/P0_IMPLEMENTATION_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 3 | 2026-07 |
| patterns_ai_enterprise_era/P1_BLOCK1_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 3 | 2026-07 |
| patterns_ai_enterprise_era/P1_BLOCK2A_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 4 | 2026-07 |
| patterns_ai_enterprise_era/P1_BLOCK2B_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 5 | 2026-07 |
| patterns_ai_enterprise_era/P1_BLOCK2C_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 5 | 2026-07 |
| patterns_ai_enterprise_era/P1_BLOCK3A_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 5 | 2026-07 |
| patterns_ai_enterprise_era/P1_BLOCK3B_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 4 | 2026-07 |
| patterns_ai_enterprise_era/P1_BLOCK3C_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 4 | 2026-07 |
| patterns_ai_enterprise_era/P1_BLOCK3D_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 4 | 2026-07 |
| patterns_ai_enterprise_era/P1_BLOCK3E_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 5 | 2026-07 |
| patterns_ai_enterprise_era/P1_ENGINEERING_REVIEW.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 7 | 2026-07 |
| patterns_ai_enterprise_era/P1_FINAL_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 11 | 2026-07 |
| patterns_ai_enterprise_era/P1_FREEZE_RECOMMENDATION.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 4 | 2026-07 |
| patterns_ai_enterprise_era/P1_REGRESSION_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 4 | 2026-07 |
| patterns_ai_enterprise_era/P2_COMPLETION_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 7 | 2026-07 |
| patterns_ai_enterprise_era/P2_DESIGN_RECEIPT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 5 | 2026-07 |
| patterns_ai_enterprise_era/P2_ENGINEERING_REVIEW.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 5 | 2026-07 |
| patterns_ai_enterprise_era/P2_READINESS_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 4 | 2026-07 |
| patterns_ai_enterprise_era/P2_REGRESSION_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 2 | 2026-07 |
| patterns_ai_enterprise_era/P3_COMPLETION_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 8 | 2026-07 |
| patterns_ai_enterprise_era/P3_ENGINEERING_REVIEW.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 4 | 2026-07 |
| patterns_ai_enterprise_era/P3_FREEZE_RECOMMENDATION.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 2 | 2026-07 |
| patterns_ai_enterprise_era/P3_REGRESSION_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 2 | 2026-07 |
| patterns_ai_enterprise_era/P4_COMPLETION_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 5 | 2026-07 |
| patterns_ai_enterprise_era/P4_DESIGN.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 8 | 2026-07 |
| patterns_ai_enterprise_era/P4_ENGINEERING_REVIEW.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 4 | 2026-07 |
| patterns_ai_enterprise_era/P4_FREEZE_RECOMMENDATION.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 2 | 2026-07 |
| patterns_ai_enterprise_era/P4_READINESS_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 2 | 2026-07 |
| patterns_ai_enterprise_era/P4_REGRESSION_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 2 | 2026-07 |
| patterns_ai_enterprise_era/P5_COMPLETION_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 6 | 2026-07 |
| patterns_ai_enterprise_era/P5_DESIGN.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 4 | 2026-07 |
| patterns_ai_enterprise_era/P5_ENGINEERING_REVIEW.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 5 | 2026-07 |
| patterns_ai_enterprise_era/P5_FREEZE_RECOMMENDATION.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 2 | 2026-07 |
| patterns_ai_enterprise_era/P5_READINESS_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 3 | 2026-07 |
| patterns_ai_enterprise_era/P5_REGRESSION_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 2 | 2026-07 |
| patterns_ai_enterprise_era/P5_ROLLOUT_GUIDE.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 3 | 2026-07 |
| patterns_ai_enterprise_era/PHASE_1_COMPLETION_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 2 | 2026-07 |
| patterns_ai_enterprise_era/PHASE_2_COMPLETION_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 1 | 2026-07 |
| patterns_ai_enterprise_era/PHASE_3_COMPLETION_REPORT.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 1 | 2026-07 |
| production/BARCODE_STAGE_PLAN.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 23 | 2026-05 |
| production/CHAT_LOG.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 8 | 2026-05 |
| production/CUTTING_DESIGN.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 29 | 2026-05 |
| production/CUTTING_REVIEW.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 16 | 2026-05 |
| production/DECISION_LOG.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 8 | 2026-06 |
| production/LAYERING_AUDIT_2026_06_02.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | dated |  | 15 | 2026-06 |
| production/PAYROLL_ARCHITECTURE.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 1 | 2026-06 |
| production/PAYROLL_GAP_ANALYSIS.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 10 | 2026-06 |
| production/SETTLEMENT_ARCHITECTURE.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 1 | 2026-06 |
| production/STAGE_COSTING_PLAN.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 1 | 2026-06 |
| production/TESTS_AND_RISKS.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 6 | 2026-06 |
| production/UI_PATTERNS.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 1 | 2026-06 |
| production/worker_workflow_review.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | lowercase_snake |  | 9 | 2026-06 |
| reviews/ERP_MASTER_CONTEXT_REVIEW.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 21 | 2026-06 |
| reviews/ERP_MASTER_CONTEXT_REVIEW_STATE.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 17 | 2026-06 |
| reviews/FINAL_PKALS_REVIEW.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 4 | 2026-06 |
| reviews/NEW_DEVELOPER_FIRST_7_DAYS.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 4 | 2026-06 |
| reviews/P2_SCHEMA_RENDER_VALIDATION.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 10 | 2026-06 |
| reviews/P4_2_BARCODE_DESIGN_REVIEW.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 10 | 2026-06 |
| reviews/PKALS_FINAL_AUDIT_2026_06_13.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | dated |  | 6 | 2026-06 |
| reviews/PKALS_FINAL_REVIEW.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 13 | 2026-06 |
| reviews/PKALS_FINAL_SCORECARD.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 6 | 2026-06 |
| reviews/PKALS_LONGEVITY_HARDENING.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 8 | 2026-06 |
| reviews/PKALS_REVIEW_FIXES.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 7 | 2026-06 |
| reviews/PKALS_REVIEW_V1.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 8 | 2026-06 |
| reviews/PKALS_SCORECARD.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 4 | 2026-06 |
| reviews/R0_RECONCILIATION.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 14 | 2026-06 |
| reviews/STAGE_DOMAIN_REVIEW_AGENDA.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 8 | 2026-06 |
| reviews/V2_1D_EXECUTION_REVIEW.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 11 | 2026-06 |
| reviews/V2_1_REVIEW.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 33 | 2026-06 |
| reviews/V2_2_EXECUTION_REVIEW.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 20 | 2026-06 |
| reviews/V2_3_EXECUTION_REVIEW.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 19 | 2026-06 |
| reviews/V2_FOUNDATION_REVIEW.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 12 | 2026-06 |
| reviews/WORK_LOG.md ⟨archive (family, DD-2)⟩ | T8 | archive-record | handwritten | archived | ALL_CAPS |  | 23 | 2026-06 |

#### docs/audit_phases (11 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| ARCH_EVAL_source_prevention_rates_variance.md | T2 | topic-canonical | handwritten | active | VIOLATION |  | 12 | 2026-06 |
| PHASE_A_core_manufacturing_flow.md | T2 | topic-canonical | handwritten | active | VIOLATION |  | 6 | 2026-06 |
| PHASE_B_costing_financial.md | T2 | topic-canonical | handwritten | active | VIOLATION |  | 11 | 2026-06 |
| PHASE_C_navigation_ux.md | T2 | topic-canonical | handwritten | active | VIOLATION |  | 5 | 2026-06 |
| PHASE_D_mobile.md | T2 | topic-canonical | handwritten | active | VIOLATION |  | 5 | 2026-06 |
| PHASE_E_docs_alignment.md | T2 | topic-canonical | handwritten | active | VIOLATION |  | 6 | 2026-06 |
| PHASE_F_assignment_ownership.md | T2 | topic-canonical | handwritten | active | VIOLATION |  | 6 | 2026-06 |
| PHASE_G_access_security.md | T2 | topic-canonical | handwritten | active | VIOLATION |  | 7 | 2026-06 |
| PHASE_H_reporting_operational_visibility.md | T2 | topic-canonical | handwritten | active | VIOLATION |  | 10 | 2026-06 |
| PHASE_I_edge_cases_integrity.md | T2 | topic-canonical | handwritten | active | VIOLATION |  | 10 | 2026-06 |
| POLICY_DECISIONS_B1_A5_B3.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 7 | 2026-06 |

#### docs/campaign_contracts (23 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| CAMPAIGN_APPROVAL_REPORT.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | ALL_CAPS |  | 7 | 2026-07 |
| PHASE_00_SAFETY_SNAPSHOT.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 35 | 2026-07 |
| PHASE_02_OWNER_VISIBILITY.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 16 | 2026-07 |
| PHASE_03_OFFICE_SUPPORT_CERTIFICATION.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 33 | 2026-07 |
| PHASE_04_CONFIRMED_FINDINGS.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 29 | 2026-07 |
| PHASE_05_DOCUMENTATION_FOUNDATION.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 63 | 2026-07 |
| PHASE_06_DOCUMENTATION_DISCOVERY.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 27 | 2026-07 |
| PHASE_07_DOCUMENTATION_CLEANUP.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 28 | 2026-07 |
| PHASE_08_KNOWLEDGE_GRAPH.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 26 | 2026-07 |
| PHASE_09_DOCUMENTATION_GENERATION.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 29 | 2026-07 |
| PHASE_10_UI_COMPONENT_LIBRARY.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 29 | 2026-07 |
| PHASE_11_DEVELOPMENT_DATASET_ARCHITECTURE.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 27 | 2026-07 |
| PHASE_12_SEEDER_ENGINE.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 27 | 2026-07 |
| PHASE_13_VERIFICATION_ENGINE.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 26 | 2026-07 |
| PHASE_14_KNOWLEDGE_SYNC.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 26 | 2026-07 |
| PHASE_15_BUSINESS_OPERATING_DASHBOARD.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 29 | 2026-07 |
| PHASE_16_MONTHLY_EXPENSE_ENGINE.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 28 | 2026-07 |
| PHASE_17_RAW_MATERIAL_EXPENSE_COST_INTEGRATION.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 29 | 2026-07 |
| PHASE_18_FUTURE_FEATURE_DOCUMENTATION_UPDATES.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 26 | 2026-07 |
| PHASE_19_DEPLOYMENT_DOCUMENTATION.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 20 | 2026-07 |
| PHASE_20_PRODUCTION_DEPLOYMENT.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 18 | 2026-07 |
| PHASE_21_DEPLOYMENT_READINESS_CERTIFICATE.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | PHASE_NN_SLUG |  | 17 | 2026-07 |
| README.md ⟨designated fill sections only⟩ | T5 | campaign-contract | frozen | frozen | ALL_CAPS |  | 24 | 2026-07 |

#### docs/pkals_v2 (5 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| PKALS_V2_ADR_PROPOSALS.md ⟨proposal pack, binds nothing (Standard §7); disposition = seeded B.3-8⟩ | T5 | topic-canonical | handwritten | superseded? | ALL_CAPS |  | 4 | 2026-06 |
| PKALS_V2_ARCHITECTURE.md ⟨proposal pack, binds nothing (Standard §7); disposition = seeded B.3-8⟩ | T5 | topic-canonical | handwritten | superseded? | ALL_CAPS |  | 7 | 2026-06 |
| PKALS_V2_EFFORT_ESTIMATE.md ⟨proposal pack, binds nothing (Standard §7); disposition = seeded B.3-8⟩ | T5 | topic-canonical | handwritten | superseded? | ALL_CAPS |  | 4 | 2026-06 |
| PKALS_V2_REQUIREMENTS.md ⟨proposal pack, binds nothing (Standard §7); disposition = seeded B.3-8⟩ | T5 | topic-canonical | handwritten | superseded? | ALL_CAPS |  | 5 | 2026-06 |
| PKALS_V2_ROADMAP.md ⟨proposal pack, binds nothing (Standard §7); disposition = seeded B.3-8⟩ | T5 | topic-canonical | handwritten | superseded? | ALL_CAPS |  | 4 | 2026-06 |

#### docs/production (10 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| BARCODE_GENERATION.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 6 | 2026-06 |
| CUTTING_PATTERN.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 7 | 2026-07 |
| LAYERING_STAGE.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 14 | 2026-07 |
| MIGRATIONS.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 6 | 2026-06 |
| OVERVIEW.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 13 | 2026-07 |
| PRODUCTION_APP.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 9 | 2026-05 |
| RAW_MATERIALS.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 8 | 2026-05 |
| RBAC.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 9 | 2026-07 |
| STAGE_FLOW.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 12 | 2026-06 |
| TRACKING.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 7 | 2026-05 |

#### docs/tracking (1 files)

| File | Tier | Type | Owner | Status | Naming | FM | KB | Mod |
|---|---|---|---|---|---|---|---|---|
| EXPORTS.md | T2 | topic-canonical | handwritten | active | ALL_CAPS |  | 8 | 2026-07 |

### Metadata presence census (per the R2-ratified adoption rule — Standard §13)

Frontmatter carriers: **2/540** — `docs/DOC_STANDARDS.md` + this report (both born after the
Phase-5 rule took effect; both valid 7-field blocks). Everything else pre-dates the rule →
**work-queue retrofit rows, NOT violations** (Wrong-metadata class applies only where the
adoption rule already binds). Retrofit-scope arithmetic: 540 − 104 archive (NEVER
retrofitted, R2) − 2 carriers = **434 retrofit rows for Phase 7** (432 md + 2 json — the
jsons take the seven as top-level keys per §13; the stray `.partial.json`'s retrofit is moot
if Phase 7 disposes of it, see F-A-05).

### DOCDISC-A findings register (first findings; classes per contract §6.1)

| # | Class | File(s) | Evidence | Standard clause | Proposed Phase-7 action | Risk |
|---|---|---|---|---|---|---|
| F-A-01 | KOS violation (naming) | `docs/AI_PATTERN_INTELLIGENCE/ADR/ADR-{A,C,D,D2,D3,E,F,G,H}-*.md` (9 files, family-level per DD-2; archive sibling `ADR-B` noted, exempt) | `ADR-<letter>-kebab` matches none of the six codified styles (census VIOLATION rows) | §14 closed set | Owner-gated: rename family to a codified style (link-rewrite burden) OR admit the style via a DOC_STANDARDS §20 amendment | docs-only, owner-gated |
| F-A-02 | KOS violation (naming) | `docs/audit_phases/PHASE_{A..I}_*.md` + `ARCH_EVAL_source_prevention_rates_variance.md` (10 files) | mixed CAPS+lowercase stems match no codified style | §14 | Adjudicate WITH the family's archive-candidacy at DOCDISC-E (archived files exit the active naming surface; else owner-gated rename) | docs-only |
| F-A-03 | KOS violation (naming) | `docs/AI_PATTERN_INTELLIGENCE/M4.5_IMPLEMENTATION_PLAN.md`, `M4.5_REPORT.md` | dot inside stem | §14 | Owner-gated rename (`M4_5_*`) or family amendment with F-A-01 | docs-only |
| F-A-04 | KOS violation (naming) | `docs/PKALS_RELEASE_v1.md` | lowercase `v1` suffix breaks ALL_CAPS | §14 | Rename (`PKALS_RELEASE_V1.md`) or archive with its family (DOCDISC-E reconciles vs DOCUMENT_ARCHIVE_REVIEW) | docs-only |
| F-A-05 | KOS violation + unassignable type | `docs/FRONTEND_DESIGN_SYSTEM_INVENTORY.partial.json` | stray partial artifact (census row T?/`?`); pre-seeded B.3-9 | §14, §3 typology | Phase-7 disposition — REMOVE-LATER class (deletion stays owner-gated) or archive | docs-only, owner-gated |
| F-A-06 | Missing | `docs/WORKER_ROLE_CERTIFICATION.md` | Worker-cert meta-audit evidence exists ONLY in agent memory (framework README risk #2; PHASE_06 dated amendment = seed 5) | §1.7 nothing-binding-only-in-memory | Phase 7 appends an evidence section sourced from the certified verdict + recoverable memory detail; unrecoverable detail honestly marked | docs-only |

Naming-violation arithmetic: 9 + 10 + 2 + 1 + 1 = **23 active-tree** ✓ (+1 archive-side
`ADR-B`, exempt per §4 archive rules — recorded, not a finding).

### Fragmentation register — Single-Canonical-Home candidates (owner directive 2026-07-13; 4 mandatory fields; **adjudication = DOCDISC-B/E**, these are census-level candidates)

| # | Knowledge | Current locations | Recommended canonical | Why consolidation benefits | Owning phase |
|---|---|---|---|---|---|
| F-A-07 | Per-app file map | `docs/LEARNING_2_0/APPS/<app>/{APP_FLOW,FILE_MAP,REQUEST_MAP}.md` (27 files, 8 apps; machines+patterns_ai MISSING — B.2) **vs** `docs/apps/<app>/GUIDE.md` (10, the Standard-§4 canonical file map) | `docs/apps/<app>/GUIDE.md` (FILE_MAP dimension); APP_FLOW/REQUEST_MAP either fold into GUIDE header/flows or archive | Two independently-maintained file maps per app = guaranteed drift (B.2 already shows APPS lags 2 apps behind reality); GUIDE is the rule-12-maintained copy | 7 (consolidate/archive) after B adjudicates |
| F-A-08 | Design-system spec | `DESIGN_SYSTEM_{MASTERPLAN,SPEC,IMPLEMENTATION_ROADMAP}.md` · `FRONTEND_DESIGN_SYSTEM_{ARCHITECTURE,STATUS}.md` · `TOKEN_MIGRATION_SPEC.md` · `BUTTONS_/FORMS_{FOUNDATION_SPEC,MIGRATION_MATRIX}.md` · `UI_COMPONENTS_CATALOG.md` (docs/) **vs** `UI_COMPONENTS.md` (root, the CLAUDE.md-rule-9 canonical) | `UI_COMPONENTS.md` for the living vocabulary; executed specs/matrices → receipts/archive | ≥10 active T2 docs answer "what is the design system" — one is canonical by standing rule, the rest are un-bannered era documents; Phase 10 (UI library) also needs ONE owner | 7 (banners/archive; content merges owner-gated); Phase 10 consumes the survivor |
| F-A-09 | Current roadmap / project state | `IMPLEMENTATION_ROADMAP_PDD_V1.md` (superseded-for-current-state per its own header) · `MANUFACTURING_V1_FREEZE.md` (declared winner) · `FOUNDATION_STATUS_SUMMARY_2026_06_14.md` · AI_AGENT_GUIDE "roadmap" manifest row → `ROADMAP_REVIEW_POST_C1_2026_06_11.md` (B.3-2) | `MANUFACTURING_V1_FREEZE.md` (current state, T1), roadmap doc banner-pointed to it | Four routes to "what is the plan/state" give three different answers — a resumability failure for a fresh session | 7 (manifest re-point = DOCCLEAN-E battery-bearing; banners docs-only) |
| F-A-10 | Deployment procedure | `deploy/README.md` (owner-approved runbook) · `DEPLOYMENT_PACKAGE_2026_06_14.md` · `ENFORCEMENT_ROLLOUT_RUNBOOK_2026_06_14.md` · PHASE_19/20 contracts (campaign wrappers; procedure deliberately not duplicated there) | `deploy/README.md` (PHASE_19 already mandates the ONE runbook) | Procedure duplicated across eras diverges exactly when it matters (deploy day); campaign already ruled procedures-live-in-ONE-place | **19** (runbook refresh); banners possibly 7 |
| F-A-11 | Implementation master plan | `IMPLEMENTATION_MASTER_PLAN.md` **and** `IMPLEMENTATION_MASTER_PLAN_V2.md` both active/T2, no supersession banner on V1 | `IMPLEMENTATION_MASTER_PLAN_V2.md` (V1 banner-superseded) — unless E finds both superseded by the freeze | V1/V2 pair without banner = Stale-class candidate (superseded-in-fact, DD-3) + duplicate answer surface | 7 (banner; archive V1) after E reconciles vs DOCUMENT_ARCHIVE_REVIEW |

### DOCDISC-A completeness + scope discipline

- **Arithmetic:** census rows **540** = mechanical boundary count 540 (= DOCDISC-0 baseline
  539 + this report, explained above). Every row carries tier + type + ownership + lifecycle
  + naming + FM + KB + month; exactly 1 row (`.partial.json`) carries the explicit
  `unassignable → typed finding` disposition (F-A-05).
- **Seeds advanced:** seed 5 → F-A-06 (confirmed-into-register). Seeds 1a/1b touched where
  census-visible (B.3-9 → F-A-05 confirmed · B.2 APPS-lag evidenced in F-A-07); full
  disposition at owning sub-phases B–F per the seeded-inputs table.
- **Zero corpus mutations:** census script read-only from scratchpad; the census-table
  assembly into THIS report (the §9-allowlisted write target) used a scratchpad insert
  script writing ONLY to this file, after every row was main-thread reviewed — disclosed;
  no other file touched. canonical_manifest.json read-only. Battery not run (never this
  phase).
- **Writes this sub-phase:** this report section · PHASE_06 Appendix A (DD answers,
  designated fill) · status file · memory. §9 exactly.

_Section closed 2026-07-13. Corrections, if ever needed, land as dated amendments._

## 1B. Canonical hierarchy verification (DOCDISC-B, 2026-07-13) ✅

> Executed under **owner clarification #2** (recorded as a PHASE_06 Appendix A dated
> amendment): every canonical-topic candidate is assessed BOTH for correct-canonical status
> AND for **future-navigation-hub capability** across the 22 owner-listed dimensions,
> condensed into six groups — **G1** business (purpose·workflow·rules·roadmap) ·
> **G2** ownership (feature·app) · **G3** code surface (URLs·views·templates·APIs·services·
> models·tables) · **G4** control surface (state machines·permissions·signals·background
> jobs) · **G5** decisions+docs (ADRs·implementation·learning·related features) ·
> **G6** verification (tests·certification evidence). Hub verdicts: **HUB-READY** (structure
> already connects most groups) · **HUB-CAPABLE** (right home; grows the missing groups via
> Phase-9 KOS:GEN sections) · **HUB-UNSUITED** (structurally cannot take the role → finding;
> the hub lands on the future Phase-9 feature doc/cards that CITE it). Discovery only —
> nothing moved/rewritten.

### canonical_manifest.json reference audit (READ-ONLY — §10 honored, file untouched)

- **Resolution: 31/31 referenced paths resolve** (entry 5 + topic canonicals + also[];
  script + raw output in scratchpad, quoted counts). All 7 `chokepoint_services` +
  5 `never_modify.only_writer` paths exist. PkalsNavigationGuardTests premise intact.
- **Topic count: 17 — B.2's "17 topics" CONFIRMED** (a DOCDISC-A-session pre-script manual
  count of 16 was wrong; corrected here — mechanical count wins).
- **Version "2026-06-13" — stale-as-documented.** Coverage gaps (→ F-B-04): NO topic routes
  machines · patterns_ai · PDD/product truth · FACTORY_OPERATIONS_MASTER/operations ·
  MANUFACTURING_V1_FREEZE/current state · deployment · DOC_STANDARDS/doc rules · campaign
  resume. `hard_rules` block: consistent with CLAUDE.md/ADR-0001/0002/0009 — no conflict.

### Per-topic canonical trace (manifest 17 + DOCUMENTATION_INDEX/Standard-T2 set)

| Topic (route) | Routed canonical | Canonical verdict | Hub verdict (evidence: heads/lines/links·code·adr from mechanical profile) |
|---|---|---|---|
| worker assignment / production truth | ARCHITECTURE_V2.md | ✓ still governing (T1) | **HUB-UNSUITED** — frozen T1, link-poor (38h/576L, 6 links, 0 code, 0 adr) → F-B-07 |
| settlement / earnings | CHOKEPOINTS/adda_settlement_service.md | ✓ | **HUB-CAPABLE** — handwritten T2, already links code+ADR+flows (2 code, 2 adr, 4 flows); G3/G5 live, G1/G6 growable |
| two truths | ARCHITECTURE_EXPLAINED/06_why_two_truths.md | ✗ **wrong register** → F-B-02 | HUB-UNSUITED — 24-line T6 micro-lesson (Standard §6: learning routes to truth, never holds it) |
| eras / ledger credit timing | ARCHITECTURE_EXPLAINED/10_why_eras.md | ✗ **wrong register** → F-B-02 | HUB-UNSUITED — 22-line T6 lesson |
| ledger / payment | CHOKEPOINTS/ledger_and_payment.md | ✓ | HUB-CAPABLE (7h/79L; G3 partial, link-poor — 1 link) |
| costing | adr/0009-cost-truth.md | ✓ mechanism truth | **HUB-UNSUITED by class** — ADR append-only, 0 links → F-B-07 |
| commerce boundary | adr/0008 | ✓ | HUB-UNSUITED by class → F-B-07 |
| tracking mode | REQUIREMENT_REVIEW_STAGE_TRACKING.md | ✓ (🔒 requirement) | HUB-UNSUITED by class (frozen, 0 links) → F-B-07 |
| request flow | PROJECT_KNOWLEDGE_MAP.md §2 | ✓ acceptable (T0 section routing onward; tier tension noted, no finding) | HUB-CAPABLE |
| a URL / route | URL_ATLAS.md | ✓ **interim canonical BY DESIGN** (Standard §5: cards replace it at Phase 9) | transfer-to-cards by design — no finding |
| request journey | REQUEST_JOURNEYS/README.md | ✓ home, but **9/12 journeys unwritten** (B.3-3 CONFIRMED at source) | HUB-CAPABLE once populated → Missing rows to §5-lane (D/F) |
| data model | LEARNING/02_DATABASE_RELATIONSHIPS.md | ✗ **wrong register** → F-B-01 | HUB-UNSUITED — T6 lesson as canonical for a G3-heavy topic |
| chokepoint services | PROJECT_KNOWLEDGE_MAP.md §7 | ✓ acceptable | HUB-CAPABLE; CHOKEPOINTS set itself lacks history_service page (B.3-4, → F mapping census) |
| an app's files | apps/README.md | ✓ (Standard §4) | HUB-CAPABLE — pure index (21L, 10 links); also[] routes to the F-A-07 duplicate (LEARNING_2_0/APPS/) → duplicate register |
| future-phase doc work | CHANGE_IMPACT_MATRIX.md | ✓ | HUB-CAPABLE (process hub; 16 flow-refs) |
| backlog / open items | PENDING_BACKLOG.md (+also ROADMAP_REVIEW_POST_C1) | ✗ **stale route** → F-B-03 (B.3-2 CONFIRMED) | n/a — status-anchor class; hub for "what's next" = status file + freeze |
| working rules | CLAUDE.md | ✓ (T0) | HUB-READY for rules dimension (49 links) |
| — T2 set: system design | SYSTEM_DESIGN.md | ✓ self-subordinating (pre-V2, "V2 wins") | HUB-CAPABLE (68h/905L/21 links; G3+G4 rich — 89 perm-mentions) |
| — glossary / vocabulary | GLOSSARY.md | ✓ | HUB-CAPABLE (terms + ER; G1 anchor) |
| — UI vocabulary | UI_COMPONENTS.md | ✓ (CLAUDE rule 9) — F-A-08 consolidation target | HUB-CAPABLE (31h/405L but 1 link — needs G5 links; Phase 10 consumer) |
| — production subsystem | production/OVERVIEW.md | ✓ | **HUB-READY pattern** (17h, 14 links, subsystem-scoped) |
| — permissions / roles | production/RBAC.md | ✓ (backlog #6 stale table seeded → stale register) | HUB-CAPABLE — G4 anchor (62 perm-mentions, 0 links out — needs G3/G5) |
| — operations / business workflow | FACTORY_OPERATIONS_MASTER.md | ✓ T1 living-body (Standard A1) | HUB-CAPABLE for G1 — best business-workflow shape (26h/508L), 1 link only → growable |
| — product truth | PRODUCT_DESIGN_DOCUMENT.md | ✓ T1 frozen | HUB-UNSUITED by class → hub = features layer citing PDD (F-B-07) |
| — current state | MANUFACTURING_V1_FREEZE.md | ✓ (F-A-09 recommended canonical) | HUB-CAPABLE (9 code-links, change-controlled updates sanctioned) |
| — app business view (exemplar) | config/expense/README.md | ✓ (T3) | **HUB-READY exemplar** — 18h/267L, 8 code + 4 adr links; the shape §4-Standard app READMEs should converge to |

### DOCDISC-B findings register

| # | Class | Subject | Evidence | Standard clause | Proposed action | Risk |
|---|---|---|---|---|---|---|
| F-B-01 | Wrong canonical source | manifest "data model" → `LEARNING/02_DATABASE_RELATIONSHIPS.md` | T6 lesson holding canonical role; profile 13h/161L teaching register | §6 (learning routes to truth, never holds it) | Phase-7 manifest re-route (DOCCLEAN-E, battery-bearing): interim → `LEARNING_2_0/DATABASE_GUIDE/README.md`; final = Phase-9 model cards | battery-bearing (manifest) |
| F-B-02 | Wrong canonical source | manifest "two truths" → `06_why_two_truths.md`; "eras" → `10_why_eras.md` | 22–24-line T6 micro-lessons as canonicals; ADR-0005/0007 are the truth homes (already in also[]) | §6, §2 conflict rules | Phase-7 manifest re-route: canonical ← ADR-0005 / ADR-0007, lessons demoted to also[] | battery-bearing (manifest) |
| F-B-03 | Wrong canonical source | manifest "backlog" → `PENDING_BACKLOG.md` + also `ROADMAP_REVIEW_POST_C1_2026_06_11.md` | B.3-2 CONFIRMED at source: campaign truth = `DEPLOYMENT_BACKLOG.md` + `DEPLOYMENT_CAMPAIGN_STATUS.md`; current-state = `MANUFACTURING_V1_FREEZE.md` (F-A-09) | §1.3, §2 T5-wins-state | Phase-7 manifest re-route + PENDING_BACKLOG disposition at E (stale/dup vs DEPLOYMENT_BACKLOG) | battery-bearing (manifest) |
| F-B-04 | Missing | canonical_manifest.json coverage | ZERO topics route: machines · patterns_ai · product truth (PDD) · operations (FOM) · current state (freeze) · deployment · doc rules (DOC_STANDARDS) · campaign resume — version "2026-06-13" predates all (B.2 CONFIRMED + extended by 5 topics) | §1.3, §6 AI-register | Phase-7 DOCCLEAN-E manifest refresh adds the 8 topics (single battery-bearing item, already queued by contract design) | battery-bearing |
| F-B-05 | KOS violation (prose-locked decision) | "7 permanent UI-architecture rules" | Decision home = dated receipt `FRONTEND_AUDIT_2026_07_05.md` (T7) + DOCUMENTATION_INDEX row; grep census shows no T1/T2 home; sibling rules sampled DO have homes (Design-System-FROZEN → MANUFACTURING_V1_FREEZE ✓ · no-native-dropdown → UI_COMPONENTS ✓ · stage-duration-auto → PDD ✓) | §1.7, §7 (decisions route to ADR/truth-lock, never live in receipts) | Phase-7: materialize the 7 rules into `UI_COMPONENTS.md` (or a new ADR, owner choice); receipt stays as evidence | docs-only, owner-gated |
| F-B-06 | Duplicate | `PENDING_BACKLOG.md` vs `DEPLOYMENT_BACKLOG.md` | Two active "open items" registers; PENDING = V2-3-era (98L, references superseded roadmap review), DEPLOYMENT = campaign-certified | §1.3 | E reconciles (likely: PENDING → banner-superseded or scope-split statement); rows → §4 register | docs-only |
| F-B-07 | KOS violation (hub-unsuited canonical — owner clarification #2 + §1.3 end-state) | Family: ALL frozen-class canonicals (ARCHITECTURE_V2 · ADR-0009 · ADR-0008 · REQUIREMENT_REVIEW_STAGE_TRACKING · PDD) | Append-only/frozen docs cannot host living navigation (hand-edits forbidden by their own class; profiles: 0–6 links, 0 code-links except AV2) | §11 frozen class, §16 fence rules, amendment #2 | **NOT a Phase-7 rewrite** — Phase-8 graph gives each a `cites` edge set; Phase-9 feature docs/cards BECOME the topic hubs and cite the locks; manifest topic rows eventually route to hubs (Phase 9 conversion, R5) | design input for 8/9 |
| F-B-08 | Wrong tier | `docs/audit_phases/` family (11 files) | Census heuristic classed T2/topic-canonical; content = closed 2026-06 audit receipts (spot-read: per-phase findings + verdicts, dated era) | §2 T7 definition | Re-class T7/receipt at Phase-7 metadata retrofit; archive-candidacy at E (with F-A-02 naming) | docs-only |

Census-imprecision adjudications (from §1's disclosed list): #1 `docs/README.md` → type
`entry-index` CONFIRMED (work-queue metadata row, not a violation) · #3 audit_phases →
F-B-08 · #5 CHOKEPOINTS-at-T2 CONFIRMED correct per Standard §2 · #2/#4/#6 stay with their
owning sub-phases (C/E).

**Fragmentation candidates adjudicated (Single-Canonical-Home):** F-A-07 CONFIRMED duplicate
(LEARNING_2_0/APPS = second file-map surface; manifest also[] even routes to it) → §4
register · F-A-08 CONFIRMED (trace row: UI_COMPONENTS canonical; ≥10 satellites un-bannered)
→ §4 · F-A-09 CONFIRMED (F-B-03/F-B-04 same root) · F-A-10 stands for Phase 19 · F-A-11 →
E per-file reconciliation.

**T1 content-conflict check (stop §16.5):** NONE triggered — every T1 lock consulted reads
consistently with the Standard as amended (A1/A2 disposed the known tensions at DOC-2).

**Scope discipline:** reads + scratchpad scripts only; manifest UNTOUCHED (read-only audit);
writes = this section + §4 rows below + PHASE_06 dated amendment (designated) + status +
memory. Zero corpus mutations. Battery never (no code).

_Section closed 2026-07-13._

## 2. Ownership + metadata audit (DOCDISC-C, 2026-07-13) ✅

> Executed under **owner clarification #3** (PHASE_06 dated amendment): ownership evaluated
> at **knowledge-DOMAIN grain**, not only document grain — per domain, is there ONE
> clearly-defined knowledge owner capable of becoming the domain's navigation hub across the
> 29 owner-listed aspects? Fragmented domain ownership = finding with 5 mandatory fields.
> Truth-lock hierarchy unchanged; discovery only.

### 2.1 OWNERSHIP_MATRIX verification (matrix-diff)

Matrix state: **24 table rows, concept/family grain**, "owner = update trigger" philosophy,
vintage ≈ 2026-06-13 (references ADR-0001..0010, PENDING_BACKLOG/ROADMAP era). Standard §11
keeps it **extended-not-replaced** at Phase 7 — the matrix's trigger dimension is
complementary to the Standard's 5-class `owner:` field, not in conflict. Verified rows: the
23 concept rows still describe their families correctly (ADR append-only trigger ✓ ·
config/README + apps/GUIDE split ✓ matches Standard §4 · CHOKEPOINTS/JOURNEYS/FLOWS/
DATABASE_GUIDE triggers ✓). The matrix itself CORROBORATES duplicate D-01: it carries BOTH a
`docs/apps/<app>/GUIDE` row and a `LEARNING_2_0/APPS/<app>/*` row with the same trigger —
two maintained file-map surfaces by its own admission.

**Gap census (mechanical proxy: boundary docs/ files with mtime ≥ 2026-06-14 = 339,
family-grouped; proxy disclosed — mtime ≠ born-date for edited older files):** families with
ZERO matrix coverage: **campaign corpus (23 contracts + status/backlog/ledger/certifications
+ this report) · AI_PATTERN_INTELLIGENCE (104) · PDD · FACTORY_OPERATIONS_MASTER ·
MANUFACTURING_V1_FREEZE · ADR-0011 (row says "0001..0010") · machines + patterns_ai app docs
· deploy/README · audit_phases · DOC_STANDARDS + KOS artifacts · design-system satellite
family**. → F-C-01.

### 2.2 Ownership-class verification (census `owner:` column adjudications)

| Adjudication | Verdict |
|---|---|
| Census imprecision #2 — AI_PATTERN receipts classed `handwritten` | **CORRECTED to `append-only`** at family grain (Standard §12: receipts/evidence born append-only). 61 T7 rows in that family carry the correction as a retrofit-queue annotation — census table itself left untouched (append-only section; correction recorded HERE) → F-C-02 |
| Census imprecision #6 — campaign contracts `frozen` | **CONFIRMED `frozen`** with the framework-defined designated-fill exception (Design Record/evidence sections); exception is the contracts' own documented mechanism, not a class violation |
| audit_phases family (F-B-08 tier T2→T7) | owner class follows: `handwritten` → `append-only` at retrofit (closed receipts) — folded into F-C-02 |
| T1 living-body locks (FOM; ARCHITECTURE_V2 rolling header) | class at retrofit per Standard §11 as amended by **A1**: `owner:` records the ACTUAL sanctioned change model — FOM = owner-ruled in-body updates; no violation |

### 2.3 Post-close edit check (append-only/frozen classes — report-only)

Honest limitation disclosed: the July corpus is uncommitted (U2 no-commit regime) → no git
baseline to byte-diff against; check = mtime sample + sanction trace. Sample (8 docs):
PDD 07-05 (amendments register + §15/§16 amendment — sanctioned) · ARCHITECTURE_V2 06-14
(S-era updates, pre-freeze — sanctioned) · REQUIREMENT_REVIEW 06-11 (untouched since lock ✓)
· FOM 07-06 (v3 owner-ruled — sanctioned per its own header) · MANUFACTURING_V1_FREEZE 07-11
(checklist/annex fills — its documented mechanism) · ADR-0011 07-05 (creation date ✓) ·
WORKER_ROLE_CERTIFICATION 07-12 (S2/S3/campaign appends — sanctioned) ·
CONFIRMED_FINDINGS_LEDGER 07-13 (append-only by design ✓). **Verdict: zero UNSANCTIONED
post-close edits detected in the sample; byte-level certainty deferred to post-Phase-22 git
history.**

### 2.4 Metadata register — R2 retrofit derivability (the Phase-7 DOCCLEAN-B input)

Queue: **434 files** (arithmetic in §1). Per-field derivability of the 7-field core:

| Field | Derivability | Method |
|---|---|---|
| `id` | MECHANICAL 434/434 | kebab of filename (uniqueness check vs full corpus) |
| `type` | MECHANICAL ~95% | census column, with the adjudicated exception lists (audit_phases→receipt · docs/README→entry-index · F-A-05 unassignable) |
| `owner` | MECHANICAL default + family exceptions | census column + F-C-02 corrections + A1 rule for T1 living-body |
| `status` | JUDGMENT for ~30 rows, mechanical `active` rest | supersession pairs (F-A-09/11, pkals_v2, PENDING_BACKLOG) need lifecycle rulings at E; archive excluded (never retrofitted) |
| `scope` | JUDGMENT (grep-assisted) | app/feature tags from path + content mentions |
| `anchors` | JUDGMENT (grep-assisted) | `config/` path mentions — chokepoints/GUIDEs near-mechanical, topic docs need selection |
| `verified` | JUDGMENT | no verified-against-code history exists; retrofit stamps the date of an actual verification read, never a fabricated past date |

Strategy handed to Phase 7 (per its contract): batch-script proposes, per-file diff review;
2 fields fully mechanical, 2 mechanical-with-exceptions, 3 judgment.

### 2.5 Knowledge-domain ownership register (clarification #3 — 13 domains assessed)

Domain list derivation (disclosed): the 8 domain apps + core + 4 cross-app knowledge domains
(costing · access-control · deployment/ops · the documentation system itself). Assessment =
current locations from census/§1B + hub shape from §1B profiles, against the 29 aspects
(grouped as §1B G1–G6 + vocabulary/journeys/forms/calculations/integrations/operational
guidance — same 6-group condensation, disclosed).

**Domains with a clear current-or-designated future owner (no finding):** production
execution (production/OVERVIEW — HUB-READY pattern) · settlement/earnings (expense README
HUB-READY + chokepoint hierarchy defined) · workers/payroll (expense README) · access
control (production/RBAC.md; #6 stale table already queued) · machines (machines README —
thin but sole + coherent) · storefront/commerce (README + ADR-0008/0010 boundary) ·
deployment (deploy/README, Phase 19 owns) · documentation system (DOC_STANDARDS) · core
(infra, README suffices).

**Fragmented / weak-owner domains → findings (5 mandatory fields each):**

| # | Class | Domain | Current ownership locations | Recommended future canonical owner | Why fragmentation hurts navigation | Resolving phase |
|---|---|---|---|---|---|---|
| F-C-01 | Wrong ownership (matrix rows absent) | (cross-domain) | OWNERSHIP_MATRIX 24 rows vs 339 post-vintage files: campaign corpus · AI_PATTERN tree · PDD · FOM · freeze · ADR-0011 · machines/patterns_ai · deploy · DOC_STANDARDS uncovered | Matrix EXTENDED (Standard §11) with family rows + `owner:`-class column reconciliation | An ownership matrix blind to ~⅔ of the active corpus cannot answer "who updates this when X changes" — the matrix's whole purpose | 7 (DOCCLEAN-B) |
| F-C-02 | Wrong ownership (class) | (family) | AI_PATTERN receipts (61) + audit_phases (11) censused `handwritten` | `append-only` per Standard §12 | Receipts editable-in-place lose evidentiary value; class drives the §17 fence/edit validation | 7 (metadata retrofit) |
| F-C-03 | KOS violation (domain fragmentation — clarification #3 + Standard §1.3) | Raw materials (cloth rolls) | `config/raw_materials/README.md` (app view) **+** `docs/production/RAW_MATERIALS.md` (T2, mtime 2026-05 pre-V2 era) + rm sections in OVERVIEW | `config/raw_materials/README.md` (business) + Phase-9 feature doc for cross-app navigation; era T2 doc → staleness check at E | Two "raw materials" homes from different eras — a reader cannot know which is live truth (OWN-E certified the app; the 2026-05 doc predates it) | 6-E (staleness) → 7 (banner/re-point) → 9 (feature hub) |
| F-C-04 | KOS violation (domain fragmentation) | Tracking / barcodes | `config/tracking/README.md` · `docs/production/TRACKING.md` · `docs/production/BARCODE_GENERATION.md` · `docs/tracking/EXPORTS.md` · 3× root `BARCODE_*_REVIEW/READINESS` docs · `REQUIREMENT_REVIEW_STAGE_TRACKING.md` (T1) | tracking README (app) + T1 lock for requirement truth; Phase-9 "barcode-traceability" feature doc as the hub citing all | 7 surfaces, no declared hierarchy among the 4 non-T1 topic docs; barcode is a future build area (TM-2) — fragmented entry = design-risk | 6-E → 7 (hierarchy statement/banners) → 9 (feature hub) |
| F-C-05 | KOS violation (domain fragmentation) | Patterns (patterns_ai) | `config/patterns_ai/README.md` **1.4KB thin** (pre-logged drift) vs `docs/apps/patterns_ai/GUIDE.md` 35KB vs `AI_PATTERN_INTELLIGENCE/` 104 files (43 active T2 incl. PLATFORM_STATUS + PRODUCT_VISION_V2 🔒 + PRODUCT_INTEGRATION_DESIGN) | App business view = README (needs Phase-7 drift fix, already pre-logged); domain hub = `PLATFORM_STATUS.md` or Phase-9 feature doc; vision truth stays PRODUCT_VISION_V2 | The largest doc family (104) has the THINNEST app README — domain entry inverted; a navigator lands on 1.4KB and misses 43 active docs | 7 (README drift fix — already queued) + 9 (feature hub) |
| F-C-06 | KOS violation (domain fragmentation) | Costing | ADR-0009 (frozen truth, hub-unsuited F-B-07) · `CHOKEPOINTS/cost_service.md` (service grain) · FOM (rates, ops grain) · expense README (settlement side) — **no living T2 topic home exists** | Phase-9 "costing" feature doc as hub citing ADR-0009 + all grains (interim: production/OVERVIEW costing section) | Money-adjacent domain where every surface is partial: readers assemble cost truth from 4 grains; ADR can't grow, chokepoint won't cover UI/reporting | 8 (graph models the grains) → 9 (feature hub) |
| F-C-07 | KOS violation (weak domain owner) | Inventory / product catalog | `config/inventory/README.md` 3.8KB for the UMBRELLA app (dashboard + RBAC hub + sidebar + products) + SYSTEM_DESIGN sections | inventory README strengthened at its next natural touch (Rule-12) or Phase-9 feature docs per sub-domain (products · dashboard · access-hub) | The app owning the most cross-cutting surfaces has a README that names none of them as domains — navigation dead-ends at the umbrella | 9 (feature docs; NO Phase-7 rewrite — content authoring ≠ cleanup, DC-D1) |

**Domain-grain hub note (clarification #3(d)):** every recommended future owner above is
subordinate to the T1 locks — hubs NAVIGATE, locks DECIDE (Standard §2 conflict rules
unchanged; F-B-07 disposition reaffirmed at domain grain).

### 2.6 Completeness + scope discipline

Seeds advanced: B.2 "3 drifted app READMEs" partially evidenced (patterns_ai → F-C-05;
production/accounts remain for D/E staleness passes). Matrix-diff = the §5 required
evidence table (2.1–2.2). Zero corpus mutations: OWNERSHIP_MATRIX read-only (its extension
is Phase-7 work); manifest untouched; no new canonicals created; nothing
moved/rewritten/consolidated. Writes = this section + PHASE_06 dated amendment (designated)
+ status + memory = §9 exactly. Battery never (no code).

_Section closed 2026-07-13._

## 3. Link + navigation audit (DOCDISC-D, 2026-07-13) ✅

> Executed under **owner clarification #4** (PHASE_06 dated amendment): contract audit PLUS
> four-persona navigation evaluation, bidirectional domain navigation, and hub-realism
> verification. Discovery only — **zero links repaired**.

### 3.1 Mechanical link audit (script `docdisc_d_links.py`, read-only; raw output preserved in scratchpad `linkaudit.json`)

Scope: active tree = boundary minus docs/archive = **436 files · 1,349 relative links
checked**. Disclosed limits: `#anchor` fragments not validated (file-level resolution only);
links inside fenced code blocks skipped (examples); directory links not traversed by the
orphan BFS (hand-verified below where it matters).

**Dead links: 63**, classified:

| # | Class | Family | Evidence | Proposed action | Risk |
|---|---|---|---|---|---|
| F-D-01 | Broken link (**HIGH — T0/T1 sources**) | Dead references to `AI_PATTERN_INTELLIGENCE_KICKOFF.md` + `AI_PATTERN_INTELLIGENCE/03_PLATFORM_BLUEPRINT.md` (both moved to `docs/archive/patterns_ai_enterprise_era/` at the patterns_ai cleanup — inbound rewrite was missed) | **CLAUDE.md:11** (T0) · **MANUFACTURING_V1_FREEZE.md:159/202/283** (T1!) · PROJECT_KNOWLEDGE_MAP.md:183 (T0) — hand-verified, targets exist in archive | Phase 7 inbound-rewrite to archive paths or supersessor; **freeze edits owner-gated** (T1 change control: owner ruling) | docs-only, owner-gated for the T1 file |
| F-D-02 | Broken link (LOW — closed receipts) | **~54 root-relative code links** (`config/…py#Lnn` written repo-root-relative from docs/ → resolve nowhere file-relative): audit_phases ×44 · PRODUCTION_TRUTH_FOUNDATION_REVIEW/ROADMAP ×8 · ERP_PRESTAGING ×4; plus ADR_PACK_CERTIFICATION ×4 archive-relative | script rows (full list in linkaudit.json) | Phase 7 batch decision: fix-relative OR accept-as-closed-receipt convention (owner choice; files are T7 closed + F-B-08 archive candidates) | docs-only |

**Active→archive links: 24 (F-D-09)** — Standard §15 permits archive citations only via
banners/index. Sampled classification: DOCUMENTATION_INDEX + DOC_STANDARDS + PROJECT_ATLAS
rows = legitimate index/reference pointers ✓; GLOSSARY/SYSTEM_DESIGN/root-README citations of
archived production docs = history-labeled but **cite-as-truth risk** → per-link
adjudication at DOCDISC-E with the archive sweep.

### 3.2 Routing-layer consistency (three layers + entry docs)

| Layer | Verdict | Evidence |
|---|---|---|
| PKALS (PROJECT_ATLAS vs LEARNING_2_0 subdirs) | ✓ CONSISTENT at directory level — all 11 subdirs indexed | per-subdir grep counts |
| AI_AGENT_GUIDE (README ↔ manifest ↔ canonicals) | ✗ **B.3-1 CONFIRMED**: CLAUDE.md + START_HERE + PROJECT_ATLAS still advertise "read-4-files"; the guide's actual method = "read ONE file to route" (line 3) → **F-D-05** (3 entry docs stale) · **B.3-9 CONFIRMED** (line 24 label `../ARCHITECTURE_V2.md` vs real path `../../` — link resolves, label misleads; folded into F-D-05) · manifest routing defects already registered (F-B-01..04) | greps quoted |
| PROJECT_BRAIN (5 indexes vs reality) | ✗ **F-D-08**: FEATURE_INDEX.md mtime 2026-06-13, ~zero machines/patterns_ai coverage — **the R3 features/-taxonomy seed is stale**; sibling indexes same vintage | grep + mtime |
| DOCUMENTATION_INDEX + START_HERE completeness | INDEX: current for campaign docs (rows added through this phase ✓) but 51 docs-root era files lack rows (→ orphan register) · START_HERE: routes 4 personas but **row B (owner) omits FOM + PDD entirely** (grep = 0) → F-D-06 | grep counts |

### 3.3 Four-persona navigation evaluation (clarification #4; 6-field findings)

| Persona | Chain walked | Verdict |
|---|---|---|
| New developer | START_HERE row A → PROJECT_KNOWLEDGE_MAP → LEARNING_PATH → app GUIDE | **WORKS** — chain current (PKM mod 2026-07); friction only where PKM's own dead link (F-D-01) sits |
| AI agent | START_HERE row C → AI_AGENT_GUIDE → manifest → canonical | **DEGRADED** — quantified: of the ~25 topics an agent needs, manifest covers 17, routes 3 to wrong-register docs (F-B-01/02) + 1 stale (F-B-03), misses 8 domains (F-B-04) → agent falls back to repo-scanning, the exact failure the manifest exists to prevent |
| Business owner | START_HERE row B → GLOSSARY → PKM §1–4 → LEARNING lessons | **INCOMPLETE** → **F-D-06**: affected path = owner entry; audience = owner; current chain ends at pre-freeze lessons; recommended future chain = row B gains FOM (operations truth) + PDD (product truth) hops, later the Phase-9 business hubs; cognitive load = owner must already KNOW FOM exists to find rates/journeys/rulings — the front door never mentions the two business truth-locks; owning phase = 7 (row edit) + 9 (hubs) |
| Experienced maintainer | CLAUDE.md → lazy-load docs + rules → DOCUMENTATION_INDEX | **MOSTLY WORKS** → **F-D-07**: CLAUDE.md header carries the dead KICKOFF link (F-D-01) and names the superseded enterprise-era "next project" (owner reset it 2026-07-07, Pattern Vision V2) — maintainer's first-read misroutes on current direction; recommended chain = CLAUDE.md header → freeze + V2 vision; load = trusted T0 file contradicts newer owner decision; owning phase = 7 |

### 3.4 Bidirectional domain navigation (Business ⇄ Implementation)

- **Business → Feature → Implementation:** works TODAY for the 9 clear-owner domains via
  PKM/FOM → app README → GUIDE → file (spot-walked: settlement · production · RBAC).
  BROKEN/foggy for the 5 fragmented domains (F-C-03..07) — no feature layer exists yet (T4
  empty by design until Phase 9), so the feature hop is improvised per-reader.
- **Implementation → Business:** works at APP grain (GUIDE headers cross-link business
  README per Standard §4 — spot-verified expense/production; **exception: patterns_ai GUIDE
  → 1.4KB README, F-C-05**). WEAK at ROUTE grain: URL→business requires URL_ATLAS (thin,
  76 lines) → by-design gap until Phase-9 cards (no new finding; Standard §5 interim
  already covers it).

### 3.5 Hub-realism verification (B/C future hubs vs truth-lock hierarchy)

Every DOCDISC-B/C-identified future hub (production/OVERVIEW · expense README · RBAC ·
FOM · UI_COMPONENTS · freeze · DATABASE_GUIDE · future Phase-9 feature docs) is: (a)
**index-reachable today** (none in the orphan register ✓), (b) **subordination-capable**
(each already cites upward; none competes with a T1 lock on truth), (c) blocked only by the
registered gaps — family indexes (F-D-04), fragmentation (F-C-03..07), manifest routing
(F-B-01..04). **Verdict: the hub model is realistic without any truth-lock hierarchy change;
truth-lock precedence unchanged.**

_Section closed 2026-07-13._

## 4. Duplicate register (DOCDISC-B/E) — BEGUN at B (2026-07-13); E consolidates + finalizes survivors

| # | Duplicated knowledge | Surfaces | Canonical survivor (proposed) | Source finding |
|---|---|---|---|---|
| D-01 | Per-app file map + flows | `LEARNING_2_0/APPS/<app>/*` (27) vs `docs/apps/<app>/GUIDE.md` (10) — manifest also[] routes to BOTH | `docs/apps/<app>/GUIDE.md` | F-A-07 (confirmed at B) |
| D-02 | Design-system spec | ≥10 docs/-root satellites vs `UI_COMPONENTS.md` | `UI_COMPONENTS.md` | F-A-08 (confirmed at B) |
| D-03 | Roadmap / current state | roadmap doc · freeze pkg · status summary · stale manifest route | `MANUFACTURING_V1_FREEZE.md` (state) | F-A-09 / F-B-03 |
| D-04 | Open-items register | `PENDING_BACKLOG.md` vs `DEPLOYMENT_BACKLOG.md` | E decides (likely DEPLOYMENT + scope-split banner) | F-B-06 |
| D-05 | Implementation master plan | `IMPLEMENTATION_MASTER_PLAN.md` vs `_V2.md` | `_V2` (or both → archive, E vs DOCUMENT_ARCHIVE_REVIEW) | F-A-11 |
| D-06 | Deployment procedure | deploy/README vs era receipts | `deploy/README.md` (Phase 19 owns) | F-A-10 |

_(register CLOSED at DOCDISC-E 2026-07-13: archive sweep added NO new duplicate pairs beyond D-01..06; D-04 re-classed SCOPE-SPLIT (both registers live, boundary statements at Phase 7); survivor + banner actions carry into the Phase-7 work queue at G with the §6.4 KOS-impact rows.)_

## 5. Orphan register (DOCDISC-D, 2026-07-13) ✅

BFS from the disclosed entry set (DOCUMENTATION_INDEX · START_HERE · CLAUDE.md ·
canonical_manifest paths) over 436 active-tree files → **reachable 249, raw orphans 187**.
Disclosed limitation: directory-links not traversed — hand-verified adjustments noted per
family. Standard §15: every active doc must be reachable from DOCUMENTATION_INDEX or a
parent index.

| Family | Count | Hand-verified nuance | Class + proposed action (Phase 7 unless noted) |
|---|---|---|---|
| docs/AI_PATTERN_INTELLIGENCE | 89 (79 + 10 ADR/) | **Root cause: the 104-file family has NO README/index at all** (verified absent); DOCUMENTATION_INDEX links only the 12-doc ACTIVE set → **F-D-04 (Missing: family index)** — creation venue = DC-D1 question for Phase 7 owner charter | Missing + orphan family |
| docs root (era docs) | 51 | design-system satellites (F-A-08) · foundation-era docs · HTML-audit family · misc receipts — no index rows | orphan rows; most co-resolve with §4/§6 dispositions (banner/archive) |
| LEARNING_2_0/APPS | 25 | reachable ONLY via the manifest's directory reference (`docs/LEARNING_2_0/APPS/`) — no file-level inbound; is duplicate D-01 anyway | resolves WITH D-01 consolidation |
| docs/audit_phases | 8 | **0 inbound links even from PRODUCTION_AUDIT_STATUS.md (its own campaign anchor) — verified by grep** | with F-A-02/F-B-08 archive-candidacy |
| LEARNING_2_0/REQUEST_JOURNEYS | 8 | **B.3-3 CONFIRMED mechanically**: written journey files unlinked because README rows 4–12 are unwritten/malformed | Phase 7 README row repair (Missing rows) |
| docs/pkals_v2 | 4 | no disposition anywhere (B.3-8) | DOCDISC-E disposition |
| config/patterns_ai/README.md | 1 | its own GUIDE does not link it (Standard §4 header cross-link missing) — **F-C-05 corroborated** | Phase 7 (with the pre-logged README drift fix) |
| docs/PAGES/ACCESS_CONTROL.md | 1 | exemplar contract unlinked from PAGES/README | Phase 7 index row |

_Register closed for D; E appends archive-side index gaps (12-rows-vs-104-files baseline)._

## 6. Duplicate / archive / lifecycle discovery (DOCDISC-E, 2026-07-13) ✅

> Executed under **owner clarification #5** (PHASE_06 dated amendment): every surviving
> finding gains a 10-field **KOS impact evaluation** + the exactly-one-owning-phase rule.
> Discovery only — nothing archived, no lifecycle changed, no banner written. Verdict-timing
> per the amendment: E delivers the complete findings reconciliation; the PHASE-final verdict
> stays at DOCDISC-G (after F), per the frozen contract.

### 6.1 DOCUMENT_ARCHIVE_REVIEW reconciliation (per-family; newer evidence wins; divergences listed — NO KEEP-family overruled → stop §16.8 untriggered)

| DAR family | Verdict | Notes |
|---|---|---|
| §1 KEEP set | **AGREE** with 3 annotations | (a) `PENDING_BACKLOG` KEEP stands but post-DAR evidence (DEPLOYMENT_BACKLOG born 07-12) turns D-04 into a **scope-split** (engineering-soak items vs campaign INFO), not supersession — Phase-7 boundary statements in both; (b) `IMPLEMENTATION_ROADMAP_PDD_V1` KEEP + F-A-09 banner-pointer are compatible (keep AND point); (c) **DAR erratum**: lists `CUTTING_DESIGN` under the KEEP production tree — it is ALREADY archived (`docs/archive/production/`, verified) |
| §1 KEEP "Design system reference pair" (DESIGN_SYSTEM_SPEC + UI_COMPONENTS_CATALOG) | **DIVERGENCE recorded** | census/CLAUDE.md rule 9 treat root `UI_COMPONENTS.md` as the LIVE vocabulary canonical (F-A-08/D-02); the DAR pair = frozen-system references. Roles differ (live vocabulary vs frozen spec) — Phase-7 hierarchy statement decides; catalog censused T7 receipt |
| §1 KEEP `PRODUCT_INTEGRATION_DESIGN` — wait, DAR lists it **§2 SUPERSEDED** (PI drafts row) | **DIVERGENCE recorded** | DOCUMENTATION_INDEX (newer, PDD-stream) cites it as the ACTIVE "integration ruling"; DAR groups it with killed enterprise-era drafts. Owner decides membership at Phase 7 — flagged, not resolved here |
| §2 SUPERSEDED — foundation chain (5) · master plans (7) · PI vision drafts (~16) · design-system working docs (~20) | **AGREE + EXTEND** | all sit in the ACTIVE tree with **zero supersession banners** → DD-3 superseded-in-fact-without-banner = **Stale class, family findings F-E-01/F-E-02**; corroborated by §5 orphan families. EXTEND: DAR's master-plans row already anticipates V2's own supersession (freeze + PLATFORM_STATUS) — aligns F-A-11/D-05 |
| §3 ARCHIVE — dated receipts/audits | **AGREE + EXTEND** | census/orphan data corroborates every family; **EXTEND: DAR omits `docs/audit_phases/` (11 files) and `docs/pkals_v2/` (5) entirely** — both now registered (F-A-02/F-B-08 → archive candidates; F-E-03 pkals_v2 disposition) |
| §4 REMOVE-LATER (3 candidate families) | **CARRIED VERBATIM** | deletion stays owner-gated, never a Phase-7 default (contract rule); rows enter the work queue as owner-gated class |
| §5 mechanics (`git mv`) | **SUPERSEDED by contract** | PHASE_07 already rules: plain `mv` NEVER `git mv` (U2); DAR mechanics otherwise consistent (tombstone banner + index row + same-session inbound rewrite) |

### 6.2 Archive-tree audit (contents READ-ONLY — indexed, never edited)

| Check | Measured | Verdict |
|---|---|---|
| Index completeness | **12 content rows vs 104 files** (README table counted) | B.3-5 CONFIRMED — 92 files unindexed → Phase-7 index rebuild |
| Banner presence | **37/102 carry an ARCHIVED-class banner in the first 6 lines** (102 = 104 − archive/README − FLOWS/README; method disclosed — baseline "42/104" used a looser anywhere-grep) | 65 bannerless → Phase-7 banner pass |
| B.3-5 dead pointer | archive/README routes live readers to root `ARCHITECTURE.md` — **does not exist** (verified); README's own row calls the archived copy "duplicate of the root" | CONFIRMED → Phase-7 |
| Cascade staleness (NEW) | index rows name successors that have SINCE been archived themselves (e.g. `PAYROLL_GAP_ANALYSIS` → "production/PAYROLL_ARCHITECTURE.md", now itself in archive) | **F-E-05** — Phase-7 index rebuild must re-resolve every successor pointer to its CURRENT home |

### 6.3 New findings (E)

| # | Class | Subject | Evidence | Proposed action | Risk |
|---|---|---|---|---|---|
| F-E-01 | Stale (superseded-in-fact, no banner — DD-3) | ROOT families: foundation chain (5) · master plans (7) · design-system working docs (~20) | DAR §2 names successors; files live un-bannered in active tree; orphan register corroborates | Phase-7: banner + archive per DAR families (owner approves batch) | docs-only |
| F-E-02 | Stale (same class) | AI_PATTERN PI vision drafts (~16, incl. the PRODUCT_INTEGRATION_DESIGN divergence flagged above) | DAR §2 row 3 ("owner reset killed the enterprise direction") | Phase-7 with the divergence ruled first | docs-only, owner-gated |
| F-E-03 | Archive candidate | `docs/pkals_v2/` (5 files, B.3-8: no disposition anywhere) | proposal pack, binds nothing (Standard §7); 2 MUSTs since built as skills; R7 superseded its generation stance | Phase-7: banner-supersede → archive (owner sign-off) | docs-only |
| F-E-04 | KOS violation (§15 archive-citation rule) | 15 of the 24 active→archive links cite archived docs as live context (GLOSSARY · SYSTEM_DESIGN · root README · REMEDIATION_PLAN · PROJECT_ATLAS/WORK_LOG) — remaining 9 = legitimate index/reference pointers (DOCUMENTATION_INDEX · DOC_STANDARDS · archive README refs) | link audit §3.1 rows, hand-classified | Phase-7: re-label as explicit history pointers or re-point to live successors | docs-only |
| F-E-05 | Broken link (archive index cascade) | archive/README successor pointers stale (see 6.2) | measured | Phase-7 index rebuild resolves successors to current homes | docs-only |

**Lifecycle proposals (NO state changed — Phase-7 owner-gated dispositions):**
pkals_v2 → `superseded` · IMPLEMENTATION_MASTER_PLAN (v1) → `superseded` (V2 successor; V2's own row per DAR) · PENDING_BACKLOG → stays `active` + scope-split statement · audit_phases family → `superseded/archived` with F-A-02 naming moot · raw-materials era doc (F-C-03) → staleness content-check at Phase-7 before banner.

### 6.4 KOS impact evaluation — ALL surviving findings (clarification #5; 10 fields: domain · future hub · nav/ownership/graph/card/AI/human impacts · priority · single owning phase)

Priorities: **P1** = blocks truth-routing or a later phase's input · **P2** = navigation quality · **P3** = hygiene/naming.

| Finding | Domain | Future hub | KOS impacts (nav · ownership · graph · feature-card · AI · human) | Pri | Owning phase |
|---|---|---|---|---|---|
| F-A-01 ADR-style naming (AI_PATTERN ×9) | patterns | PLATFORM_STATUS / P9 feature doc | closed naming set stays enforceable · clarifies these are NOT repo-ADRs (ownership) · graph `adr` node-kind stays unambiguous · cards cite real ADRs only · AI stops mis-matching `adr` pattern · humans stop confusing the two ADR families | P3 | 7 |
| F-A-02+F-B-08 audit_phases naming+tier | (cross) audit history | n/a (archive) | active tree shrinks · receipts reclassed append-only · graph excludes archived nodes cleanly · no cards needed · AI census noise −11 · humans stop landing in 2026-06 audits | P3 | 7 |
| F-A-03/04 naming (M4.5, PKALS_RELEASE_v1) | patterns / docs-system | family hubs | same closed-set benefits as F-A-01 | P3 | 7 |
| F-A-05 `.partial.json` stray | docs-system | DOC_STANDARDS | typology stays closed · zero unowned artifacts · graph doc-nodes all typed · — · AI parsers don't choke on partials · index stays clean | P3 | 7 |
| F-A-06 worker-cert evidence memory-only | workers/RBAC | WORKER_ROLE_CERTIFICATION | evidence navigable on-disk · append-only ownership honored · graph `documented_by` edge for the meta-audit exists · cert cards cite it · memory-less AI can verify the cert · humans see the full verdict | **P1** | 7 |
| F-A-07/D-01 APPS vs GUIDE dup | all apps | docs/apps/<app>/GUIDE | ONE file-map per app · single maintenance trigger (matrix row merges) · graph one `documented_by` source per file · app cards cite GUIDE only · AI file-map route unambiguous · humans stop cross-checking two maps | **P1** | 7 |
| F-A-08/D-02 design-system satellites | UI | UI_COMPONENTS.md | one UI vocabulary · frozen-family ownership clear · graph UI nodes cite one owner · Phase-10 library consumes ONE source · AI stops quoting superseded specs · humans find live tokens | P2 | 7 |
| F-A-09/D-03+F-B-03 roadmap/state routes | (cross) current state | MANUFACTURING_V1_FREEZE | "what is the plan" has one answer · state ownership = freeze+status · graph `supersedes` chain complete · — · AI resumes correctly · humans stop reading dead roadmaps | **P1** | 7 |
| F-A-10/D-06 deployment procedure | deployment | deploy/README | one runbook · Phase-19/20 own procedure · graph ops nodes cite runbook · — · AI deploys from one doc · humans too | P2 | **19** |
| F-A-11/D-05 master plans V1/V2 | (cross) planning history | freeze + PLATFORM_STATUS | supersession chain visible · — · `supersedes` edges acyclic+complete · — · AI ignores dead plans · humans see era boundaries | P3 | 7 |
| F-B-01/02 lesson-canonicals (manifest) | data-model / money-truth | DATABASE_GUIDE / ADR-0005+0007 | truth routed to truth-register docs · learning stays teaching-only · graph `routes_to` lands on right kinds · cards cite locks not lessons · **AI answers from truth not simplifications** · humans get depth-first | **P1** | 7 |
| F-B-04 manifest 8 missing topics | 8 domains | (their hubs) | machine routing covers all domains · — · graph⊇manifest proof possible (P8-E) · card topics complete · **AI stops repo-scanning** · — | **P1** | 7 |
| F-B-05 UI rules in receipt | UI | UI_COMPONENTS.md | binding rules live in a living doc · rules owner = vocabulary owner · graph rule-nodes cite canonical · P10 consumes · AI finds rules on the UI route · humans too | P2 | 7 |
| F-B-06/D-04 backlog pair | (cross) open work | status file + both backlogs | scope boundary explicit · each register owns its class · — · — · AI picks correct register · humans too | P2 | 7 |
| F-B-07 frozen canonicals ≠ hubs | 5 truth domains | **P9 feature docs/cards** | hubs navigate, locks decide (precedence intact) · lock ownership untouched · graph `cites` edges model it · **cards ARE the fix** · AI navigates hub→lock · humans same | **P1** | **9** (8 feeds it) |
| F-C-01 matrix gaps (~⅔ corpus) | docs-system | OWNERSHIP_MATRIX (extended) | update-triggers known for all families · THE ownership fix · graph `documented_by` maintainable · card ownership rows fillable · AI knows what to update on change · humans too | **P1** | 7 |
| F-C-02 receipt classes | patterns/audit | (family) | — · append-only classes honest · graph node class correct · — · AI edit-guards right docs · — | P3 | 7 |
| F-C-03 raw-materials era split | raw materials | rm README + P9 feature doc | one live rm truth · README owns domain · graph rm nodes single-source · rm card cites README · AI/human single entry | P2 | 7 |
| F-C-04 tracking/barcode ×7 surfaces | tracking | P9 "barcode-traceability" feature doc | pre-TM-2 design reads one hub · hierarchy declared · graph groups 7 sources · **card = the hub** · AI/human stop assembling 7 docs | P2 | **9** |
| F-C-05 patterns README inversion | patterns | README (fixed) + PLATFORM_STATUS | domain entry matches domain size · §4 dual-register restored · graph app-node has real README · patterns card cites it · AI/human land correctly | P2 | 7 |
| F-C-06 costing no living home | costing | **P9 "costing" feature doc** | money domain gets one navigable home · grains keep their owners · graph joins 4 grains · **card = the home** · AI assembles cost truth safely · humans too | **P1** | **9** |
| F-C-07 inventory umbrella weak | inventory | P9 sub-domain feature docs | umbrella decomposed · sub-owners named · graph features split app · cards per sub-domain · AI/human stop dead-ending | P2 | **9** |
| F-D-01 T0/T1 dead links | patterns/docs-system | (entry docs) | trusted entries stop 404ing · freeze edit via its own change control · graph link-integrity clean · — · **AI trusts T0/T1 blindly — must not 404** · humans same | **P1** | 7 |
| F-D-02 root-relative code links | audit history | n/a | receipts render correctly OR convention documented · — · graph anchors parse · — · low · low | P3 | 7 |
| F-D-03/04 orphan families + AI_PATTERN no-index | patterns + era docs | family README (DC-D1 venue) | §15 no-orphans restored · family gains an owner-index · graph reachability = index reachability · — · AI discovers family without ls · humans too | P2 | 7 |
| F-D-05 read-4-files stale ×3 | docs-system | AI_AGENT_GUIDE | entry instructions match reality · — · — · — · **AI follows correct protocol from first read** · humans stop miscounting | P2 | 7 |
| F-D-06 START_HERE row B gap | business entry | START_HERE → FOM/PDD | owner front door reaches business truth · — · — · — · — · **owner self-serves rates/rulings/journeys** | **P1** | 7 |
| F-D-07 CLAUDE.md stale header | docs-system | CLAUDE.md | maintainer entry current · — · — · — · every agent reads CLAUDE.md first — wrong direction propagates · humans same | **P1** | 7 |
| F-D-08 FEATURE_INDEX stale | features (R3 seed) | FEATURE_INDEX → features/ | **P8 taxonomy extraction gets a true seed** · feature ownership complete · graph `belongs_to_feature` complete · card set complete · AI feature-routes fully · humans too | **P1** | 7 (pre-8 gate) |
| F-D-09/F-E-04 archive citations | (cross) history | (per doc) | active tree cites truth, archive cited as history · — · graph never routes truth through T8 · — · AI doesn't quote archived truth · humans warned | P2 | 7 |
| F-E-01/02 unbannered superseded families | (cross) era docs | (successors) | DD-3 staleness eliminated at family scale · successor named per file · `supersedes` edges materialize · — · AI/human never read dead truth unlabeled | **P1** | 7 |
| F-E-03 pkals_v2 disposition | docs-system | DOC_STANDARDS lineage note | predecessor pack closed out · — · supersession edge to KOS v3 · — · AI stops weighing dead proposals · humans see lineage | P3 | 7 |
| F-E-05 archive index cascade | archive | archive/README (rebuilt) | index resolves to CURRENT homes · — · graph successor-pointers valid · — · AI/human archive lookups land | P2 | 7 |

### 6.5 One-owning-phase verification (clarification #5b)

Every surviving finding above carries exactly ONE owning phase: **Phase 7** ×30 finding-rows
(all cleanup-class) · **Phase 9** ×4 (F-B-07, F-C-04, F-C-06, F-C-07 — hub/feature-doc
creation; Phase 8 contributes graph input, never owns) · **Phase 19** ×1 (F-A-10 deployment
runbook). Zero unassigned; zero dual-owned; earlier phases listed only as contributors.
**No finding can become orphan work after Phase 6 closes** — DOCDISC-G's work queue will
carry each row with this owner.

### 6.6 Findings reconciliation (complete, all sub-phases)

| Register | Count | Classes |
|---|---|---|
| F-A-01..11 | 11 | 5 naming KOS-violations · 1 Missing (seed 5) · 5 fragmentation (SCH) |
| F-B-01..08 | 8 | 3 wrong-canonical · 1 Missing (manifest topics) · 2 KOS-violation (prose-locked rules · frozen-hub family) · 1 duplicate · 1 wrong-tier |
| F-C-01..07 | 7 | 2 wrong-ownership · 5 domain-fragmentation/weak-owner |
| F-D-01..09 | 9 | 2 broken-link families · 2 orphan/Missing · 3 navigation-persona · 1 stale-seed · 1 archive-citation |
| F-E-01..05 | 5 | 2 stale families · 1 archive-candidate · 1 §15-violation family · 1 archive-index cascade |
| **Total surviving** | **40** | duplicates D-01..06 fold into their F-rows |

Seeds disposed at E: seed 2 (DOCUMENT_ARCHIVE_REVIEW) = reconciled per-family above
(agree/extend/2 divergences/1 erratum; NO KEEP overruled) · B.3-5 CONFIRMED+extended
(F-E-05) · B.3-8 disposed (F-E-03). Remaining seed items (B.2 manifest staleness → F-B-04 ✓
done; B.3-6 apps-README blurbs + B.3-7 PAGES backlog → land in F's mapping census; seed 4
applied throughout). Full seed table finalizes at G per contract.

_Section closed 2026-07-13. E-scope verdict: discovery registers COMPLETE for
duplicate/archive/lifecycle lanes; DOCDISC-F (generation + graph readiness) then DOCDISC-G
(totals + work queue + PHASE-6 VERDICT) remain, per the frozen contract._

## 7. Generation-candidate register (DOCDISC-F, 2026-07-13) ✅

> Executed under **owner clarification #6** (PHASE_06 dated amendment): 8-field
> determination per candidate. Prose is NEVER machine-rewritten (R7); candidates below are
> STRUCTURAL content only. KOS:GEN boundaries sketched section-level — **no fence written,
> nothing generated.** Fields: source of truth · mechanical? · judgment? · one-time/
> repeatable · graph node / edge / card input · owning phase.

| # | Candidate (structural content) | Source of truth | Mech? | Judgment? | Cadence | Node/Edge/Card | Phase |
|---|---|---|---|---|---|---|---|
| GC-01 | URL_ATLAS route tables (~40 summary rows vs 528 live routes) | URLConf walk (MGT-H style) | YES | route grouping labels only | repeatable | url nodes · routes_to/gated_by edges · **cards replace the atlas per R4** | 9 |
| GC-02 | app GUIDE file-tables (per-directory rows, ★ markers) | filesystem + chokepoint register | YES (rows) | ★/role annotations stay hand | repeatable (hybrid fences) | doc↔file documented_by edges · card "services" section | 9 (owner-activated lane) |
| GC-03 | docs/apps/README.md app table (B.3-6 **CONFIRMED: machines "R10" + patterns_ai "P1 Block 1" blurbs stale** — rows exist, text era-frozen) | apps registry + GUIDE headers | YES (rows) | blurb wording | repeatable | app nodes | 9 (blurb repair itself = 7, stale row) |
| GC-04 | COVERAGE_REPORT.md (self-declares "dated snapshot, NOT auto-maintained, re-measure on demand"; drift guards = core.tests — inventory complete) | grep/ORM censuses | YES | none | repeatable | (validation input, not a node) | 14 (knowledge_sync report class) |
| GC-05 | canonical_manifest.json → **generated VIEW of the graph (R5 RATIFIED)** | graph | YES | topic match-terms curation | repeatable | routes_to edges | **9 GEN-D (the one battery-bearing item; CI-guard PkalsNavigationGuardTests retained; manifest hand-maintained + quarantined until then — Phase-7 refresh stays hand-edit under the guard)** |
| GC-06 | DOCUMENTATION_INDEX section tables | doc census/graph | YES (rows) | descriptions hand | repeatable (hybrid) | doc nodes | 9 (owner-activated) |
| GC-07 | FEATURE_INDEX → features/ tree (R3 seed; **F-D-08: seed stale, refresh = Phase-7 P1 row**) | graph feature nodes | YES | taxonomy curation at KG-0 | one-time extraction, then generated | **feature nodes + belongs_to_feature edges · THE card scaffold** | 8 (extract) → 9 (generate); owner = 8 |
| GC-08 | CHOKEPOINTS pages — writes/locks/gates tables | never_modify register + service code | partial | invariant prose stays hand | repeatable (hybrid) | writes/calls edges · card "single-writer" rows | 9 (owner-activated) |
| GC-09 | DATABASE_GUIDE per-model pages — field/FK tables | model introspection | YES (tables) | "one row means" prose stays hand | repeatable (hybrid) | model nodes · relationships | 9 (owner-activated) |
| GC-10 | OWNERSHIP_MATRIX rows | frontmatter `owner:` fields post-retrofit | YES (post-7) | trigger wording | repeatable (hybrid) | documented_by maintenance edges | 9/14 |
| GC-11 | archive/README index (12/104 + F-E-05 cascade) | archive scan + banners | YES | successor naming = judgment ONCE (Phase-7 rebuild), then mechanical | repeatable | supersedes edges | 7 rebuilds by hand; 9+ regenerates |
| GC-12 | docs/features/** + URL cards (do not exist — the Phase-9 TARGETS, born generated) | knowledge_graph.json only | YES | none (grain R4 ratified) | repeatable, byte-stable | **the card layer itself** | 9 |

## 8. Graph-readiness section (DOCDISC-F, 2026-07-13) ✅ — Phase-8's §2 facts, pre-built

### 8.1 Mapping-law coverage arithmetic (Standard §10 — counted, not asserted; grep-level methods disclosed)

| Law | Denominator (measured) | Current doc coverage (measured) | Gap verdict |
|---|---|---|---|
| URL → card/atlas row | **528 routes** (MGT-H certified census; grep path() = 493, excludes dynamic mounts — both quoted) | URL_ATLAS ≈ 40 summary rows (group grain, not per-route) | **~93% of routes have no per-route doc unit → the R4 one-card-per-row mandate is the fix; atlas grain ≠ card grain (KG-0 input: cards enumerate from URLConf walk, NOT from atlas rows)** |
| Model → README row + DATABASE_GUIDE | **~87 model classes** (grep models.Model/TimeStampedModel bases) | DATABASE_GUIDE 10 pages · README "one row means" tables cover majors per app | ~11% deep-doc coverage; graph model nodes must come from introspection, docs attach via documented_by where they exist |
| Service → GUIDE row + CHOKEPOINTS | **57 service modules**; manifest names 7 single-writers | CHOKEPOINTS 6 pages — **history_service page MISSING (B.3-4 CONFIRMED mechanically: 7 manifest writers vs 6 pages)** | 1 chokepoint gap = Phase-7 missing-doc row (DC-D1 venue); 50 non-chokepoint services = GUIDE-row grain only, sufficient for v1 |
| View → card/GUIDE + PAGES | **~238 class-based views** (grep) | PAGES = 1 exemplar contract (B.3-7 CONFIRMED); GUIDE rows cover files | PAGES backlog = owner-appetite question (Phase-7 charter row, NOT auto-queued); view nodes from code walk |

### 8.2 Knowledge-level node analysis (clarification #6 — five strata vs the ratified P8 v1 schema)

P8 v1 node kinds (KG ratification pending at KG-0): app · url · view · service · model ·
doc · feature · adr; 8 edge kinds. Strata mapping:

| Stratum | v1 representation | Gap (recorded as KG-0/GEN-0 INPUT — no architecture introduced here) |
|---|---|---|
| Documentation artifacts | `doc` nodes | none — census §1 = the node inventory |
| Knowledge domains | `feature` tree ROOTS (13-domain register §2.5 = the seed's top level) | **KG-0 input: decide domain = root-feature vs first-class `domain` kind** (additive minor either way) |
| Business capabilities | `feature` nodes (FEATURE_INDEX seed + R3) | seed refresh = F-D-08 (P1, Phase 7) |
| Technical capabilities | `url`/`view`/`service` nodes | none for v1 |
| Implementation artifacts | `model`/`service`/`view`/`url` + code paths as node attrs | templates · forms · signals · background jobs NOT v1 kinds — **acceptable: repo has no-signals rule (ADR-0001) + no job queue today; record as future additive minors** |

Knowledge kinds from the owner's list not first-class in v1 — all representable via `doc`
nodes + edges today, first-class = future additive minors: workflows/user journeys
(journey docs) · permissions (RBAC doc + gated_by edges cover the navigation need) · tables
(≈ model nodes; PG-level views/constraints via DATABASE_GUIDE docs) · calculations (ADR-0009
+ chokepoint docs) · integrations (none live; ADR-0008 fences) · certification evidence
(evidence-cert docs + cites edges). **Verdict: knowledge-level navigation is achievable in
v1 via feature/doc nodes; nothing blocks Phase 8; six enumerated additive-minor candidates
go to KG-0 as Design-Record input.**

### 8.3 R5 migration notes (manifest → graph view) + constraints for Phases 7/8

- Manifest stays **hand-maintained + CI-guarded** (PkalsNavigationGuardTests) until the
  Phase-9 GEN-D conversion (R5 ratified; PHASE_08 defers it there — Phase 8 proves
  graph⊇manifest READ-ONLY).
- **Phase-7 constraint:** the DOCCLEAN-E manifest refresh (F-B-01..04 re-routes + 8 new
  topics) happens BEFORE graph build → Phase 8 consumes the refreshed manifest for its
  coverage proof; every manifest-referenced path is move-frozen outside DOCCLEAN-E
  (quarantine, per PHASE_07).
- **Phase-8 constraint:** cards/features enumerate from code walks + registers (8.1), never
  from the thin atlas; FEATURE_INDEX refresh (Phase 7) is a HARD input to R3 extraction.
- Existing generated-ish artifacts inventoried: canonical_manifest.json (hand + CI guard) ·
  COVERAGE_REPORT.md (manual dated snapshot, self-declared) — no other machine-written doc
  exists; **fence adoption today = 0 (expected; fences arrive at Phase 9)**.

### 8.4 Scope discipline

Zero mutations (censuses read-only, grep/ls-level, methods + counts quoted); manifest/
matrix/archive untouched; nothing generated — no fence, no card, no graph. Writes = report
§7+§8 + PHASE_06 dated amendment + status + memory (§9 exactly). Battery never (no code).
Sub-agent use: none (mechanical scripts + main-thread judgment; U7 vacuous).

_Sections closed 2026-07-13. Remaining: DOCDISC-G — totals · completeness census · Phase-7
work queue · PHASE-6 VERDICT._

## 9. Classification totals + arithmetic reconciliation (DOCDISC-G, 2026-07-13) ✅

### 9.1 Corpus-mutation spot-check (contract §14 — PASS)

Boundary re-count at G: docs 520 md + 2 json + 7 root + 10 app READMEs + 1 deploy =
**540 = the DOCDISC-A baseline exactly** (zero drift; §16.6 clear). Mtime sample (10 censused
probes incl. manifest, matrix, FEATURE_INDEX, URL_ATLAS, pkals_v2, archive README, PDD,
deploy): **all timestamps pre-date Phase 6** — the census observed an unmutated corpus.
Phase-6 total write-set = report + PHASE_06 designated sections + status + memory, per §9,
every session.

### 9.2 Findings arithmetic (cross-footed)

**40 findings** = F-A 11 + F-B 8 + F-C 7 + F-D 9 + F-E 5. Dead links **63 = 6 (T0/T1
KICKOFF/blueprint family) + 53 (root-relative code links) + 4 (ADR_PACK archive-relative)**
— residual ∅ (F-D-01's precise count = 6 references, refined here from §3.1's five named
source-lines + the freeze→blueprint row). Naming violations 24 = 23 active (9+10+2+1+1) + 1
archive-exempt. Archive links 24 = 15 findings + 9 legitimate. Orphans 187 raw
(family-adjudicated §5). Duplicate register 6 families — fold-map: D-01=F-A-07 ·
D-02=F-A-08 · D-03=F-A-09/F-B-03 · D-04=F-B-06 (scope-split) · D-05=F-A-11 · D-06=F-A-10.
Frontmatter 2/540; retrofit 434 = 540 − 104 − 2. Generation candidates 12 (GC-01..12).
Matrix rows verified 24; gap families enumerated (F-C-01).

### 9.3 Per-register totals (the verdict numbers)

| Register | Total |
|---|---|
| Findings (all classes) | **40** |
| Phase-7 cleanup queue rows (§10) | **27** |
| Later-phase handoff rows (§10.2) | **9** (Phase 9 ×4 findings + GC lanes · Phase 8 ×1 · Phase 14 ×1 · Phase 19 ×1 + 2 register lanes) |
| Future graph items handed to Phase 8 | **10** = 6 additive-minor schema inputs + 4 mapping-law coverage censuses |
| Generation candidates | **12** |
| Metadata retrofit candidates | **434** |
| Duplicate families | **6** |
| Wrong-canonical findings | **3** (F-B-01 · F-B-02 [2 manifest rows] · F-B-03) |
| Ownership findings | **7** (F-C-01..07) |
| Navigation findings | **9** (F-D-01..09) |
| Graph-readiness findings/facts | **10** (as defined above) |
| Owner clarifications recorded + applied | **6** (#1 SCH · #2 hub · #3 domain ownership · #4 personas · #5 KOS-impact · #6 knowledge-level) — PHASE_06 dated-amendment census = 7 entries ✓ (6 + the Campaign-Approval seed-5 amendment); each demonstrably applied in §1/§1B/§2/§3/§6/§7-8 respectively; **none unaccounted** |

## 10. Phase-7 work queue (DOCDISC-G, 2026-07-13) ✅ — THE handoff artifact (ordered by DOCCLEAN sub-phase, P1 first within each)

Fields per owner order: id · finding(s) · priority · owning phase/sub-phase · class ·
dependency · owner approval? · battery? · docs/code. **ALL rows docs-only; battery = the
single manifest row (CI-guarded file, code-adjacent by test surface, zero app code).**

| id | Finding(s) | Pri | Owns | Class | Dep | Appr? | Batt? |
|---|---|---|---|---|---|---|---|
| Q-0a | B.3-4 history_service page · F-D-04 AI_PATTERN index · B.3-3 unwritten journeys · B.3-7 PAGES appetite | P1 | 7/DOCCLEAN-0 | missing-doc VENUE ruling (DC-D1: creation ≠ cleanup) | — | **YES** | no |
| Q-0b | DAR divergences ×2 (UI pair · PRODUCT_INTEGRATION_DESIGN) + naming ruling (F-A-01/03: rename vs Standard §20 amendment) | P1 | 7/DOCCLEAN-0 | owner rulings | — | **YES** | no |
| Q-A1 | F-D-08 FEATURE_INDEX refresh | **P1** | 7/A | stale (R3 seed — HARD Phase-8 input) | — | no | no |
| Q-A2 | F-A-09/D-03 roadmap/current-state banner-pointers | **P1** | 7/A | stale/wrong-canonical | — | no | no |
| Q-A3 | F-A-06 worker-cert meta-audit evidence section | **P1** | 7/A | Missing (seed 5; memory-sourced, unrecoverable marked) | — | no | no |
| Q-A8 | backlog #6 RBAC.md role table rebuild (seed 3; named venue) | P1 | 7/A | stale | — | no | no |
| Q-A4 | F-A-08/D-02 UI hierarchy statement + F-B-05 7-rules materialization | P2 | 7/A | duplicate/prose-locked | Q-0b | **YES** | no |
| Q-A5 | F-C-05 patterns_ai README drift + GUIDE cross-link | P2 | 7/A | fragmentation (pre-logged) | — | no | no |
| Q-A6 | F-B-06/D-04 backlog scope-split statements ×2 | P2 | 7/A | duplicate→split | — | no | no |
| Q-A7 | F-C-03 raw-materials era-doc staleness check → banner/pointer | P2 | 7/A | stale-check | — | no | no |
| Q-A9 | B.3-6/GC-03 apps/README blurbs refresh | P3 | 7/A | stale | — | no | no |
| Q-B1 | F-C-01 OWNERSHIP_MATRIX extension (family rows + class column) | **P1** | 7/B | wrong-ownership | — | no | no |
| Q-B2 | 434-row metadata retrofit (incl. F-C-02 class fixes + census type corrections) | P2 | 7/B | metadata (R2) | Q-B1, §2.4 derivability | batch-review | no |
| Q-C1 | F-D-01 dead links — CLAUDE.md + PKM rows | **P1** | 7/C | broken link | — | no | no |
| Q-C1b | F-D-01 dead links — MANUFACTURING_V1_FREEZE ×4 (T1) | **P1** | 7/C | broken link (T1 change control) | — | **YES** | no |
| Q-C2 | F-D-05 read-4-files ×3 · F-D-06 START_HERE row B (+FOM/PDD) · F-D-07 CLAUDE.md header | **P1** | 7/C | navigation | — | no | no |
| Q-C3 | F-E-04 15 archive-citations re-label/re-point | P2 | 7/C | §15 violation | — | no | no |
| Q-C4 | F-D-03 orphan index rows (docs-root era files + PAGES/ACCESS_CONTROL) | P2 | 7/C | orphan | Q-D1/D2 (archive first shrinks the list) | no | no |
| Q-C5 | B.3-3 journeys README rows for the WRITTEN journeys | P2 | 7/C | index repair | Q-0a (unwritten part) | no | no |
| Q-C6 | F-D-02 53 code-links: batch-fix or convention note | P3 | 7/C | broken link | Q-0b-style choice | choice | no |
| Q-D1 | F-E-01 root superseded families (foundation 5 · plans 7 · design-system ~20) banner+archive per DAR | **P1** | 7/D | stale→archive | Q-A4 (UI survivor first) | **YES** (batch) | no |
| Q-D2 | F-E-02 PI drafts (~16) banner+archive | P2 | 7/D | stale→archive | Q-0b (INTEGRATION_DESIGN ruling) | **YES** | no |
| Q-D3 | F-A-02/F-B-08 audit_phases archive (naming moot on move) | P3 | 7/D | archive candidate | — | **YES** | no |
| Q-D4 | F-E-03 pkals_v2 supersede→archive | P3 | 7/D | archive candidate | — | **YES** | no |
| Q-D5 | archive-tree rebuild: 104 index rows · 65 banners · B.3-5 pointer · F-E-05 cascade re-resolution | P2 | 7/D | archive integrity | Q-D1..D4 (moves land first) | no | no |
| Q-D6 | F-A-05 partial.json + DAR REMOVE-LATER ×3 (archive-only this campaign, DC-D3 zero deletions) | P3 | 7/D | REMOVE-LATER class | — | **YES** | no |
| Q-D7 | F-A-01/03/04 renames IF ruled at Q-0b (move-class: inbound census → mv → rewrite) | P3 | 7/D | naming | Q-0b | **YES** | no |
| Q-E1 | **manifest refresh**: F-B-01/02 lesson→truth re-routes · F-B-03 backlog route · F-B-04 +8 topics · also[] APPS removal (D-01) | **P1** | 7/**E** | wrong-canonical/Missing | Q-A1, Q-A2 (targets live first) | queue-validated | **YES — the ONE battery-bearing row (PkalsNavigationGuardTests + full battery per PHASE_07)** |

### 10.2 Later-phase handoff rows (owned OUTSIDE Phase 7 — recorded so nothing orphans)

| id | Item | Owner |
|---|---|---|
| H-8 | GC-07 FEATURE_INDEX → features/ taxonomy extraction + 6 additive-minor schema inputs + 4 coverage censuses + R5/quarantine constraints (§8.3) | **Phase 8** (KG-0 Design Record) |
| H-9a..d | F-B-07 frozen-canonical hubs · F-C-04 barcode hub · F-C-06 costing hub · F-C-07 inventory sub-domain hubs — feature docs/cards ARE the resolution | **Phase 9** |
| H-9e | GC-01/02/06/08/09/10 hybrid-fence lanes (owner-activated per PHASE_09) + GC-05 manifest→view at GEN-D + GC-11 regeneration | **Phase 9** |
| H-14 | GC-04 COVERAGE_REPORT → knowledge_sync report class | **Phase 14** |
| H-19 | F-A-10/D-06 deployment-procedure consolidation into the runbook | **Phase 19** |

**Fold-map proof (no orphan findings · no conflicting ownership):** every one of the 40
findings appears in exactly one Q-row or H-row above (F-D-01 spans Q-C1+Q-C1b — one finding,
one owning phase, two execution rows for gating clarity); duplicates D-01..06 ride their
F-rows; 12 GC rows all owned (7 ×Phase-9 lanes · 1 ×8 · 1 ×14 · 1 ×7-then-regen · 2 ×9
targets). **Zero unassigned · zero dual-owned · zero unresolved discovery outputs.**

## 11. Seeded-inputs disposition table — FINAL (DOCDISC-G) ✅

| Seed | Disposition |
|---|---|
| 1a B.2 (5 items) | archive index 12/104 ✓→Q-D5 · manifest stale 17-topics ✓→F-B-04/Q-E1 · PKALS APPS missing machines+patterns_ai ✓→F-A-07/D-01 evidence · 3 drifted app READMEs ✓ (patterns_ai→Q-A5 · production/accounts checked at C/E: no live contradiction found beyond registered rows) · 41 memory-links → appendix note ✓ (out of census scope) |
| 1b B.3 (9 items) | 1 read-4-files ✓ F-D-05/Q-C2 · 2 roadmap route ✓ F-B-03/Q-E1+Q-A2 · 3 journeys ✓ F-D-03+Q-C5/Q-0a · 4 history_service ✓ §8.1/Q-0a · 5 archive README ✓ F-E-05/Q-D5 · 6 apps blurbs ✓ Q-A9 · 7 PAGES backlog ✓ §8.1/Q-0a · 8 pkals_v2 ✓ F-E-03/Q-D4 · 9 minor trio ✓ (AV2 label F-D-05 · HTML name-collision noted in F-E-01 family · partial.json F-A-05/Q-D6) — **9/9 disposed** |
| 2 DOCUMENT_ARCHIVE_REVIEW | reconciled per-family §6.1 (AGREE+EXTEND · 2 divergences→Q-0b · 1 erratum · NO KEEP overruled) |
| 3 backlog #6 + patterns_ai drift | ✓ Q-A8 · Q-A5 (certification citations carried) |
| 4 the Standard + Phase-5 evidence | applied throughout as the measuring stick; never re-litigated ✓ |
| 5 worker-cert meta-audit (dated amendment) | ✓ F-A-06/Q-A3 |

**None silently dropped — every seed confirmed-into-register or disposed with pointer.**

## 12. Handoff statement (Phase 6 → Phase 7)

Phase 7 (DOCCLEAN-0) may execute **Q-A1..Q-E1 without further discovery** — every row
carries finding-id, evidence (§-refs), Standard clause, KOS-impact (§6.4), and risk flag.
**Owner input required before/at DOCCLEAN-0:** Q-0a venue ruling + Q-0b rulings + the 8
owner-approval rows (batch archive approvals, T1 freeze edit, REMOVE-LATER). **Battery
arms exactly once** (Q-E1, DOCCLEAN-E, per PHASE_07's quarantine design). Off-queue defects
discovered during cleanup return here ONLY as dated Phase-6 amendments (no silent
re-discovery). Phases 8/9/14/19 receive §10.2 + §8's readiness pack.

## 13. 🏁 PHASE 6 VERDICT

**CENSUS-COMPLETE.** 540/540 boundary files inventoried against the frozen Standard; 40
findings, all classed, evidenced, KOS-impact-enriched, single-owned; 6 owner clarifications
incorporated with zero unaccounted; all seeds disposed; corpus proven unmutated; work queue
ordered and risk-flagged; success criteria §3.1–7 ALL MET (1 report+all artifacts ✓ ·
2 coverage arithmetic ✓ · 3 single-class findings ✓ · 4 seeds ✓ · 5 zero mutations ✓ ·
6 queue countersigned by this census ✓ · 7 status/memory synced, battery baseline
untouched+never run ✓). No blockers within Phase-6 scope — the "with-blockers" variant is
NOT invoked. Phase 7 gate: DOCCLEAN-0 (owner-gated).

_Report complete. Post-close corrections land only as dated amendments._

## Appendix — memory-links maintenance note (contract §2.1)

The 2026-07-11 audit's "41 broken docs-links in agent memory" is a memory-maintenance note,
NOT census scope (repo docs must stand without memory — Standard §8). Recorded here at
DOCDISC-0 for the appendix as required; any agent with persistent memory repairs its own
memory links opportunistically outside this phase. — _(further notes appended at DOCDISC-G if any)_
