---
id: docs-release-certification-program
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# Release Certification Program (RCP) — Campaign Phase 18A

> **PERMANENT methodology (owner directive 2026-07-18).** The project's final
> release-certification stage: the ENTIRE ERP certified as ONE integrated product —
> complete business workflows, cross-application integration, UI quality, permissions,
> calculations, data integrity, reports, dashboards, and user experience — in the
> browser, phase by phase, before ANY deployment. This is not feature development, not
> implementation, not bug fixing as a goal (fixes happen through the certification
> loop). **Deployment is FORBIDDEN until this program completes** (see §6).
> Status: **PROGRAM RATIFIED 2026-07-18** ("OWNER AUTHORIZATION — PHASE 18A —
> RELEASE CERTIFICATION PROGRAM"): the owner defined the BINDING wave structure
> **RCP-0..RCP-9** (§3) — dimension-based certification (architecture · business ·
> security · financial · data · testing · documentation · deployment · decision).
> The earlier RC-0..RC-F sketch is SUPERSEDED as a structure and RETAINED as the
> browser-verification instrument consumed inside RCP-2/3/4 (mapping in §3).
> This revision = the owner-ordered RCP-0 planning package: Charter (§3a) ·
> Certification Plan (§3b) · Certification Matrix (§3c) · Scorecard Template (§3d) ·
> Risk Register (§3e). Evidence log: [RELEASE_CERTIFICATION_LOG.md](RELEASE_CERTIFICATION_LOG.md).
> Numbering: inserted as **Phase 18A** — an ADDITIONAL permanent stage; no existing
> phase renumbered or compressed (the 16–22 freeze holds).

## 1. Placement in the roadmap (and why)

```
16 Monthly Expense Engine ─┐ implementation
17 RM → Expense Cost Integ ┘
18  Future Feature Documentation Updates   (docs converge, sync-clean baseline)
18A ★ RELEASE CERTIFICATION PROGRAM ★      (this program — certify the whole product)
19  Deployment Documentation               (documents the CERTIFIED product; RCP = readiness input)
20  Production Deployment                  (gate now ALSO requires 18A complete)
21  Deployment Readiness Certificate       (cites the RCP certification package)
22  First Git Checkpoint
```

**Why after 18, before 19:** (a) both implementation phases (16/17) are closed — the
program certifies a STABLE product once, instead of re-certifying after each feature;
(b) Phase 18 leaves documentation sync-clean, so certification verifies TRUE docs;
(c) Phase 19's runbook then documents the certified product and lists the RCP
certificate among its readiness inputs; (d) fixes discovered here land BEFORE the
deployment documentation freezes, not after. Certification later (between 19 and 20)
would let cert-driven fixes invalidate finished deployment docs; earlier (before 17)
would certify a product that is still changing.

## 2. Program laws (permanent)

1. **Phased, never monolithic** — no single enormous browser sweep; each phase is a
   bounded certification unit with its own verify → document → classify → fix →
   re-verify → certify loop.
2. **No phase begins until the previous phase is certified.**
3. **Certification loop per phase:** browser verification (real logins, real clicks,
   3 widths) → findings documented in the issue register → classified
   (**CRITICAL / MAJOR / MINOR / OBSERVATION**) → CRITICAL+MAJOR fixed via the Phase-4
   defect protocol (U8 money stops apply; battery after every fix wave) → re-verify →
   phase certificate recorded in the evidence log.
4. **Quality over speed; token usage is not a concern** (owner ruling verbatim).
5. Certification runs on **seeded scratch worlds** (`seed_factory` + feature scenarios)
   plus read-only primary checks — never destructive on primary; browser evidence =
   the BOD-E/MEE-C headless-chrome method (authenticated capture at 360/768/1280) +
   scripted click-throughs; console/JS errors captured per page.
6. Existing instruments are the substrate, never duplicated: battery (U5) ·
   `verify_*` engine · `knowledge_sync` · golden journeys ₹801/₹344.25/₹633/₹225 ·
   the certified permission matrices. RCP ADDS the integrated-product browser layer
   on top; it re-USES every lower layer.
7. Performance = OBSERVE AND DOCUMENT only (no optimization work inside RCP).

## 3. THE BINDING WAVE STRUCTURE — RCP-0..RCP-9 (owner-ratified 2026-07-18) + Release Roadmap

| Wave | Dimension | Objective (headline) | Verdict form |
|---|---|---|---|
| **RCP-0** | Release planning | this charter package ratified; evidence log live; rig/worlds inventory confirmed | package accepted |
| **RCP-1** | Architecture | verify architecture/module boundaries/dependency rules/ADR compliance/layering/ownership/extension seams/tech debt; classify risks critical/acceptable/deferred. **Evidence only — no repairs** | Architecture Certificate |
| **RCP-2** | Business | EVERY completed feature: implemented · documented · tested · certified · traceable; no orphan features; **complete feature inventory**. Browser verification = the RC instrument below | Business Certificate + Feature Inventory |
| **RCP-3** | Security | permissions/role boundaries/authn/authz/financial visibility/write restrictions/privilege-escalation hunt/management-only views/FINANCIAL_ROLES | Security Certificate |
| **RCP-4** | Financial | ledger integrity · money-write rules · ADR-0009 · ADR-0011 · one-rupee-once · costing · expense reporting · settlements · historical consistency. No recalculation bugs, no duplicate money | Financial Certificate |
| **RCP-5** | Data | schema/constraints/datasets/seed scenarios/migration history/rollback safety/historical integrity. **No schema work** | Data Certificate |
| **RCP-6** | Testing | unit+integration coverage census · golden scenarios · performance pins · verification suites · battery history | Testing Certificate |
| **RCP-7** | Documentation | **CONSUME Phase 18 — do not repeat FFD**: verify the estate REMAINS synchronized (sweep + fixed-point re-check) | Documentation Certificate |
| **RCP-8** | Deployment readiness | deployment docs · rollback · recovery · monitoring · logging · configuration · environment readiness · known operational risks (feeds Phase 19) | Readiness Certificate |
| **RCP-9** | Release decision | Release Scorecard (filled §3d) · Risk Register final · Blocking Issues · **Go / No-Go recommendation** · Executive Summary | GO / NO-GO |

**Every subsystem exits a wave either CERTIFIED or BLOCKED — with objective evidence.
Nothing assumed; everything demonstrated.** One wave per owner authorization; STOP
after each (U3).

**RC→RCP mapping (the retained browser instrument):** RC-0→RCP-0 · RC-1 (auth/RBAC
browser matrix) → RCP-3 · RC-2..RC-8 (per-app walks + the E2E owner chain + golden
journeys through the browser) → **RCP-2's verification body** · RC-9 (₹-surface
reconciliation) → RCP-4 · RC-10 (UI/responsive/console sweep) → inside RCP-2
(mobile-first = a FUNCTIONAL business requirement, rule 11) · RC-11 (data/perf
probes) → RCP-5 + RCP-6 observations · RC-F → RCP-9.

