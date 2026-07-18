---
id: docs-campaign-contracts-phase-06-documentation-discovery
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 6 Execution Contract — Documentation Discovery

> Authored 2026-07-12 under the contract-first directive. Inherits every universal invariant in
> [README.md](README.md) (U1–U14) **and — as the FIRST CHILD contract — every definition in the
> parent contract [PHASE_05_DOCUMENTATION_FOUNDATION.md](PHASE_05_DOCUMENTATION_FOUNDATION.md)**:
> the documentation philosophy, tier hierarchy T0–T8, the 20-type typology, layer
> responsibilities, mapping laws, ownership classes, lifecycle states, the 7-field metadata
> core, naming/linking conventions, KOS:GEN fence rules, validation dimensions, and the phase
> interface table (parent §6.1.1–§6.1.19). **None of that is restated here; this contract is
> deltas only.** Where this contract says "the Standard", it means `docs/DOC_STANDARDS.md` as
> frozen at Phase-5 close — the Standard wins over the parent's §6.1 defaults wherever the
> owner's R1–R12 answers amended them.
> Evidence doc (created at DOCDISC-0): `docs/DOCUMENT_DISCOVERY_REPORT.md`.

## 1. Phase objective

Perform the complete documentation census against the Standard and produce the authoritative
**discovery report** that drives Phase 7 (Cleanup). Every documentation artifact in scope is
inventoried, classified against the Standard, and every deviation becomes a typed finding in a
work queue — **and nothing is repaired, rewritten, moved, archived, deleted, or generated.**
Phase 6 is to the documentation corpus what a certification phase is to a role: evidence in,
verdict out, fixes elsewhere (Phase 7 = the documentation analog of Phase 4's implementation
protocol).

## 2. Scope

### 2.1 Census boundary (default — ratify at DD-1)

**In:** `docs/**` (496 md + 2 json at parent authoring; re-count at DOCDISC-0) · repo-root doc
companions (README, CHANGELOG, CLAUDE.md, GLOSSARY, SYSTEM_DESIGN, UI_COMPONENTS,
ABOUT_THIS_PROJECT) · code-adjacent app docs `config/<app>/README.md` ×9 + `core` ·
`deploy/README.md`. **In at family-level depth (ratify DD-2):** `docs/AI_PATTERN_INTELLIGENCE/`
(104 md — has its own DOC_CLEANUP_REPORT + archive era) and `docs/archive/` (104 md — indexed
for completeness, contents never judged for staleness: archive is history by definition,
parent §6.1.12). **Out:** `.claude/` (tooling, Phase-14 input) · `env/`, `media/`, application
code/templates (docstrings are code, not docs) · agent memory files (the audit's "41 broken
docs-links in memory" is a memory-maintenance note recorded in the report appendix, not census
scope — repo docs must stand without memory, parent §6.1.8).

### 2.2 Seeded inputs (discovery starts from these, re-verifies, then extends)

1. Parent Appendix **B.2** (2026-07-11 audit findings) + **B.3** (9-item fresh drift register)
   — every item re-verified and carried into the typed registers.
2. [DOCUMENT_ARCHIVE_REVIEW.md](../DOCUMENT_ARCHIVE_REVIEW.md) (2026-07-11, family-level
   KEEP/SUPERSEDED/ARCHIVE/REMOVE-LATER) — the archive-candidate baseline; DOCDISC-E reconciles
   per-file against it (newer evidence wins, divergence noted per row).
3. Backlog **#6** (RBAC.md role-table drift) and the pre-logged patterns_ai README drift
   (status-file carry-over) — enter the stale register with their certification citations.
4. The Standard's own §6.2-register + Phase-5 evidence (what was checked at DOC-1) — Phase 6
   does not re-litigate the Standard; it applies it.

### 2.3 In / out (activity)

