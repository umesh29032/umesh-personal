---
id: docs-campaign-contracts-readme
type: entry-index
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Campaign Execution Contracts — framework + master index

> **Owner directive 2026-07-12 (strategy change):** the remaining pre-deployment campaign phases
> are executed CONTRACT-FIRST. Every remaining phase gets a written execution contract in this
> directory BEFORE any implementation. Contracts are authored one phase per session (owner-gated),
> by a planning-capable model; execution may later be performed by ANY AI (Claude, GPT, Gemini, …)
> or a human, using ONLY these documents — zero chat history required.
>
> **⚠️ OWNER DIRECTIVE 2026-07-13 — PLANNING → EXECUTION TRANSITION:** the contract layer is
> COMPLETE and FROZEN. All 21 contracts (phases 0, 2–21) were verified and RATIFIED by the
> owner via the Campaign Approval Pass —
> **[CAMPAIGN_APPROVAL_REPORT.md](CAMPAIGN_APPROVAL_REPORT.md) is the final architectural
> approval of record** — converting every contract to 🔒 (frozen: never rewrite; dated
> amendments through each contract's designated mechanism only). **Contract authoring is
> CLOSED** — the sole future authoring act is the deliberately reserved Phase-22 contract, at
> the owner's chosen time. **The campaign is now in EXECUTION mode:** phases execute per the
> locked order and each contract's §17 resume instructions, one sub-phase per session (U3),
> owner-gated at every -0 decision pack. First execution step: Phase 0 SNAP-0, then the
> locked order from Phase 2 → OWN-A.

## Document hierarchy (which file wins)

1. **[../DEPLOYMENT_CAMPAIGN_STATUS.md](../DEPLOYMENT_CAMPAIGN_STATUS.md)** — LIVE STATE.
   What is done, what is next, current battery baseline, open carry-overs. Always read FIRST.
2. **This directory** — HOW TO EXECUTE each phase. One contract per phase,
   `PHASE_<nn>_<SLUG>.md`. A contract is FROZEN once owner-approved: never rewrite a frozen
   contract; append a dated `## Corrections` section if reality forces a change, and mirror the
   correction into the status file. A contract may additionally be a **parent contract** for a
   family of phases (e.g. [PHASE_05_DOCUMENTATION_FOUNDATION.md](PHASE_05_DOCUMENTATION_FOUNDATION.md)
   for documentation phases 6–9, 14, 18–19): child contracts inherit its definitions exactly as
   all contracts inherit U1–U14 from this README, and state only their deltas.
3. **Per-phase evidence docs** (e.g. [../OWNER_VISIBILITY_CERTIFICATION.md](../OWNER_VISIBILITY_CERTIFICATION.md))
   — WHAT HAPPENED. Evidence appended at each sub-phase close, per the contract's rules.

Conflict rule: status file wins on *state*, contract wins on *procedure*, evidence doc wins on
*what was actually observed*. A contradiction between them is itself a finding — report it to the
owner before proceeding (precedent: campaign reconstruction 2026-07-12 found 4 doc-drift items).

## Universal invariants (inherited by EVERY contract — contracts state only their deltas)

These are owner standing orders. No contract may weaken them; a contract may only tighten them.

| # | Invariant |
|---|---|
| U1 | **Engine FROZEN.** No refactors, no cleanup, no redesigns, no drive-by improvements. Fix ONLY findings confirmed with evidence inside the active phase's mandate. |
| U2 | **NO COMMITS** until campaign phase 22 (First Git Checkpoint). No branch switches, no stashes, no `git add`. The working tree IS the product until phase 22. |
| U3 | **One sub-phase per session. STOP after each.** Next sub-phase is owner-gated. Never continue automatically. |
| U4 | **Regression pins ONLY for confirmed fixes.** No speculative tests. |
| U5 | **Battery = sequential, fresh test DBs, ONLY when code changed.** 9-app suite (`accounts core raw_materials production tracking expense storefront inventory machines`) + `patterns_ai` as separate runs. NEVER `--parallel`, NEVER `--keepdb` across suites (DEPLOYMENT_BACKLOG #4 + MGT-F addendum: keepdb carries truncated Role rows between suites → false failures). Current canonical baseline: see status-file dashboard. |
| U6 | **Docs-sync same session** (owner rule 2026-06-12): any code change ⇒ its docs/ md updated in the same session (lookup order: `docs/apps/<app>/GUIDE.md` → `config/<app>/README.md` → topic canonical via [../DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md)). |
| U7 | **Audit honesty** (owner rule 2026-06-15): sub-agent/workflow findings are supplemental only. NEVER mark a surface clean because sub-agents found nothing; finder failures are recorded in the evidence doc. Money and final verdicts = main-thread. |
| U8 | **Money-Write STOP rule** (owner rule 2026-07-05): any new money-write path outside the approved single-writer services ⇒ STOP the session and report; never silently fix. Single writers: `ledger_service` for `WorkerLedgerEntry`, `history_service` for `*History` tables, settlement money only via settlement services. |
| U9 | **Frozen Foundation rules** (owner lock 2026-07-05): manager-assignment-only rosters · access-control-only visibility · settlement-only money · read-only snapshots · mobile summary-first · fit-existing-architecture. No refactor/redesign of frozen modules without explicit owner approval. |
| U10 | **Enforcement flags stay OFF** (`ENFORCE_ALLOCATION_BOUND=False`, `ENFORCE_SETTLEMENT_RECONCILIATION=False`) until R11 — owner rollout policy. No campaign phase flips them. |
| U11 | **Evidence over inspection.** "Looks correct in code" is never a verdict. Every claim carries its probe artifact (status matrix, DB before/after, exact error/flash quote, rollback proof). |
| U12 | **Backlog discipline.** Findings outside the active mandate → INFO row in [../DEPLOYMENT_BACKLOG.md](../DEPLOYMENT_BACKLOG.md) (where found · what · why deferred · fix-when-touched spec). Never fixed on the spot. |
| U13 | **Data/history principles** (owner 2026-06-09): work-that-happened = immutable append-only; soft-state over delete; probe artifacts that land in append-only tables are disclosed in the evidence doc, not deleted. |
| U14 | **If a fix requires a migration**, STOP and get owner approval BEFORE writing it (migrations are semi-irreversible under U2's no-commit regime). |

## Environment facts (for any executing AI — verify, don't assume)

- Repo root: `/home/tech/umesh-personal/django_inventory`. Django 5.0 + PostgreSQL.
  Venv: `env/` → run everything as `env/bin/python config/manage.py <cmd>`.
  Settings: `config.settings.local`.
- Dev server expected on **:8003** (owner-run). If down: `env/bin/python config/manage.py runserver 8003`.
  Dev runserver caches templates — RESTART after template edits (production-audit lesson).
- Battery commands (U5):
  `env/bin/python config/manage.py test accounts core raw_materials production tracking expense storefront inventory machines`
  then separately `env/bin/python config/manage.py test patterns_ai`,
  then separately `env/bin/python config/manage.py test devseed`,
  then separately `env/bin/python config/manage.py test verification`.
  **[Dated amendment 2026-07-17, SEED-D4 — owner-approved verbatim ("the devseed test suite
  becomes an official sequential member of the canonical battery from Phase 12 onward"):**
  the dev-only `devseed` app's tests (guards · purity · idempotency · determinism · golden
  integration — golden tests IN the battery per the owner's SEED-D9 ruling, runtimes recorded)
  = the third sequential suite member. Same U5 laws: sequential, fresh test DBs, never
  --parallel/--keepdb.]
  **[Dated amendment 2026-07-17, VER-D6 — owner-accepted default (Phase 13 VER-0
  ratification, "I accept the defaults for VER-D1 through VER-D9 exactly as proposed"):**
  the production-present `verification` app's tests (read-only purity · guard polarity ·
  report determinism · SEED-D6 single-implementation pins) = the FOURTH sequential suite
  member of the canonical battery from Phase 13 onward. Same U5 laws apply.]
  **[Dated amendment 2026-07-17, SYNC-D8 — owner-accepted default (Phase 14 KS-0
  ratification): per SYNC-D1 the knowledge_sync engine is HOSTED IN `devseed` (its charter
  widens to "dev tooling"), so its tests live in the EXISTING devseed suite — the third
  sequential member's scope now covers seeder + knowledge_sync (no fifth suite; the devseed
  count grows). Same U5 laws apply.]
  **[Dated amendment 2026-07-18, BOD-D7 — owner-ratified (Phase 15 BOD-A authorization):**
  the `bod` app is a PRODUCTION feature app — its tests join the FIRST sequential member
  (the app suite), whose label list becomes
  `accounts core raw_materials production tracking expense storefront inventory machines bod`
  (10 apps) from Phase 15 onward. Same U5 laws apply.]
- Identities: manager `dev.mgr@test.local` / Dev@12345 · worker `dev.ow.a@test.local` / Dev@12345 ·
  listing team `dev.listing` · owner/SA `umesh29mar@gmail.com` pk=1 (**password NOT recorded in repo
  docs — owner supplies at session start**; Claude sessions: memory `test-credentials`).
  Login `/app/login/password/` (bypasses OTP). **Rate-limited per IP+email — one wrong attempt can
  lock ~15-30 min; type exactly.**
- Test data: DEV-marked entities are fair game (owner rule 2026-07-04); never touch non-DEV rows
  destructively. OTP-send POSTs are never probed (EMAIL_BACKEND may be real SMTP).
- Git state at contract-framework creation: HEAD `49404001`, ~306 dirty/untracked paths — the
  entire July body of work exists ONLY in the working tree (why U2 + Phase 0 matter).

## The 17-section contract template

Every phase contract has exactly these sections, in this order:

1. **Phase objective** — one paragraph; the question the phase answers or the thing it builds.
2. **Scope** — in/out lists; apps, URLs, services, docs touched by the phase.
3. **Success criteria** — testable exit conditions; what makes the phase DONE vs merely attempted.
4. **Rules of engagement** — deltas from the universal invariants (tightenings only).
5. **Evidence standard** — what counts as proof for this phase's claims.
6. **Methodology** — numbered, repeatable steps per sub-phase.
7. **Sub-phase breakdown** — table: id, scope, size driver, probe targets, status checkbox.
8. **Deliverables** — artifacts that must exist at phase close.
9. **Files expected to change** — exhaustive allowlist (docs always; code only under stated conditions).
10. **Files that must never change** — the frozen set for this phase; touching one = STOP.
11. **Documentation update rules** — which doc gets what, at sub-phase close vs phase close.
12. **Memory update rules** — for agents with persistent memory: which memory file + index line. For agents WITHOUT memory: the on-disk docs in rule 11 are the complete binding record; memory is a convenience mirror, never the only copy of anything.
13. **Battery policy** — when to run, expected count arithmetic (baseline + pins), canonical procedure.
14. **Regression policy** — what must be re-proven, which negative controls, prior-fix guard list.
15. **Rollback policy** — how probes/writes are contained (transaction-wrapped shell, DEV-marked browser data, disclosed artifacts); what to do if state leaks.
16. **Stop conditions** — enumerated events that end the session immediately with a report.
17. **Resume instructions** — exact reading order + how to find the next unit of work, assuming zero chat history.

## Master index — every remaining phase

Contract status: ✅ authored · 🔒 authored+owner-approved · ☐ pending. Execution status lives in
the status file, NOT here.

| Phase | Name | One-line objective | Contract |
|---|---|---|---|
| 0 | Safety Snapshot | Preserve the uncommitted working tree (182 modified + 494 untracked + 1 deleted, all in django_inventory/) against loss; mechanism = OWNER DECISION D1–D5 (commit+tag / bundle / tarball / rsync mirror — vendor-neutral matrix in contract §6) | 🔒 [PHASE_00_SAFETY_SNAPSHOT.md](PHASE_00_SAFETY_SNAPSHOT.md) |
| 2 | Owner Visibility Certification | Certify the super-admin/owner role: zero false blocks, every SA-only op functional, universal walls hold (OWN-0 charter done; OWN-A..H paused pending contracts) | 🔒 [PHASE_02_OWNER_VISIBILITY.md](PHASE_02_OWNER_VISIBILITY.md) |
| 3 | Office / Support Role Certification | Certify `accountant` (FINANCIAL_ROLES member) + `listing_team` (STOREFRONT_ROLES member): blocked/allowed/functional on their designed surfaces. Headline: code-derived reachability contradiction — pure accountant is dispatch-403'd from every page hosting its own financial-field grant; deployment model = owner Design Record D1–D4 before probing | 🔒 [PHASE_03_OFFICE_SUPPORT_CERTIFICATION.md](PHASE_03_OFFICE_SUPPORT_CERTIFICATION.md) |
| 4 | Fix confirmed findings | Work ONLY the confirmed-bug residue from phases 1–3 + owner-selected backlog rows; pins + battery per fix. **PERMANENT implementation protocol** (owner designation 2026-07-12): 7-class finding taxonomy · bug lifecycle Confirmed→Fixed→Pinned→Battery→Docs→Closed · single-fix-at-a-time · smallest-change · CONFIRMED_FINDINGS_LEDGER; FIX-0 gated on phases 2+3 closing + owner F-D1..F-D3 | 🔒 [PHASE_04_CONFIRMED_FINDINGS.md](PHASE_04_CONFIRMED_FINDINGS.md) |
| 5 | Documentation Foundation (KOS) | Materialize the owner-frozen KOS design as DOC_STANDARDS.md; **PARENT contract** for phases 6–9/14/18–19 (KOS v3 core + drift register EMBEDDED in the contract's Appendix B — the chat/memory dependency is closed; owner ratification items R1–R12 pending at DOC-0) | 🔒 [PHASE_05_DOCUMENTATION_FOUNDATION.md](PHASE_05_DOCUMENTATION_FOUNDATION.md) |
| 6 | Documentation Discovery | Full documentation census against the ratified Standard (496 md at authoring + root/app-README companions); 11-class finding taxonomy → typed registers + Phase-7 work queue; discovery ONLY, zero repairs. **First CHILD of the PHASE_05 parent** — execution gated on DOC_STANDARDS.md `frozen-v1` (Phase 5 closed); evidence doc = DOCUMENT_DISCOVERY_REPORT.md | 🔒 [PHASE_06_DOCUMENTATION_DISCOVERY.md](PHASE_06_DOCUMENTATION_DISCOVERY.md) |
| 7 | Documentation Cleanup | Execute the Phase-6 work queue ONLY (no re-discovery): stale repairs (incl. backlog #6 RBAC table), duplicates/canonical re-pointing, metadata retrofit, link/nav repair, archive moves+banners+index (mv never git-mv; no stubs — inbound-rewrite rule; ZERO deletions), **canonical_manifest refresh isolated in battery-bearing DOCCLEAN-E** (quarantine mechanism keeps every other sub-phase battery-free). **Second CHILD of PHASE_05**; process shape = PHASE_04 permanent protocol adapted for docs; evidence doc = DOCUMENT_CLEANUP_LOG.md | 🔒 [PHASE_07_DOCUMENTATION_CLEANUP.md](PHASE_07_DOCUMENTATION_CLEANUP.md) |
| 8 | Knowledge Graph | Build knowledge_graph.json + schema + builder/validator tooling — the single source **for generated documentation** (graph = derivation of code+docs truth, never truth itself; fix-at-source law, hand-edits forbidden, deterministic byte-stable builds, 8 fatal invariants). **Third CHILD of PHASE_05**; gated on Phase 7 closed; manifest conversion deferred to Phase 9 (Phase 8 = read-only coverage proof); battery never runs by default (KG-D9); owner ratifies KG-D1..D9 | 🔒 [PHASE_08_KNOWLEDGE_GRAPH.md](PHASE_08_KNOWLEDGE_GRAPH.md) |
| 9 | Documentation Generation | Generate all machine-generated docs from knowledge_graph.json (graph = ONLY machine input): URL cards + features layer (mandatory) · summaries/indexes as KOS:GEN fences in existing canonicals (owner-activated) · **manifest-view conversion = the one battery-bearing sub-phase GEN-D**; deterministic byte-stable regeneration, write-fencing, hand-edit-in-fence = refuse+report, zero hard deletions, tool-death degradation. **Fourth CHILD of PHASE_05**; gated on Phase 8 closed; owner ratifies GEN-D1..D9 + the R6 date-field amendment | 🔒 [PHASE_09_DOCUMENTATION_GENERATION.md](PHASE_09_DOCUMENTATION_GENERATION.md) |
| 10 | UI Component Library | Census + certify + consolidate the existing UI vocabulary into a certified component library — NOT a redesign: one certified owner per pattern (compose-from-canon made total), owner-gated INERT consolidations under rule-of-3 (14b819b2 precedent), token registry as closed set, frozen-family firewall (Auth/Forms/Inputs/Select/Date/Financial); **UIL-D waves battery-bearing** (templates = code); a11y baseline + visual-regression method = Design Record (no repo standard exists); owner ratifies UI-D1..UI-D9 | 🔒 [PHASE_10_UI_COMPONENT_LIBRARY.md](PHASE_10_UI_COMPONENT_LIBRARY.md) |
| 11 | Development Dataset Architecture | DESIGN phase (documented-not-implemented): spec `DEV_DATASET_ARCHITECTURE.md` formalizing the organic dev dataset (3-PATTI worlds, Dev@12345 cast, golden journeys ₹801/₹344.25/₹633/₹225) — deterministic/idempotent/production-safe layers, **service-path seeding law (no raw fixtures into guarded tables — the seeder orchestrates chokepoints)**, stable natural handles replacing pk-references, 6-class scenario taxonomy incl. golden-value regression worlds, reset semantics + 4-factor production guard; zero code, battery never; owner ratifies DATA-D1..D9 | 🔒 [PHASE_11_DEVELOPMENT_DATASET_ARCHITECTURE.md](PHASE_11_DEVELOPMENT_DATASET_ARCHITECTURE.md) |
| 12 | Seeder Engine | Implement `seed_demo` / `seed_factory` / `seed_feature <x>` / `reset_demo` as a spec-faithful orchestration engine (the Phase-11 spec owns WHAT, this contract owns HOW): dev-only app registered ONLY in local settings (structural 5th guard factor) at a new topmost import-linter layer; guards-before-features; **service-path orchestration proven by a purity test (zero direct guarded-table writes — U8 compliance pinned)**; idempotent by natural handle; one atomic per world; scratch-DB law (primary dev DB never a target); golden-value scenarios; **first NEW-CODE phase — battery-bearing every wave, suite grows (D4 framework amendment)**; owner ratifies SEED-D1..D9 | 🔒 [PHASE_12_SEEDER_ENGINE.md](PHASE_12_SEEDER_ENGINE.md) |
| 13 | Verification / Smoke Test Engine | Implement `verify_demo`/`verify_factory`/`verify_feature <x>`/`verify_production`/`verify_all` — strictly READ-ONLY, deterministic (body-hash-stable reports), checks CODIFY certified invariants only (every check cites manifest-rule/spec/ADR/golden/CheckConstraint); guard-polarity matrix (dev-world commands refuse prod); production checks SELECT-only (no request cycle); DEV-contamination scan; **the permanent deployment-verification instrument (Phase-21 certificate cites a green verify_production report)**; app lives in BASE settings → flags the SEED-D6 assertions-home reconciliation (dated cross-contract amendment); battery-bearing every wave; owner ratifies VER-D1..D9 | 🔒 [PHASE_13_VERIFICATION_ENGINE.md](PHASE_13_VERIFICATION_ENGINE.md) |
| 14 | Automatic Knowledge Sync | `manage.py knowledge_sync` — **PURE DETECTOR** (never modifies code/docs/graph/manifests/generated outputs; a `--fix` flag must never exist): 8 drift domains (code⇄docs, code⇄graph, docs⇄graph, generated staleness, manifest, ownership/metadata, dataset-spec⇄seeder registry, verification-registry citations), every finding severity-classified (BLOCKER/WARN/INFO) + routed to its owning repair venue; extends-never-forks the P08 validator/P09 suite/P12-P13 registries; full-sweep + `--diff` + `--deep`; deterministic P13-convention reports; owner-selected battery guard subset. **FINAL CHILD of PHASE_05 — closes the 5→14 knowledge family**; owner ratifies SYNC-D1..D9 | 🔒 [PHASE_14_KNOWLEDGE_SYNC.md](PHASE_14_KNOWLEDGE_SYNC.md) |
| 15 | Business Operating Dashboard (BOD) | First NEW feature since the freeze — architecture frame + laws only, **product content (KPI catalog) = owner-supplied at BOD-0 via PDD change-control, never invented**: window-not-engine (aggregates only, zero business logic, zero writes — purity + zero-POST proven; read-only over frozen modules), metric-resolution ladder guarantees one authoritative owner per KPI (no second source of truth; step-2 additive read-functions individually owner-gated + INERT), money widgets ADR-0009/0011-compliant + U8-hostile wave, certification-grade permissions matrix, mobile summary-first from Phase-10 canon, zero models; owner ratifies BOD-D1..D9 | 🔒 [PHASE_15_BUSINESS_OPERATING_DASHBOARD.md](PHASE_15_BUSINESS_OPERATING_DASHBOARD.md) |
| 16 | Monthly Expense Engine | Recurring factory-expense automation implementing the future ADR-0011 reserved — factory-level ONLY, never per-Adda, never ledger/settlement-linked; **two campaign firsts: real U14 migration gate (new additive tables, per-migration owner approval BEFORE writing) + the first sanctioned dated addendum to the R5 Money-Write census** (generation = additive function INSIDE the expense-service family; UI/command layers write nothing); idempotent (template,period)-constrained generation with preview→confirm, append-only stands (wrong row = void+regenerate, no edit path ever); recurring catalog/amounts/cadence/policy = owner charter via PDD change-control (unanswered = blocked); money do-no-harm = ledger/golden/costing byte-checks; owner ratifies MEE-D1..D9 | 🔒 [PHASE_16_MONTHLY_EXPENSE_ENGINE.md](PHASE_16_MONTHLY_EXPENSE_ENGINE.md) |
| 17 | Raw Material → Expense Cost Integration | Connect roll cost truth to expense/cost reporting under an owner-chartered model (A read-only aggregation / B Costing-2 = the ADR-0009 Decision-2 formula ALREADY FIXED on record / C provenance-only materialization w/ full MEE-class gates); **one-rupee-once reconciliation = the signature proof (roll truth stays THE sole material record)**; honest-NULL end-to-end (Decision 5: NULL≠₹0, "material costing incomplete" statements mandatory); permission ruling RMX-D2 (aggregates default behind the FINANCIAL_ROLES wall, per-roll wall intact regardless); dual reserved-futures untouched (overhead + per-Adda factory expenses); period/valuation semantics = owner policy; owner ratifies RMX-D1..D9 | 🔒 [PHASE_17_RAW_MATERIAL_EXPENSE_COST_INTEGRATION.md](PHASE_17_RAW_MATERIAL_EXPENSE_COST_INTEGRATION.md) |
| 18 | Future Feature Documentation Updates | **The PERMANENT feature-documentation protocol** (owner designation; PHASE_04 precedent — the contract IS the protocol, pointed to from the Standard via dated amendment): lifecycle §6 = before-coding charter stage (PDD entry + contract + feature slug + scenario decision + impact pre-read) → during-coding U6-instrumented waves (diff-mode dispositions, fence discipline) → merge-equivalent gate (BLOCKER-clean) → feature-close (graph rebuild → regeneration → registers → certification sweep = docs-complete IS feature-DONE) + rollback-docs + ownership table; FIRST RUN = the 15–17 reality-sync, closing on the P14-defined condition (full sweep BLOCKER/WARN-clean or owner-accepted); one battery-bearing step (manifest regen); owner ratifies FFD-D1..D9 | 🔒 [PHASE_18_FUTURE_FEATURE_DOCUMENTATION_UPDATES.md](PHASE_18_FUTURE_FEATURE_DOCUMENTATION_UPDATES.md) |
| **18A** | **★ Release Certification Program (RCP)** | **PERMANENT stage (owner directive 2026-07-18, dated amendment — inserted WITHOUT renumbering; the 16–22 freeze holds):** the whole ERP certified as ONE integrated product in the browser before ANY deployment — phased campaign RC-0..RC-F (auth/RBAC → app-by-app → cross-app integration + E2E workflows → financial → UI/UX/responsive/a11y → data-integrity + perf observations → final certificate); per-phase loop verify→document→classify→fix(Phase-4)→re-verify→certify; no phase before the previous certifies. **AMENDS the Phase-20 entry gate: deployment FORBIDDEN until RC-F certifies (zero CRITICAL/MAJOR)**; P19 lists the RCP certificate among readiness inputs; P21 §6.1 evidence pack gains the RCP-certificate row (dated-amendment mechanism at those contracts' own gates). Design of record: [../RELEASE_CERTIFICATION_PROGRAM.md](../RELEASE_CERTIFICATION_PROGRAM.md); detailed contract authored at RC-0 after owner approval | ☐ design pending owner approval |
| 19 | Deployment Documentation | Docs-only: refresh the REAL owner-approved runbook (deploy/README.md, direction C single-VPS compose + restic DR, 2026-06-11) to campaign truth (new apps, devseed exclusion, 16/17 migrations, verify_production + sweep steps, flags-OFF statement) + the four checklists + rollback/release/ownership docs + a tabletop walkthrough vs the PHASE_20 contract; **surfaces the deployable-artifact tension (runbook `git clone` vs deploy-before-first-commit locked order) as DEP-D2 owner ruling**; deploy scripts read-only (executable code); owner ratifies DEP-D1..D9 | 🔒 [PHASE_19_DEPLOYMENT_DOCUMENTATION.md](PHASE_19_DEPLOYMENT_DOCUMENTATION.md) |
| 20 | Deployment | EXECUTION ONLY, runbook-verbatim (procedures live in ONE place — the runbook; the contract is the campaign wrapper): GO gate = the PHASE_21 §6.1 evidence pack freshly verified + **Phase 0 executed** + owner GO verbatim (single-use, voided by any stop/rollback) + final pre-deploy battery; provision → transfer per DEP-D2 → deploy → initial data per DEP-D3 → verify_production IN PROD + smoke + backup + **restore drill before worker credentials** → stabilization window; no live fixes EVER (defects → Phase-4 on dev side after clean stop/rollback); dev tree porcelain-proven untouched; owner ratifies PD-D1..D8 | 🔒 [PHASE_20_PRODUCTION_DEPLOYMENT.md](PHASE_20_PRODUCTION_DEPLOYMENT.md) |
| 21 | Deployment Readiness Certificate | The final attestation: **§6.1 = the 11-item evidence-pack SPEC that PD-0 assembles (spec-in-contract — no ordering paradox with 21 executing after 20)**; at execution every item freshly RE-VERIFIED at source (verify-never-trust; adjusting an input to green a row = the cardinal sin), open-items register (S6, R11, backlog residue, accepted WARNs — conscious deferrals only), verdict CERTIFIED / WITH-CONDITIONS / NOT-CERTIFIED + owner attestation verbatim; the certificate = a self-contained append-only evidence-cert and **the MANDATORY Phase-22 input**; owner ratifies CERT-D1..D5 | 🔒 [PHASE_21_DEPLOYMENT_READINESS_CERTIFICATE.md](PHASE_21_DEPLOYMENT_READINESS_CERTIFICATE.md) |
| 22 | First Git Checkpoint | The ONE commit (ends U2); requires Phase 0 decision honored + owner sign-off | ☐ |

Known cross-phase risks the future contracts must absorb:
- **KOS design record risk (phases 5–9): CLOSED 2026-07-12.** The surviving design core +
  audit findings are embedded in PHASE_05_DOCUMENTATION_FOUNDATION.md Appendix B; the label
  inconsistency is canonicalized as "KOS v3" (= "v3.1"), owner confirms at DOC-0 item R1.
  Residual risk: the full V1→V3 chat reasoning chain is unrecoverable — every reconstructed
  detail is `[PROPOSED]`-labeled and owner-ratified before DOC_STANDARDS.md is authored.
- **Worker-cert meta-audit evidence** lives only in memory (`project_v11_sprint_2026_07_12.md`),
  not in WORKER_ROLE_CERTIFICATION.md — flagged 2026-07-12. **ASSIGNED 2026-07-13 (Campaign
  Approval Pass): Phase 6 discovers/queues it (PHASE_06 dated amendment, §2.2 seed item 5);
  Phase 7 materializes it into WORKER_ROLE_CERTIFICATION.md.**
- **Phase 0 is a prerequisite gate for risk, not for order:** every session that changes files
  increases unsnapshotted work; owner should decide Phase 0 mechanism soon regardless of
  contract-authoring progress.

## Authoring cadence

One phase contract per session, owner-gated, in the order the owner requests (default: master
index order, Phase 0 next). Author = planning-capable model; each contract must be executable by
a different, weaker, or memory-less agent. After each contract: update this index, update the
status file, update memory (if available), STOP.