## 3a. Release Certification Charter (RCP-0)

1. **Release scope:** the ENTIRE ERP as it stands at Phase-18 close — 13 apps
   (accounts · inventory · raw_materials · production · tracking · expense · machines
   · storefront · core · bod · patterns_ai · devseed · verification), all surfaces,
   MANUFACTURING V1 FREEZE + campaign phases 0–18 inclusive; tree = git HEAD
   `49404001` + the uncommitted campaign body (U2). OUT of scope: post-P22 visions
   (RM-V2, KOS consolidation, pattern phases 4–6), anything in a deferred register.
2. **Release criteria:** all eight dimensions (RCP-1..8) CERTIFIED; zero CRITICAL/
   MAJOR open; every BLOCKED item either fixed+re-verified or owner-dispositioned;
   RCP-9 recommendation delivered and owner-ratified.
3. **Certification methodology:** per wave — verify (evidence-first, existing
   instruments as substrate §2.6) → document (append-only log) → classify (§4
   severity + CERTIFIED/BLOCKED/ACCEPTED-RISK/DEFERRED) → fix ONLY through the
   defect protocol (CRITICAL/MAJOR; U8 money stops; battery after fix waves) →
   re-verify → certify. Independent instruments preferred: scripted checks,
   fresh-context reconstruction/adversarial agents (the Phase-18 FFD-D audit
   workflow — supplemental only, MAIN-THREAD verifies every finding), live browser
   evidence (authenticated headless-chrome, 3 widths).