**In:** counting, reading, classifying, cross-referencing, register-building, work-queue
authoring. Mechanical censuses (file counts, link resolution, naming-pattern matching,
frontmatter presence) MAY be scripted read-only from the scratchpad; **every judgment call
(stale / wrong-canonical / duplicate / archive-candidate) is main-thread with per-item
evidence** (U7 applied to docs). **Out:** every repair (even a one-character broken link — it
becomes a finding); `canonical_manifest.json` stays untouched AND unedited-around (read-only
reference audit only; its refresh is Phase-7's battery-bearing item, parent §6.1.19);
knowledge-graph construction (Phase 8); generation (Phase 9); DOC_STANDARDS amendments (owner
change-control per the Standard's own amendment section).

## 3. Success criteria

Phase 6 is DONE when ALL hold:
1. `docs/DOCUMENT_DISCOVERY_REPORT.md` exists with ALL output artifacts (§8) as sections:
   full census · ownership matrix · link audit · duplicate register · orphan register ·
   archive-candidate register · generation-candidate register · Phase-7 work queue.
2. **Complete coverage with arithmetic:** every file inside the DD-1 boundary appears in the
   census exactly once, with tier + type + ownership class + lifecycle state assigned (or the
   finding "unassignable → typed finding"); census total reconciles against a mechanical
   file-count of the boundary (counts shown).
3. Every finding carries exactly one class from §6.1, its evidence (file:line / link target /
   citation), and a proposed Phase-7 action + risk flag — no unclassified deviations.
4. Every §2.2 seeded item is re-verified and disposed (confirmed-into-register / stale-seed /
   already-resolved), none silently dropped.
5. Zero mutations: no file in the boundary was modified (report + §9 allowlist excepted) —
   the report itself and index rows are the phase's only writes.
6. The Phase-7 work queue is ordered, risk-flagged (battery-bearing items marked — manifest
   refresh class), and countersigned by the DOCDISC-G completeness census.
7. Status file + memory synced at every sub-phase close; battery baseline untouched and NOT
   re-run.

## 4. Rules of engagement (deltas beyond U1–U14 + parent)

- **Discovery only — the repair impulse is a stop-class temptation.** A discovered defect,
  however trivial, is a register row (parent §4 "register, don't fix", tightened: this phase
  exists to build the register).
- **Execution gate:** DOCDISC-0 refuses to proceed unless `docs/DOC_STANDARDS.md` exists with
  lifecycle status `frozen-v1` (Phase 5 closed). Measuring against an unfrozen standard
  certifies against sand.
- **Classification is single-class:** a file with multiple deviations gets multiple findings
  (one per class), never a merged blob — Phase 7 works findings, not essays.
- **Archive contents are exempt from staleness** (they are point-in-time by definition); they
  are audited ONLY for index-completeness and banner-presence (parent §6.1.12 rules).
- Frozen truth-locks (T1) are audited for reference-integrity ONLY — their content is never a
  finding (change control = ADR/owner, parent §6.1.7).
- Scripted censuses: read-only, run from the scratchpad, script + raw output preserved as
  evidence; scripts never write inside the repo.

## 5. Evidence standard

- Every census number carries its command + raw count (Phase-0 §5 pattern applied to docs).
- Every finding row: file path · class · evidence (quoted line / dead target / conflicting
  citation pair) · Standard clause it violates (§-reference into DOC_STANDARDS.md) · proposed
  Phase-7 action · risk flag.
- Judgment findings (stale/duplicate/wrong-canonical) additionally quote BOTH sides (the doc's
  claim vs the certified/current truth with its citation).
- Link audit: every checked link's disposition (ok / dead / wrong-anchor / points-to-archive /
  points-to-superseded) — mechanical output attached, exceptions hand-verified.
- Sub-agent sweeps supplemental (U7): a surface is "clean" only after main-thread spot-checks
  of the sweep's method + a sample; finder failures recorded in the report.

## 6. Methodology

### 6.1 Finding classification (normative for Phases 6–7)

Mapped onto the parent's validation dimensions (§6.1.17) — one class per finding:

| Class | Definition (Standard clause it tests) |
|---|---|
| **Missing** | a doc the mapping laws or typology require, absent (URL/model/service/view coverage §6.1.10; app-layer pairs §6.1.4; PAGES backlog class) |
| **Duplicate** | same topic answered authoritatively in 2+ places without one being canonical (one-canonical-per-topic §6.1.1-P3) |
| **Stale** | content contradicts current code/certified truth, or superseded-in-fact without banner (drift=bug §6.1.1-P2; age alone ≠ stale) |
| **Broken link** | link/anchor resolves nowhere (linking §6.1.15) |
| **Wrong canonical source** | an index/manifest/guide routes a topic to a non-canonical or superseded doc (B.3 item 2 class) |
| **Wrong ownership** | doc's actual maintenance pattern contradicts its ownership class, or OWNERSHIP_MATRIX row absent/wrong (§6.1.11) |
| **Wrong tier** | doc claims/receives a hierarchy position conflicting with the T0–T8 rules (§6.1.2) |
| **Wrong metadata** | frontmatter absent/incomplete/invalid **per the R2-ratified adoption rule** (retrofit-scope docs lacking the 7 fields = work-queue rows, not violations, until Phase 7 retrofits) |
| **Archive candidate** | active-tree doc whose job is done (receipt/superseded/dead plan) — reconciled with DOCUMENT_ARCHIVE_REVIEW families |
| **Generation candidate** | handwritten content the Standard designates generated/hybrid (structural tables, indexes, URL knowledge — §6.1.16 structural-only law) |
| **KOS violation** | any other breach of a Standard clause (naming style ×5th, AI-only truth, memory-only record, fence misuse once fences exist) — always with the clause cited |

### 6.2 Discovery targets → sub-phase map

The owner-mandated targets land as follows: canonical documents + hierarchy + ADR coverage +
canonical_manifest references → DOCDISC-B · application guides + README hierarchy + ownership
+ metadata + naming → DOCDISC-A/C · indexes + cross-links + orphans + PKALS/PROJECT_BRAIN/
AI_AGENT_GUIDE consistency → DOCDISC-D · archive structure + duplicates + archive candidates →
DOCDISC-E · generated documents + KOS:GEN boundaries + generation candidates + documentation-
graph readiness → DOCDISC-F.

## 7. Sub-phase breakdown

Every sub-phase: one session, STOP after (U3); all writes = report sections + §9 allowlist;
rollback for every sub-phase = delete/revert the report section drafted this session (report
is append-only once a section closes); battery NEVER runs (no code is touchable, §10).

| # | Scope · Inputs · Outputs · Evidence · Stop deltas |
|---|---|
| **DOCDISC-0** — Charter + inherited-standard validation | **Scope:** verify the execution gate (DOC_STANDARDS.md exists, status `frozen-v1`, entry-points wired — Phase-5 §3 criteria spot-checked); re-verify parent §2.1 landscape facts (counts, manifest version, pkals_v2 presence); owner ratifies DD-1 (boundary) + DD-2 (AI_PATTERN_INTELLIGENCE depth); create report skeleton with section stubs + the seeded-inputs table (§2.2). **Inputs:** the Standard, parent contract, §2.2 seeds. **Outputs:** report skeleton + filled Design Record + boundary file-count baseline. **Evidence:** gate proof (Standard's metadata block quoted); count commands + numbers. **Stop:** gate fails (Phase 5 not closed) → report and stop; DD-1/DD-2 unanswered. |
| **DOCDISC-A** — Repository documentation census | **Scope:** one census row per file in the boundary: path · tier · type (20-type typology) · ownership class · lifecycle state · naming style · size/date; per-directory rollups; naming-convention conformance (files outside the codified styles = KOS-violation findings); metadata presence census (expected ≈0 pre-retrofit — recorded, classed per R2 rule). **Inputs:** DD-1 boundary + Standard typology. **Outputs:** census section + first findings (unassignable-type, wrong-tier candidates, naming violations). **Evidence:** mechanical inventory attached; every judgment-assigned tier/type spot-justified for non-obvious cases. **Stop:** boundary drift vs DOCDISC-0 count unexplained. |
| **DOCDISC-B** — Canonical hierarchy verification | **Scope:** one-canonical-per-topic audit (topic list = canonical_manifest topics + DOCUMENTATION_INDEX sections + Standard tier-2 set); wrong-canonical + duplicate findings; T0–T8 assignment verification against the conflict rules; **ADR coverage:** every locked decision referenced by docs has its ADR/truth-lock home (decisions living only in prose = findings); **canonical_manifest reference audit (READ-ONLY):** all 17 topics' targets resolve + still canonical, staleness gaps enumerated (known: missing machines/patterns_ai/PDD topics — B.2), never edited. **Inputs:** census + manifest + index + Standard. **Outputs:** hierarchy-verification section + duplicate/wrong-canonical/wrong-tier registers begun. **Evidence:** per-topic canonical trace (topic → routed doc → verdict). **Stop:** a T1 truth-lock CONTENT conflict surfaces (truth-lock contradiction = report to owner, framework conflict rule — not a Phase-7 queue item). |
| **DOCDISC-C** — Ownership + metadata audit | **Scope:** per-census-row ownership verification vs OWNERSHIP_MATRIX (+ matrix completeness itself — rows for new docs since 2026-06-13); wrong-ownership findings; append-only/frozen-class docs checked for post-close edits (report-only); metadata audit per the R2-ratified adoption rule → retrofit work-queue rows (file + which of the 7 fields derivable mechanically vs needing judgment). **Inputs:** census + OWNERSHIP_MATRIX + Standard §metadata. **Outputs:** ownership-matrix section (verified + gaps) + metadata register. **Evidence:** matrix-diff table. **Stop:** none beyond standard. |
| **DOCDISC-D** — Cross-link + navigation audit | **Scope:** full link audit across active-tree docs (mechanical resolution + hand-verified exceptions); orphan register (docs unreachable from DOCUMENTATION_INDEX or a parent index — parent §6.1.15 no-orphans law); navigation-consistency audit of the three routing layers: PKALS (PROJECT_ATLAS vs subdirs), PROJECT_BRAIN (5 indexes vs reality — FEATURE_INDEX especially, as the features/ seed), AI_AGENT_GUIDE (README table vs manifest vs actual canonicals — B.3 items 1/2/9 re-verified here); DOCUMENTATION_INDEX + START_HERE completeness. **Inputs:** census + B.3. **Outputs:** link-audit section + orphan register + navigation-consistency findings. **Evidence:** link-checker script + raw output preserved; per-orphan reachability trace. **Stop:** none beyond standard. |
| **DOCDISC-E** — Duplicate / orphan / archive discovery | **Scope:** consolidate duplicates (from B + D) into the duplicate register with canonical-survivor proposals; archive-candidate register: per-file reconciliation against DOCUMENT_ARCHIVE_REVIEW families (agree/extend/contradict — newer evidence wins, divergences listed); superseded-without-banner census; archive-tree audit: index completeness (12 rows vs 104 files baseline), banner presence (42/104 baseline), the broken ARCHITECTURE.md pointer (B.3 item 5); REMOVE-LATER rows carried verbatim (deletion stays owner-gated, never a Phase-7 default). **Inputs:** registers so far + DOCUMENT_ARCHIVE_REVIEW. **Outputs:** duplicate + archive-candidate registers final; archive-integrity findings. **Evidence:** per-family reconciliation table. **Stop:** contradiction with DOCUMENT_ARCHIVE_REVIEW that changes a KEEP-family disposition → flag for owner in the report (don't silently overrule a reviewed KEEP). |
| **DOCDISC-F** — Generation readiness audit | **Scope:** generation-candidate register (handwritten structural content the Standard marks generated/hybrid: URL_ATLAS tables, GUIDE file-tables, index tables, COVERAGE_REPORT — each with its future KOS:GEN boundary sketched, section-level, no fences written); **graph readiness** for Phase 8: mapping-law coverage censuses (URLs vs URL_ATLAS rows vs future cards; models vs README/DATABASE_GUIDE rows; services vs GUIDE/CHOKEPOINTS — known gap: history_service page, B.3 item 4; views vs PAGES backlog), FEATURE_INDEX → features/-taxonomy seed extraction readiness (R3), canonical_manifest → graph-view migration notes (R5 answer applied, CI-guard constraints listed for Phase 7/8); existing generated-ish artifacts inventoried (manifest json, COVERAGE_REPORT) with their current update mechanism. **Inputs:** census + Standard mapping laws + R3/R5 answers. **Outputs:** generation-candidate register + graph-readiness section (Phase-8's §2 facts, pre-built). **Evidence:** coverage arithmetic per mapping law (counted, not asserted). **Stop:** none beyond standard. |
| **DOCDISC-G** — Final report + Phase-7 handoff | **Scope:** assemble classification totals (findings per class, per directory); completeness census (every boundary file rowed once — arithmetic; every seeded input disposed; every register cross-footed); build the **Phase-7 work queue**: ordered rows (finding → proposed action → owning register → risk flag: docs-only vs battery-bearing [manifest refresh class] vs owner-gated [REMOVE-LATER, truth-lock adjacent]); write the handoff statement (what Phase 7 may do without further discovery, what needs owner input); PHASE-6 VERDICT (census-complete / census-complete-with-blockers). **Inputs:** everything. **Outputs:** final report; status file Phase-6 row → ✅. **Evidence:** the arithmetic. **Stop:** unaccounted file/finding at the completeness census → back to the owning sub-phase as a dated amendment. |

## 8. Deliverables

All as sections of **`docs/DOCUMENT_DISCOVERY_REPORT.md`** (single evidence-doc pattern —
certification precedent; no register scatter): document census · ownership matrix (verified +
gaps) · link audit · duplicate register · orphan register · archive-candidate register ·
generation-candidate register · graph-readiness section · classification totals · **Phase-7
work queue** · seeded-inputs disposition table · memory-links appendix note (§2.1). Plus the
filled Design Record (Appendix A) and status/memory updates per sub-phase.

## 9. Files expected to change

**Docs only:** `docs/DOCUMENT_DISCOVERY_REPORT.md` (NEW at DOCDISC-0 — the phase's only new
file) · `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` · `docs/DOCUMENTATION_INDEX.md` (report row at
DOCDISC-0) · this file (Design Record + dated amendments only) · memory files (if agent has
memory). **Scratchpad:** read-only census scripts + raw outputs (outside the repo; preserved
as evidence attachments quoted into the report). Nothing else — explicitly NOT
DEPLOYMENT_BACKLOG (doc findings live in the report/work queue, not the code backlog; a
discovered CODE defect, if any, is the only backlog-eligible event and follows U12).

## 10. Files that must never change (touching one = STOP + report)

- Every file inside the census boundary except the §9 allowlist — the census OBSERVES the
  corpus; a mutated corpus invalidates its own census (Phase-0 §10 tree-sanctity analog).
- `canonical_manifest.json` (CI-guarded; Phase-7 battery-bearing item) — read-only here.
- `docs/DOC_STANDARDS.md` (frozen at Phase-5 close; amendments = owner change-control only).
- All application code/tests/migrations/templates/settings; `.git` state (U2); the 2 stashes.
- `docs/archive/**` contents (indexed, never edited here — banners are Phase-7 work).

## 11. Documentation update rules

At every sub-phase close, same session: (a) report section appended (closed sections never
edited; corrections = dated amendments); (b) status-file Phase-6 sub-phase row + dashboard
(docs-sync, memory-sync; battery row untouched — no code) + "Next action"; (c) DOCUMENTATION_
INDEX row for the report at DOCDISC-0; (d) U6 app-doc lookups N/A throughout (no code changes
— stated once in the report, not per-file).

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-6
bullet: sub-phase closed, headline counts, report pointer) + MEMORY.md index line at each
sub-phase close. Agents without memory: skip — the report + status file are the complete
binding record (parent §6.1.8: nothing binding lives only in memory).

## 13. Battery policy

**Never runs in this phase.** No code change is possible under §10; the census is read-only.
Baseline (status-dashboard value; 1526/1526 at authoring) is untouched and NOT re-verified
here. The one docs-file with a test surface (canonical_manifest.json) is §10-frozen precisely
to keep this policy true (parent §13 guard note, inherited).

## 14. Regression policy

- The only regressions this phase can cause: corpus mutation (guarded by §10 + a DOCDISC-G
  spot-check: mechanical re-count + mtime sample vs DOCDISC-0 baseline, shown in the report)
  and misclassification (guarded by §5 per-finding evidence + single-class rule).
- Certified truths are inputs, never re-litigated: a doc contradicting a certification is a
  STALE finding against the DOC — the certification stands (evidence-doc-wins conflict rule).
- No pins, no tests (U4 vacuously satisfied).

## 15. Rollback policy

- The report is the only artifact: a bad session's section is deleted/redrafted before close;
  closed sections are append-only (corrections dated).
- Scratchpad scripts/outputs are disposable; re-runs are idempotent (read-only).
- A wrong Design Record answer is amended as a dated row, never edited in place.
- Session crash: next session re-runs the mechanical baseline count first; a drifted corpus
  (files changed by non-campaign activity) → stop condition §16.6 before continuing the census.

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. Execution gate fails at DOCDISC-0: DOC_STANDARDS.md absent / not `frozen-v1` / Phase-5
   success criteria visibly unmet.
3. DD-1/DD-2 unanswered at DOCDISC-A start.
4. Repair temptation materializes as a write: ANY corpus file would be modified (§10).
5. A T1 truth-lock content conflict, or evidence contradicting a CLOSED certification —
   report, never reconcile/reopen unilaterally.
6. Corpus drift mid-phase (boundary count/mtime baseline diverges without a campaign
   explanation) — re-baseline decision belongs to the owner.
7. A discovered CODE defect (docs said X, code does Y, and code is wrong) — that is a
   certification-class finding: record it, route it per U12 to the backlog as an observation,
   and if it is money-adjacent, U8 applies (stop + report).
8. The report contradicts DOCUMENT_ARCHIVE_REVIEW on a KEEP-family disposition (§7 DOCDISC-E).

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-6 row: which DOCDISC-* is next.
2. Read `docs/campaign_contracts/README.md` (U1–U14 + environment) → the PARENT contract
   [PHASE_05_DOCUMENTATION_FOUNDATION.md](PHASE_05_DOCUMENTATION_FOUNDATION.md) FULLY (its
   §6.1 definitions are this phase's measuring stick) → `docs/DOC_STANDARDS.md` (the ratified
   Standard — it wins over parent defaults) → this contract.
3. Read `docs/DOCUMENT_DISCOVERY_REPORT.md` if it exists (absent ⇒ next work = DOCDISC-0):
   closed sections, Design Record state, the DOCDISC-0 baseline counts.
4. Re-verify read-only: the execution gate (Standard present + frozen-v1); boundary file count
   vs the DOCDISC-0 baseline (drift → §16.6); git HEAD vs status file.
5. No app login, no passwords, no dev server needed (docs-only phase).
6. Execute exactly ONE sub-phase per §7. STOP per §16.
7. Anything internally inconsistent across status file / Standard / parent / this contract /
   report → report before continuing (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (DOCDISC-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| DD-1 | Census boundary | §2.1 as written: docs/** + root companions + config/<app>/README.md + deploy/README.md; excludes .claude/, code docstrings, agent memory | **ACCEPT DEFAULT** (owner 2026-07-13, verbatim: "Use the census boundary exactly as defined in the contract: docs/**, the 7 root companion documents, the 10 application READMEs, deploy/README.md. Do not expand or reduce the boundary.") |
| DD-2 | AI_PATTERN_INTELLIGENCE + archive depth | Family-level census (per-file rows, but staleness judgment at family granularity, mirroring DOCUMENT_ARCHIVE_REVIEW's method) — full per-file judgment only where a family is mixed | **ACCEPT DEFAULT** (owner 2026-07-13, verbatim: "Evaluate AI_PATTERN_INTELLIGENCE and archive/ at the family level, performing per-file analysis only where a family is mixed.") |
| DD-3 | Staleness threshold | Stale = contradicts current code/certified truth OR superseded-in-fact without banner; age/date alone never qualifies (drift=bug, not old=bad) | **ACCEPT DEFAULT** (owner 2026-07-13, verbatim: "A document is stale only if it contradicts the current code, certified truth, or has been superseded without the required banner. Age alone must never classify a document as stale.") |

Date · answered by: **2026-07-13 · Owner (Umesh) — "I ACCEPT THE DEFAULTS exactly as defined by the Phase 6 contract." Same order re-binds the Single-Canonical-Home clarification (dated amendment above) onto every discovery finding, and gates this session to DOCDISC-A ONLY.**

## Dated amendments

- **2026-07-13 (owner clarification #6, pre-DOCDISC-F — KNOWLEDGE-LEVEL GRAPH READINESS):**
  scope-preserving, binding DOCDISC-F only. (a) Graph-readiness distinguishes FIVE strata —
  documentation artifacts · knowledge domains · business capabilities · technical
  capabilities · implementation artifacts — and evaluates whether future graph nodes can
  exist at the KNOWLEDGE level (business domains · features · workflows · user journeys ·
  permissions · URLs · views · services · models · tables · calculations · integrations ·
  ADR decisions · implementation guides · certification evidence), not only the file level.
  (b) Every generation candidate gets an 8-field determination: source of truth ·
  mechanically derivable? · human judgment required? · one-time vs repeatable · future graph
  node? · future graph edge? · feature-card input? · owning phase. (c) Discovery only — no
  graphs/cards generated, no rewrites, no manifest edits, no cleanup, **no new architecture**
  (knowledge-level gaps are recorded as KG-0/GEN-0 ratification INPUT for the Phase-8/9
  Design Records, never decided here).
- **2026-07-13 (owner clarification #5, pre-DOCDISC-E — KOS-IMPACT ENRICHMENT):**
  scope-preserving, binding DOCDISC-E only. (a) Every finding SURVIVING Phase 6 gains a
  **KOS impact evaluation** with 10 fields: affected knowledge domain · future Knowledge Hub
  · navigation impact · ownership impact · graph impact · feature-card impact · AI navigation
  impact · human navigation impact · cleanup priority · future resolving phase — explaining
  WHY its resolution strengthens the future KOS, not merely what to clean. (b) **Exactly-one
  owning-phase rule:** every surviving finding must carry exactly ONE future resolving phase
  (earlier phases may contribute analysis; one phase RESOLVES) — no finding may become orphan
  work after Phase 6 closes. (c) Discovery only — no cleanup/consolidation/rewrites/moves/
  archiving/lifecycle changes/manifest edits. (d) **Verdict-timing note (contract-exact
  execution of the owner order):** the order requests "the complete Phase 6 reconciliation
  and final Phase 6 verdict" at E; the frozen contract places the FINAL phase verdict at
  DOCDISC-G, after DOCDISC-F's generation-candidate + graph-readiness outputs (§3.1, §7).
  E therefore delivers the COMPLETE findings reconciliation + enrichment + the E-scope
  verdict; the phase-final verdict remains G's deliverable — recorded here so the
  discrepancy is disposed, not silently resolved.
- **2026-07-13 (owner clarification #4, pre-DOCDISC-D — NAVIGATION QUALITY, four personas):**
  scope-preserving strengthening of DOCDISC-D, binding for this sub-phase only. In addition
  to the contract-defined link/orphan/routing-consistency audit: (a) navigation evaluated
  from four independent user perspectives — new developer · AI agent · business owner ·
  experienced maintainer — across ALL routing systems (START_HERE · PROJECT_KNOWLEDGE_MAP ·
  PROJECT_BRAIN · PKALS · AI_AGENT_GUIDE · DOCUMENTATION_INDEX · app READMEs · canonicals ·
  truth-locks); entry points must lead to correct canonical knowledge without unnecessary
  branching, circular navigation, dead ends, or contradictory paths; (b) deficient paths =
  findings with 6 mandatory fields (affected path · audience · current chain · recommended
  future chain · why cognitive load increases · owning phase); (c) **bidirectional check per
  major business domain**: Business → Feature → Implementation AND Implementation →
  Business; (d) hub-realism verification: can every DOCDISC-B/C future Knowledge Hub become
  its domain's primary navigation center WITHOUT violating truth-lock precedence (unchanged).
  Discovery only — no redesign, no rewrites, no consolidation, no moves, **no link repairs**.
- **2026-07-13 (owner clarification #3, pre-DOCDISC-C — KNOWLEDGE-DOMAIN OWNERSHIP):**
  scope-preserving strengthening of DOCDISC-C evaluation, owner verbatim core: "The objective
  is to create one complete knowledge home for every business domain … evaluate ownership
  from a knowledge-domain perspective rather than only a document perspective." Effect:
  (a) DOCDISC-C additionally evaluates, per business DOMAIN, whether a clearly-defined
  knowledge owner exists that can become the domain's single navigation hub, considering the
  29 owner-listed knowledge aspects (purpose · vocabulary · workflow · user journeys ·
  permissions · URLs · views · forms · templates · APIs · services · models · tables ·
  relationships · state machines · workflows · business rules · calculations · background
  jobs · integrations · ADRs · implementation guides · learning material · certification
  evidence · historical decisions · related features · roadmap · testing strategy ·
  operational guidance); (b) fragmented domain ownership without one authoritative future
  home = a discovery finding with 5 mandatory fields (domain · current locations ·
  recommended future owner · why fragmentation hurts navigation · resolving phase);
  (c) hub-structural capability re-checked at domain grain; (d) **truth-lock hierarchy
  unchanged — hubs stay subordinate to ADRs/PDD/ARCHITECTURE_V2/MANUFACTURING_V1_FREEZE**;
  (e) explicitly NO redesign/rewrite/consolidation/moves/manifest edits/new canonicals —
  findings strengthen Phases 8–9 discovery input only.
- **2026-07-13 (owner clarification #2, pre-DOCDISC-B — CANONICAL = FUTURE NAVIGATION HUB):**
  scope-preserving strengthening of the DOCDISC-B evaluation criteria, owner verbatim core:
  "The goal is a true Knowledge Operating System where every business topic has exactly one
  canonical home. That canonical home must become the navigation hub for the complete
  knowledge graph of that topic." Effect: DOCDISC-B assesses every canonical-topic candidate
  BOTH for correct-canonical status AND for **future-hub capability** — whether it can
  naturally connect to the 22 owner-listed dimensions (business purpose · workflow · feature
  ownership · app ownership · URLs · views · templates · APIs · services · models · DB tables
  · state machines · permissions/roles · signals · background jobs · business rules · ADRs ·
  implementation docs · learning docs · related features · tests · certification evidence ·
  future roadmap). An unsuitable current canonical = a discovery finding (registered, never
  redesigned/moved/rewritten in Phase 6). Alignment note: this operationalizes what Phases
  8–9 build (graph + cards + features layer = the navigation fabric); hub-capability findings
  feed the Phase-8 graph design and Phase-9 generation targets, not just Phase-7 cleanup.
- **2026-07-13 (owner clarification, post-DOCDISC-0 — SINGLE-CANONICAL-HOME OBJECTIVE):**
  standing architectural objective for Phase 6 and ALL later KOS phases, owner verbatim: "My
  long-term goal is that documentation should eventually have a single canonical home. I do
  NOT want the same knowledge permanently scattered across multiple locations." Operational
  effect (a tightening, not a scope change — operationalizes Standard §1.3
  one-canonical-per-topic): (a) Phase 6 stays discovery-only (no moves/merges/rewrites/
  deletes); (b) **every Duplicate/fragmentation finding row MUST additionally record: current
  locations · recommended canonical location · why consolidation benefits · which cleanup
  phase performs it** (extends the §5 "proposed Phase-7 action" field for that class);
  (c) Phase 7 consolidates into approved canonical homes per the work queue — no duplicate
  LIVING documentation survives cleanup; (d) KOS end-state acceptance idea: a developer/AI
  starts from one canonical document and navigates to every related URL, model, table,
  business rule, ADR, and implementation detail without searching disconnected documents
  (graph/cards/features layer = the navigation fabric, Phases 8–9). DD-1..DD-3 remain
  UNANSWERED by this clarification — DOCDISC-A still gated (§16.3).
- **2026-07-13 (Campaign Approval Pass, owner-ordered):** §2.2 seeded inputs gain item 5 —
  **the Worker-Certification meta-audit evidence** (framework README risk #2: its detail
  survives only in agent memory, not in WORKER_ROLE_CERTIFICATION.md). DOCDISC-A additionally
  registers this as a `Missing`-class finding against WORKER_ROLE_CERTIFICATION.md, and the
  Phase-7 work queue carries its materialization (an appended evidence section in that doc,
  sourced from the certified verdict + whatever memory detail remains recoverable at
  execution; unrecoverable detail is honestly marked as such). Ownership assigned: Phase 6
  discovers/queues it; Phase 7 materializes it.

# Evidence note

All discovery evidence lives in `docs/DOCUMENT_DISCOVERY_REPORT.md` (created at DOCDISC-0),
not in this contract — contract = procedure, report = what was found (framework hierarchy
rule). The report is Phase 7's sole work-source: Phase 7 executes the work queue and returns
to discovery ONLY via a dated Phase-6 amendment (no silent re-discovery during cleanup).