4. **Evidence standards:** every certificate row carries venue evidence (grep/
   script/screenshot/test-run) — certificates assert ONLY what evidence shows
   (Phase-18 FFD-D lesson, binding). Money claims: reconciliation identities on a
   seeded world + read-only primary checks. UI claims: 360/768/1280 captures.
   Coverage claims: census tables (every route/feature/model enumerated, none
   sampled silently — no silent caps).
5. **Acceptance rules:** owner accepts each wave certificate before the next wave
   (U3). ACCEPTED-RISK requires recorded reason + explicit owner sign-off in the
   wave's authorization or close review. Nothing self-accepted.
6. **Blocking conditions (automatic wave-block):** any money-truth violation (U8
   STOP) · any security/permission leak · data loss/corruption evidence · workflow
   dead-end without workaround · battery red · sweep BLOCKER · a certificate claim
   that evidence contradicts.
7. **Exit criteria:** §6 deployment rule satisfied — every wave certified, zero
   CRITICAL/MAJOR open, scorecard complete, Go recommendation + owner ratification.
8. **Certification order & why:** RCP-1→9 as listed — foundations before surfaces
   (architecture first: everything else cites its boundaries), business before
   security/financial (the feature inventory IS their checklists' denominator),
   data/testing before docs (docs certify against verified reality), deployment
   readiness last-before-decision (it consumes all certificates; feeds P19),
   decision closes.
9. **Deliverables:** per wave — the wave certificate + findings register rows +
   evidence pack in [RELEASE_CERTIFICATION_LOG.md](RELEASE_CERTIFICATION_LOG.md);
   program-final — the filled Scorecard, final Risk Register, Blocking Issues
   census, Go/No-Go recommendation, Executive Summary (RCP-9).

## 3b. Certification Plan (per wave: inputs to REUSE → activities → evidence → exit)

- **RCP-1 Architecture.** Inputs: `.importlinter` contracts · ADR-0001..0011 ·
  service-layer/single-writer rules (CLAUDE.md #4–6) · OWNERSHIP_MATRIX · knowledge
  graph `b64db8bac13e` · FF-1..FF-28 tech-debt review. Activities: dependency-rule
  census (run import-linter; map violations if any) · ADR-by-ADR compliance table
  (each Decision → where enforced → proof pointer) · layering/boundary walk per app
  · seam inventory (extension points vs frozen cores) · debt register classification
  (critical/acceptable/deferred). Evidence: linter output, per-ADR tables, seam
  census. Exit: Architecture Certificate, risks classified. **No repairs.**
- **RCP-2 Business.** Inputs: PDD v1.0 + amendment register (8 entries) ·
  MANUFACTURING_V1_FREEZE · FACTORY_OPERATIONS_MASTER (16 ops, 3 settled journeys)
  · feature registry (25+ devseed slugs) · docs/features cards (581) · the RC browser
  instrument (§3 mapping). Activities: build THE feature inventory (every shipped
  feature → PDD/charter source → code → tests → docs → certification pointer —
  five-way traceability, no orphans) · browser certification per the RC walk plan
  (real logins, 3 widths, golden journeys through the browser). Evidence: inventory
  table + URL census + captures. Exit: Business Certificate + Feature Inventory.
- **RCP-3 Security.** Inputs: WORKER_ROLE_CERTIFICATION (9 apps + meta-audit, 0
  global issues) · per-phase identity matrices (BOD-E/MEE-D/RMX-D) · 4-layer
  FINANCIAL_ROLES wall proofs · accounts security baseline (Argon2, rate limits,
  lockout) · S2/S3 fixes · SidebarItemRule double-gate. Activities: integrated role
  × surface matrix re-verification · privilege-escalation hunt (adversarial agents +
  main-thread) · write-restriction census (GET-only posture of read windows) ·
  PHASE_03 accountant contradiction → owner disposition. Exit: Security Certificate.
- **RCP-4 Financial.** Inputs: R5 Money-Write census + ADDENDUM 1 · ADR-0009/0011
  compliance tables (RMX-E) · golden journeys ₹801/₹344.25/₹633/₹225 ·
  one-rupee-once pins · verify_factory engine (19 checks) · ledger baselines
  (170/Σ₹10,880.25). Activities: whole-ERP ₹-surface reconciliation on ONE seeded
  world (every rendered ₹ ≡ its owning service ≡ the ledger; the RC-9 scope) ·
  duplicate-money hunt across combined views · historical-consistency replay.
  Exit: Financial Certificate. U7/U8 discipline: money work MAIN-THREAD.
- **RCP-5 Data.** Inputs: 26+ CheckConstraints (PR1/PR2) · U14 migration gates +
  reverse-proofs (0015/0042 etc.) · seeder certification (22/24 scenarios;
  byte-identical goldens) · dataset spec frozen-v1 + amendments A1–A4. Activities:
  fresh-DB full `migrate` + targeted reverse paths · constraint census vs models ·
  seed-world convergence re-proof · PRIMARY data hygiene census (dev cast/dev Addas
  teardown decision → owner) · append-only spot-audits. Exit: Data Certificate.
- **RCP-6 Testing.** Inputs: battery baseline 1871/1871 + its full history chain ·
  verification engine 1.0.0 (5 commands) · perf pins (a360 80 · costing 16) ·
  golden byte-asserts. Activities: coverage census vs the RCP-2 feature inventory
  (every feature → its tests; gaps = findings) · pin inventory + rationale table ·
  battery re-run at wave close. Exit: Testing Certificate.
- **RCP-7 Documentation.** Inputs: **Phase 18 wholesale** (FFD-0..E; permanence
  §20-A3). Activities: `knowledge_sync --deep` re-run (expect BLOCKER=0/WARN=2
  accepted) · graph fixed-point re-check · certificate-consistency spot-audit (the
  FFD-D 10-stage walk on ONE more phase as a sample). Exit: Documentation
  Certificate. **Consume, never repeat.**
- **RCP-8 Deployment readiness.** Inputs: deploy/README runbook ·
  ENFORCEMENT_ROLLOUT_RUNBOOK (flags OFF→soak→enable) · P19 contract · settings
  split (base/local). Activities: runbook walk-through vs the real target
  environment · rollback/recovery paths (DB backup/restore drill on scratch) ·
  monitoring/logging posture census (KNOWN GAP — likely findings) · configuration/
  secrets audit · operational risk register. Exit: Readiness Certificate → Phase 19
  input.
- **RCP-9 Release decision.** Fill §3d scorecard from the eight certificates ·
  finalize §3e · blocking-issues census · **Go/No-Go recommendation** · Executive
  Summary. Owner ratifies.

## 3c. Certification Matrix (dimension × existing evidence base × gap-to-certify)

| Dimension | Already-certified base (REUSE) | Gap the wave must close |
|---|---|---|
| Architecture | importlinter · ADRs · single-writer rules · graph | no single current-state compliance census |
| Business | PDD+freeze · FOM 16 ops · role certs · 581 cards | whole-product feature inventory + browser walk |
| Security | 9-app worker cert · identity matrices · wall proofs | integrated re-verify + escalation hunt + accountant ruling |
| Financial | R5 census · RMX-E tables · goldens · verify_factory | whole-ERP ₹-reconciliation on one world |
| Data | constraints · U14 reverse-proofs · seeder cert | migration-history run + hygiene census |
| Testing | battery 1871 + chain · engine 1.0.0 · pins | coverage-vs-inventory census |
| Documentation | Phase 18 COMPLETE | re-verify still-clean only |
| Deployment | deploy/README · rollout runbook | environment/monitoring/rollback verification |

## 3d. Release Scorecard TEMPLATE (filled at RCP-9)

| Wave | Dimension | Status (CERTIFIED / BLOCKED / ACCEPTED-RISK) | Evidence (log §) | Date | Owner acceptance |
|---|---|---|---|---|---|
| RCP-1 | Architecture | — | — | — | — |
| RCP-2 | Business | — | — | — | — |
| RCP-3 | Security | — | — | — | — |
| RCP-4 | Financial | — | — | — | — |
| RCP-5 | Data | — | — | — | — |
| RCP-6 | Testing | — | — | — | — |
| RCP-7 | Documentation | — | — | — | — |
| RCP-8 | Deployment readiness | — | — | — | — |
| **RCP-9** | **RELEASE DECISION** | **GO / NO-GO** | — | — | — |

## 3e. Release Risk Register (seeded 2026-07-18; LIVING — waves append; final at RCP-9)

| Id | Risk | Class (initial) | Owning wave |
|---|---|---|---|
| RR-1 | **Entire campaign body uncommitted until P22** (HEAD `49404001`; disk failure loses months) — snapshot refresh DUE (owner, standing since P9) | **CRITICAL (operational)** | RCP-8 + owner action NOW |
| RR-2 | Monitoring/logging/backup posture undefined | critical (gap) | RCP-8 |
| RR-3 | Deployment runbook never walked against a real target | critical (gap) | RCP-8 → P19 |
| RR-4 | PHASE_03 accountant contradiction (role reaches no page) — knowingly open | acceptable (needs ruling) | RCP-3 |
| RR-5 | Dev data in PRIMARY (dev.* cast; dev Addas 011/013/014/015 teardown pending owner) | acceptable (hygiene) | RCP-5 |
| RR-6 | Enforcement flags default OFF (allocation-bound · settlement-recon · ledger lever) — deploy-OFF→soak→enable runbook | acceptable (by design) | RCP-8 |
| RR-7 | No load/performance testing (pins are query-count, not latency) | acceptable (observe-only §2.7) | RCP-6/8 |
| RR-8 | Bus factor 1 (single owner-operator) | deferred (accepted) | RCP-9 note |
| RR-9 | S6 `reported_quantity` retirement deferred (irreversible; post-deploy soak-gated) | deferred (by design) | RCP-9 note |
| RR-10 | P18 accepted exceptions (CLAUDE.md frontmatter · doc-islands · unarchived session evidence · truncated historical hashes) | accepted (recorded) | RCP-7 |
| RR-11 | INFO residue #6–#14 (fix-when-touched) + accounts ≈5 role-lookups/request | acceptable | RCP-1/6 |
| RR-12 | 3-Patti config pass blocked on RR-5 teardown (stage-trio testing debt) | acceptable | RCP-2 |

## 4. Issue classification (program-wide)

| Class | Meaning | Gate effect |
|---|---|---|
| CRITICAL | money wrong · data loss/corruption · security/permission leak · workflow dead-end | blocks the phase; fix + re-verify mandatory |
| MAJOR | broken feature/page/flow with no workaround; wrong business behavior | blocks the phase; fix + re-verify mandatory |
| MINOR | cosmetic/UX defects with workaround | fix-or-register (owner dispositions at RC-F) |
| OBSERVATION | performance notes, polish ideas, future items | register only (PENDING_BACKLOG) |

## 5. Evidence standard

Per phase: URL census coverage table (every route of the scope visited, status noted) ·
authenticated screenshots at 360/768/1280 for every page class · click-through scripts/
receipts for every CRUD + workflow step · console/JS error log per page · findings
register rows (id · class · evidence · fix commit-intent · re-verify proof) · battery
result after any fix wave · the phase certificate line. All appended to
`RELEASE_CERTIFICATION_LOG.md` (created at RCP-0; append-only).

## 6. Deployment rule (permanent, binding)

Deployment (Phase 20) is FORBIDDEN until: every RCP wave certified · zero CRITICAL/MAJOR
open · all required browser verification complete · all major business workflows
certified · all inter-application integrations certified · the **RCP Final Certification**
issued at RCP-9 (GO). Phase 19 lists the RCP certificate as a readiness input; Phase 21's
Deployment Readiness Certificate CITES it. Recorded as a dated amendment in the campaign
framework README (the P20 entry gate now includes Phase 18A).

## 7. Permanence

This program is part of the execution methodology from now on: any FUTURE feature
program (post-22 roadmaps included — e.g. Raw Materials V2) ends with its own RCP pass
before its deployment, using this document as the template.
