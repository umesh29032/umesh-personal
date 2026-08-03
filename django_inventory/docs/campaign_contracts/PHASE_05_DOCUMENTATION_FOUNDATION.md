---
id: docs-campaign-contracts-phase-05-documentation-foundation
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 5 Execution Contract — Documentation Foundation (KOS)

> Authored 2026-07-12 under the contract-first directive. Inherits every universal invariant in
> [README.md](README.md) (U1–U14) — this contract only adds phase specifics and tightenings.
> **This is the PARENT CONTRACT for all later documentation phases.** Phases 6 (Discovery),
> 7 (Cleanup), 8 (Knowledge Graph), 9 (Generation), 14 (knowledge_sync), 18 (Future Feature
> Documentation Updates) and 19 (Deployment Documentation) inherit the definitions in §6 of this
> contract exactly as all contracts inherit U1–U14 from the framework README; their contracts
> state only deltas. Phases 10–17 and 20–22 are bound by §6 wherever they produce or modify
> documentation.
> **This contract EMBEDS the surviving KOS design record (Appendix B)** — the owner-frozen
> "Version 3" design previously lived only in chat history plus one agent-memory summary
> (framework README, "Known cross-phase risks"). From this file's existence onward, the design
> core is on-disk and the memory dependency is dead. Executable by Claude, GPT, Gemini, or a
> human engineer with no chat history.
> **Authoring ≠ execution.** This session created only this contract. `DOC_STANDARDS.md` does
> NOT exist yet; it is created at Phase-5 EXECUTION (owner-ordered), per §7.

## 1. Phase objective

Materialize the owner-frozen KOS (Knowledge Operating System) design as
**`docs/DOC_STANDARDS.md`** — the documentation constitution of the project: philosophy,
hierarchy, document typology, layer responsibilities, code→doc mapping laws, ownership,
lifecycle, metadata, naming, linking, generated-vs-handwritten rules, validation philosophy, and
the interface every later phase (6–22) has with documentation.

**Why this phase exists and why it is a foundation:** the campaign's own operating premise is
that any session — any AI, any account, zero chat history — resumes from documentation alone.
That premise currently rests on 496 markdown files accreted across five overlapping systems
(root topic docs, PKALS/LEARNING_2_0, app README+GUIDE pairs, PAGES contracts, ADRs) with four
naming styles, zero metadata, a stale machine manifest, and a broken archive index. Phases 6–9
(census → cleanup → graph → generation) cannot run without a standard to measure against; this
phase writes that standard. It builds NOTHING else: no census, no cleanup, no cards, no graph,
no tooling.

## 2. Scope

### 2.1 Measured documentation-landscape facts (2026-07-12 — re-verify at execution, §17.4)

| Fact | Value |
|---|---|
| docs/ size | **496 md files** (392 active + 104 in docs/archive/); root-level ≈125; adr 12 (ADRs 0001–0011 + index) · AI_PATTERN_INTELLIGENCE 104 · apps 11 (10 GUIDEs + index) · audit_phases 11 · campaign_contracts 3 · LEARNING 11 · LEARNING_2_0 97 · PAGES 2 · pkals_v2 5 · production 10 · tracking 1. (Docs-architecture audit of 2026-07-11 counted 490; +6 = campaign docs since — normal authoring drift) |
| Metadata | **0 of 496 files carry YAML frontmatter.** The KOS 7-field metadata core is a greenfield decision (→ Design Record R2) |
| Naming styles | 4 coexisting: ALL_CAPS topic (364) · dated `*_2026_MM_DD` (46) · `PHASE_*` (14) · lowercase_snake flow/page files (41); plus `NN_TOPIC.md` lessons and `NNNN-kebab` ADRs |
| Machine index | `docs/LEARNING_2_0/AI_AGENT_GUIDE/canonical_manifest.json` — task→canonical-doc router, version **2026-06-13 (stale: 17 topics; predates PDD freeze, machines, patterns_ai, R10/OP-1)**; **CI-guarded by `core.tests.PkalsNavigationGuardTests` (a dead path fails the build)** — this is why the manifest is UNTOUCHABLE in Phase 5 (§10, §13) |
| Existing doc systems | DOCUMENTATION_INDEX + START_HERE (persona routing; "PROJECT_KNOWLEDGE_MAP wins overview conflicts") · PKALS/LEARNING_2_0 13 layers (AI_AGENT_GUIDE, LIVING_DOCUMENTATION_SYSTEM = PKALS-LIVE drift-is-a-bug + CHANGE_IMPACT_MATRIX + OWNERSHIP_MATRIX, PROJECT_BRAIN incl. FEATURE_INDEX, DATA_FLOWS 9 flows, REQUEST_JOURNEYS 16-section template 3/12 written, CHOKEPOINTS 6 pages, URL_ATLAS, APPS, DATABASE_GUIDE, DJANGO_GUIDE, ARCHITECTURE_EXPLAINED/VALIDATION) · app two-layer README(business/Hinglish dual-register)+GUIDE(file-by-file map, ★ chokepoint marker) ×10 apps · PAGES 10-section per-page contracts (1 exemplar + backlog) · ADRs (Status·Context·Decision·Consequences, append-only, supersede-not-rewrite) · receipts (plan-becomes-receipt `*_EXECUTION_PLAN.md` + standalone `*_RECEIPT_YYYY_MM_DD.md`) · archive with `> **ARCHIVED <date>**` banner convention |
| Features layer | **`docs/features/` does NOT exist.** Nearest precursor: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (feature→URL/view/service/model/docs) — the seed for the KOS features/ layer |
| PKALS v2 | `docs/pkals_v2/` (5 md, 2026-06-13, "PROPOSAL, nothing implemented") — predecessor design for automation: read-only-over-frozen-v1, **detect-and-notify-never-auto-rewrite**, cost/benefit register. Two of its MUST items were later BUILT as repo-local skills: `.claude/skills/find-canonical` + `.claude/skills/impact` (wrapping `scripts/pkals_canonical.py` and the CHANGE_IMPACT_MATRIX). Partially in tension with KOS v3 generation (→ Design Record R7) |
| Cleanup input | `docs/DOCUMENT_ARCHIVE_REVIEW.md` (2026-07-11, review-only; KEEP/SUPERSEDED/ARCHIVE/REMOVE-LATER at family level) — the verified-sound base plan for Phase 7. Consumed there, NOT here |
| Known drift register | pre-seeded Phase-6 input, Appendix B.3 — includes the 2026-07-11 audit findings (archive index 12 rows vs 104 files; canonical_manifest stale; PKALS APPS missing machines+patterns_ai; 3 drifted app READMEs) plus fresh 2026-07-12 findings (read-4-files terminology drift; stale roadmap canonical pointer; REQUEST_JOURNEYS rows 4–12 unwritten; CHOKEPOINTS missing history_service page; archive README broken ARCHITECTURE.md pointer). **Phase 5 fixes NONE of these** (§4) |

### 2.2 The design-record gap (what this contract can and cannot recover)

The KOS design was frozen by owner review across a V1→V2→V3 chain that lived in chat history.
What survives on record is a **seven-element core** (Appendix B.1, embedded verbatim from the
campaign memory file) plus the docs-architecture audit findings (Appendix B.2). The full V1→V3
reasoning chain and any fine detail beyond the seven elements (e.g. the exact seven metadata
field names, the exact card template) are **unrecoverable**. This contract therefore:
1. embeds what survives, with provenance labels;
2. defines binding defaults for every gap, each labeled `[PROPOSED]`;
3. routes every `[PROPOSED]` default through owner ratification at DOC-0 (Design Record,
   Appendix A) before DOC_STANDARDS.md is authored.
Label resolution: status file says "Version 3", the agent-memory index says "v3.1". Both name
the same frozen design; this contract canonicalizes **"KOS v3"** and DOC-0 asks the owner to
confirm no lost delta hides behind the ".1" (→ R1).

### 2.3 In / out

**In:** owner ratification of the design (DOC-0) · authoring `docs/DOC_STANDARDS.md` (DOC-1) ·
wiring it into the entry indexes + activating the parent-contract inheritance (DOC-2).
**Out (each has its own phase):** docs census (6) · fixing/moving/archiving/renaming ANY
existing doc (7) · knowledge_graph.json construction (8) · generating cards/indexes (9) · any
management command or script (12/13/14) · Knowledge Card content · README updates beyond the §9
allowlist · application code, tests, migrations, battery, certification · touching
`canonical_manifest.json` or anything CI-guarded · PDF regeneration.

## 3. Success criteria

Phase 5 is DONE when ALL hold:
1. Design Record (Appendix A) filled: every ratification item R1–R12 carries an owner answer
   ("default accepted" is a valid answer; silence is not).
2. `docs/DOC_STANDARDS.md` exists, is complete against the required-content register (§6.2 —
   every row checked off with the section that satisfies it), and is **self-contained**: a
   reader with no chat history and no agent memory can apply it.
3. DOC_STANDARDS.md contradicts NO tier-1 truth lock (PDD, ADRs, freeze packages,
   ARCHITECTURE_V2, PRE_S1_DESIGN_ADDENDUM, FACTORY_OPERATIONS_MASTER) — it cites and
   subordinates (§6.1.7); any discovered contradiction was reported per §16.3, not reconciled
   unilaterally.
4. Every statement in DOC_STANDARDS.md carries one of the three provenance classes (§5) — no
   unlabeled invention.
5. The parent-contract inheritance is live: framework README names this contract as parent for
   phases 6–9/14/18–19; DOCUMENTATION_INDEX and START_HERE route to DOC_STANDARDS.md.
6. Zero code changes; zero existing docs renamed/moved/archived/content-edited outside the §9
   allowlist; battery baseline untouched and NOT re-run.
7. Status file + this contract's Design Record/evidence + memory (if available) updated.

## 4. Rules of engagement (deltas beyond U1–U14)

- **Docs-only phase, tighter than U1:** there is no code-change branch at all. A "confirmed
  finding" in this phase can only ever be a documentation-standards decision.
- **Read-only until the owner ratifies.** DOC-0 presents the Design Record items and STOPS.
  DOC_STANDARDS.md is not authored before Appendix A's decision half is filled.
- **No invention without a label.** Every rule in DOC_STANDARDS.md traces to `[KOS-v3]`,
  `[REPO <file>]`, or `[PROPOSED→R#]` (§5). An executing agent that cannot source a rule must
  route it to the Design Record, never silently assert it.
- **Discovered drift is registered, never fixed.** Phase 5 will inevitably re-observe stale
  docs (§2.1 drift register). Fixing even one is scope creep into Phase 7 — append it to
  Appendix B.3 and move on. The SOLE exception is the §9 allowlist (index rows + pointers).
- **No renames, no moves, no archives, no deletions** of anything, anywhere, this phase.
- **Truth locks are upstream.** Where existing owner rules already legislate documentation
  (CLAUDE.md rule 12 DOCS-SYNC, PKALS-LIVE, U6, archive banner convention, ADR append-only
  rule), DOC_STANDARDS.md codifies and cites them; it may tighten, never weaken (mirror of the
  U-invariant rule).
- DOC_STANDARDS.md is created with lifecycle status `draft` and flips to `frozen-v1` only at
  DOC-2 owner acceptance (§6.1.12 lifecycle applied to itself).

## 5. Evidence standard

An architecture phase proves provenance and completeness, not runtime behavior:
- **Provenance classes (mandatory on every DOC_STANDARDS rule):**
  `[KOS-v3]` = from the embedded design core (Appendix B.1) ·
  `[REPO <path>]` = codification of an existing convention, citing the file(s) that prove it ·
  `[PROPOSED→R#]` = reconstructed/new default, ratified under Design Record item R#.
- **Completeness proof:** the §6.2 required-content register reproduced in the DOC-1 evidence
  section with every row → satisfying DOC_STANDARDS section, or an explicit owner-approved N/A.
- **Non-contradiction proof:** DOC-1 evidence lists each tier-1 truth lock consulted and states
  "no conflict" or the reported conflict (§16.3).
- **Link proof:** every link added in this phase (DOC_STANDARDS + index rows) resolves —
  verified by opening each target; results recorded.
- Sub-agent findings supplemental only (U7); the Design Record and the final §6.2 check are
  main-thread work.

## 6. Methodology — the documentation architecture this phase materializes

§6.1 defines the architecture as **binding defaults**. At execution, DOC-1 transcribes §6.1
into DOC_STANDARDS.md as amended by the DOC-0 Design Record — the Record wins wherever it
differs. Provenance labels below are normative and carry into DOC_STANDARDS.md.

### 6.0 Design of record

The design of record = the seven-element KOS v3 core, embedded verbatim with provenance in
**Appendix B.1**:

1. **features/ layer = the primary aggregation key** of project knowledge.
2. **URL knowledge cards** — per-route knowledge units.
3. **knowledge_graph.json = single source** for generated documentation.
4. **KOS:GEN fences** — generated content lives inside marked fences.
5. **`manage.py knowledge_sync`** — code⇄docs drift detection (built in Phase 14).
6. **7-field metadata core** on documents.
7. **Graceful tool-death degradation** — documentation survives its tooling.

Everything else in §6.1 is codification `[REPO]` or reconstruction `[PROPOSED]`.

### 6.1 The documentation architecture

#### 6.1.1 Philosophy `[REPO + KOS-v3]`

1. **Docs are the resumability substrate.** Any session, any AI, any human resumes from
   documentation alone — the campaign itself is the proof (framework README; status file).
2. **Drift is an architecture bug.** Code change ⇒ docs change, same session (CLAUDE.md rule
   12; PKALS-LIVE; U6). A stale doc is a defect with a register, not an annoyance.
3. **One canonical doc per topic.** Every question has exactly ONE authoritative answer
   document; everything else routes to it (canonical_manifest.json `how_to_use`; START_HERE).
4. **Docs are the map; code + truth locks are the territory.** PKALS "routes you to
   code/tests/ADRs — it is not the source of truth, it is the map" (LEARNING_2_0/README.md).
   Exception: tier-1 truth locks (PDD = product truth; ADRs = mechanism truth).
5. **Dual-register by default.** Operational docs serve the junior developer AND the owner
   (Hinglish welcome — expense README precedent) AND the AI agent (token-cheap routing).
6. **Evidence over assertion** (U11). Claims about system behavior carry probe artifacts;
   receipts and certifications are append-only.
7. **Nothing binding lives only in memory or chat.** Agent memory is a convenience mirror
   (campaign contracts §12 pattern). The KOS design itself nearly dying in chat is the founding
   incident of this rule.
8. **Lazy-load layering.** Entry docs stay small and route; deep context loads only when needed
   (CLAUDE.md header pattern).

#### 6.1.2 Hierarchy — tiers and conflict rules `[REPO, tiers formalized: PROPOSED→R10]`

| Tier | Class | Members (today) | Wins on |
|---|---|---|---|
| T0 | Entry / routing | START_HERE · DOCUMENTATION_INDEX · PROJECT_KNOWLEDGE_MAP · canonical_manifest.json · CLAUDE.md | where to read |
| T1 | Truth locks (frozen) | PDD · ADRs 0001–0011 · MANUFACTURING_V1_FREEZE · ARCHITECTURE_V2 · PRE_S1_DESIGN_ADDENDUM · FACTORY_OPERATIONS_MASTER · frozen design/requirement docs | WHAT is true (product intent: PDD · mechanism: ADR) |
| T2 | Canonical topic/system docs | SYSTEM_DESIGN · GLOSSARY · UI_COMPONENTS · docs/production/* incl. RBAC · CHOKEPOINTS pages | HOW a subsystem works |
| T3 | App layer | config/<app>/README.md + docs/apps/<app>/GUIDE.md | one app's business view + file map |
| T4 | Feature / URL layer (KOS, new) | docs/features/* + URL knowledge cards (Phase 9) | cross-app feature aggregation + per-route routing |
| T5 | Operational / live state | status files · backlogs · certifications · campaign contracts · SOAK_TRACKER | current state + procedure |
| T6 | Learning | LEARNING/ lessons · LEARNING_2_0 academy layers | teaching |
| T7 | Receipts / evidence | `*_EXECUTION_PLAN` with results · `*_RECEIPT_*` · certification evidence | what actually happened |
| T8 | Archive | docs/archive/ | history only |

Conflict rules (existing rules restated + completed): PDD wins business intent · ADR wins
mechanism · status file wins state, contract wins procedure, evidence wins observation
(framework README) · PROJECT_KNOWLEDGE_MAP wins overview conflicts (START_HERE) · lower-tier
docs cite upward and never override; generated T4 artifacts NEVER win over T1–T3 — they cite.

#### 6.1.3 Canonical document types `[REPO, typology formalized: PROPOSED→R11]`

The closed typology (a doc's `type` metadata field takes exactly one): `entry-index` ·
`truth-lock` · `adr` · `topic-canonical` · `app-readme` · `app-guide` · `feature-doc` ·
`url-card` · `page-contract` · `data-flow` · `request-journey` · `chokepoint` ·
`database-guide` · `lesson` · `receipt` · `evidence-cert` · `campaign-contract` ·
`status-anchor` · `machine-index` (json) · `archive-record`. New types require a
DOC_STANDARDS amendment (owner-gated once frozen).

#### 6.1.4 README responsibilities `[REPO docs/apps/README.md, config/expense/README.md]`

`config/<app>/README.md` = the app's **business view, code-adjacent, dual-register**: purpose ·
one-sentence business responsibility · tables-created table ("one row means / lifecycle") ·
data-flow diagram · invariants and money rules · dated hardening narratives. It is NEVER a
file-by-file map (that is the GUIDE) and never machine-generated. Root README = repo front
door. `docs/apps/<app>/GUIDE.md` = developer's file-by-file map (per-directory tables, ★ marks
chokepoint/sole-writer files, header cross-links to the business README + governing 🔒 docs).
New code file ⇒ GUIDE table row, same session (CLAUDE.md rule 12).

#### 6.1.5 Knowledge Card responsibilities `[KOS-v3 + PROPOSED→R4]`

A URL knowledge card is the **smallest routable knowledge unit**, keyed by URL name. It answers,
for one route: route/mount · view · gate(s) (mixin + SidebarItemRule + service re-gate) ·
services invoked · models written (naming the single writer) · governing docs (page contract,
flow, journey, ADR) · mobile strategy. Cards ROUTE and SUMMARIZE with citations; they are never
truth. Cards are `generated` or `hybrid` class (§6.1.16), produced in Phase 9 from the graph.
Until Phase 9 ships, **URL_ATLAS.md remains the interim canonical** for route knowledge.
Default grain: one card per URL_ATLAS row `[PROPOSED→R4]`.

#### 6.1.6 Audience registers `[REPO]`

- **Business documentation:** PDD (product truth) · GLOSSARY · FACTORY_OPERATIONS_MASTER ·
  business flows (stage_earnings_flow, fnf_business_flow) · owner-register sections of app
  READMEs. Business intent changes only via ADR/approved PDD revision.
- **Developer documentation:** SYSTEM_DESIGN · app GUIDEs · DATABASE_GUIDE · DJANGO_GUIDE ·
  CHOKEPOINTS · UI_COMPONENTS · PAGES contracts · DATA_FLOWS/REQUEST_JOURNEYS.
- **AI documentation:** CLAUDE.md · AI_AGENT_GUIDE + canonical_manifest.json · campaign
  contracts · (Phase 8+) knowledge_graph.json. Law: **no AI-only truth** — every binding rule
  readable by machines must also exist in human-readable form; machine indexes are generated
  views or CI-guarded mirrors, never sole records.
- **Learning documentation:** LEARNING/ `NN_TOPIC.md` lessons (generic concepts) ·
  LEARNING_2_0 academy (project-specific why/how). Teaching register; routes to truth, never
  holds it.

#### 6.1.7 ADR relationship `[REPO docs/adr/README.md]`

ADRs are append-only, immutable, supersede-not-rewrite, numbered `NNNN-kebab-slug`. Format:
Status · Context · Decision · Consequences (+ observed extensions: Source, guardrails).
DOC_STANDARDS is **subordinate to every ADR** and must link rather than restate (link-don't-fork
prevents truth divergence). Any decision surfaced during documentation phases that locks
architecture or product behavior routes to a NEW ADR — documentation phases never lock
decisions inside documentation-system files. PKALS-v2-style proposal packs (pkals_v2/) are
explicitly NOT ADRs and bind nothing.

#### 6.1.8 Memory relationship `[REPO campaign contracts §12 pattern]`

Agent memory (any vendor) is a per-agent convenience mirror. Binding order: on-disk docs >
memory; a contradiction is a finding (framework conflict rule). Nothing may exist ONLY in
memory — the standing test: "could a memory-less agent execute from docs alone?" Every phase
contract carries a §12 memory rule with the "agents without memory: skip" clause. Memory files
may cite docs; docs never cite agent memory.

#### 6.1.9 Cross-app documentation `[REPO + KOS-v3]`

Cross-app knowledge lives in exactly four places: DATA_FLOWS (write paths) · REQUEST_JOURNEYS
(call chains, 16-section template) · CHOKEPOINTS (single-writer services — one page per
manifest `never_modify` writer) · the **features/ layer** (KOS: a feature = the primary
aggregation key spanning apps; seed = PROJECT_BRAIN/FEATURE_INDEX.md). Import boundaries
(`config/.importlinter`, AI_AGENT_GUIDE boundary rules) are documented at T2. An app doc never
narrates another app's internals — it links the flow/journey/feature doc.

#### 6.1.10 Code→doc mapping laws `[KOS-v3 + REPO + PROPOSED→R4/R5]`

| Code object | Must map to | Completeness instrument |
|---|---|---|
| URL (every live route) | exactly ONE url-card (Phase 9+; interim: URL_ATLAS row) + membership in ≥1 feature | route census (MGT-H instrument: 528 routes at last count) vs card/atlas inventory |
| Model (every concrete model) | owning app README "one row means" row + DATABASE_GUIDE/GUIDE coverage; append-only/money tables ADDITIONALLY a chokepoint page naming the sole writer | model census vs rows |
| Service (every service module) | app GUIDE row; single-writer services ADDITIONALLY: CHOKEPOINTS page + manifest never_modify entry | service census vs GUIDE/CHOKEPOINTS |
| View | documented at URL grain (its card/atlas row), file grain (GUIDE row); significant pages ADDITIONALLY a PAGES 10-section contract | view census vs rows |

Mapping completeness is MEASURED in Phase 6, ENFORCED by Phase 14 knowledge_sync, and NEVER
assumed. Known gap example at authoring: CHOKEPOINTS lacks a history_service page (drift
register, B.3).

#### 6.1.11 Documentation ownership `[PROPOSED→R11, precedent: OWNERSHIP_MATRIX.md]`

Every doc declares exactly one ownership class in metadata:
**`handwritten`** (human/agent-authored; machines never write it) · **`generated`** (machine-
owned in full; regenerated from the graph; hand edits forbidden and overwritten; carries a
generated-banner) · **`hybrid`** (handwritten body + KOS:GEN fenced generated sections) ·
**`frozen`** (truth locks; append-only dated corrections/amendments only) · **`append-only`**
(receipts, evidence, certifications — closed sections never edited, corrections appended).
The existing OWNERSHIP_MATRIX (doc → human owner + update trigger) is extended, not replaced,
when Phase 7 touches it.

#### 6.1.12 Documentation lifecycle `[REPO archive convention + DOCUMENT_ARCHIVE_REVIEW taxonomy]`

`draft → active → (frozen) → superseded → archived`, plus `remove-later` (delete only after
soak + explicit owner sign-off — never before). Transitions: supersession NAMES the successor
and stamps the `> **ARCHIVED <date>** — superseded by <successor>. Kept for history.` banner;
archived files move under docs/archive/ AND gain an archive-index row (both, always — the
current 12-rows-vs-104-files state is the counterexample). Truth is never deleted; it is
superseded. Receipts/evidence are born `append-only` and skip `draft`. Lifecycle state lives in
the metadata `status` field.

#### 6.1.13 Metadata — the 7-field core `[KOS-v3 count; fields PROPOSED→R2]`

KOS v3 fixes the count at seven; the exact field names did not survive. Proposed core, as YAML
frontmatter (0/496 adoption today — greenfield):

```yaml
---
id: stable-kebab-slug            # unique across docs/
type: url-card                   # one of §6.1.3
status: active                   # §6.1.12 lifecycle state
owner: hybrid                    # §6.1.11 class (+ optional maintainer)
scope: expense, settlement       # apps/features this doc binds
anchors: config/expense/services/settlement_service.py   # code paths documented (drift probes)
verified: 2026-07-12             # last verified-against-code date
---
```

Adoption strategy `[PROPOSED→R2]`: mandatory on all NEW docs from Phase-5 execution onward;
retrofit onto ACTIVE-tier docs during Phase 7 (not before); archive NEVER retrofitted.
Machine-index files (json) carry the same seven as top-level keys.

#### 6.1.14 Naming conventions `[REPO, codified; new-artifact names PROPOSED→R8]`

Codify the existing styles as the closed set — ALL_CAPS topic docs (root/system) ·
`*_YYYY_MM_DD` dated receipts/audits · `PHASE_NN_SLUG` campaign contracts · lowercase_snake
flow/page/card files · `NN_TOPIC` lessons · `NNNN-kebab` ADRs. New KOS artifacts (default,
ratify): `docs/DOC_STANDARDS.md` · `docs/features/<feature_slug>/README.md` (feature doc) ·
`docs/features/<feature_slug>/<url_name>.md` (url-cards) · `docs/knowledge_graph.json`
(Phase 8). No fifth naming style without a DOC_STANDARDS amendment.

#### 6.1.15 Linking conventions `[REPO]`

Relative markdown links, always to the CANONICAL doc (never to a copy) · `[text](path)`
clickable form, not bare backticks · section anchors for deep links · archived docs are linked
only via their supersession banners or the archive index — active docs never cite archive as
truth · `[[wiki-links]]` are an agent-memory idiom and never appear in docs/ · every active doc
must be reachable from DOCUMENTATION_INDEX or a parent index (orphan = Phase-6 finding) · link
integrity of machine-indexed paths is CI-guarded (PkalsNavigationGuardTests precedent; extended
by Phase 14).

#### 6.1.16 Generated vs handwritten `[KOS-v3 + pkals_v2 stance; fence syntax PROPOSED→R6]`

- Fence syntax (default): `<!-- KOS:GEN begin section=<name> generator=<tool> source=knowledge_graph.json generated=<ISO-date> -->` … `<!-- KOS:GEN end section=<name> -->`.
- Humans/agents never edit inside a fence; generators never write outside one. A `generated`-
  class doc is one fence with a banner; a `hybrid` doc mixes fenced and handwritten sections.
- **Prose is never machine-rewritten.** The pkals_v2 law "detect-and-notify, never auto-rewrite"
  is adopted permanently for PROSE; KOS generation produces STRUCTURAL content (tables, indexes,
  cards, cross-reference lists) from the graph. This is the reconciliation of pkals_v2's
  "auto-generation NOT WORTH" verdict with KOS v3 generation (→ R7 for owner confirmation).
- **Graceful tool-death degradation** `[KOS-v3]`: every generated artifact must remain valid,
  readable, hand-editable static markdown if the tooling never runs again. No doc may REQUIRE
  tooling to be read. If the owner ever declares generation dead, generated docs convert to
  `handwritten` via a dated banner — content survives, the fence discipline retires.

#### 6.1.17 Validation philosophy `[REPO PKALS-LIVE + KOS-v3; dimensions PROPOSED→R12]`

Drift = bug. Validation dimensions: link integrity · metadata completeness · fence integrity ·
mapping coverage (§6.1.10 censuses) · index completeness (no orphans) · staleness (`verified`
date vs anchor-file changes) · non-contradiction spot-checks. Until Phase 14: manual, per U6 +
CHANGE_IMPACT_MATRIX (+ the existing `/impact` and `/find-canonical` skills). Phase 14
automates detection; per the adopted pkals_v2 law, automation DETECTS and REPORTS — a human or
agent judges and writes. Validation failures are findings under U12 discipline.

#### 6.1.18 Future automation hooks `[KOS-v3 + REPO pkals_v2/skills; defined-not-built]`

Named hooks, all **documented-not-implemented** until their phase: `knowledge_graph.json`
builder (Phase 8) · card/index generators (Phase 9) · `manage.py knowledge_sync` code⇄graph⇄docs
drift detector (Phase 14; extends — does not duplicate — `scripts/pkals_canonical.py`, the
`/find-canonical` + `/impact` skills, and PkalsNavigationGuardTests) · CI-guard extension
points. Every hook is code ⇒ its building phase runs the battery per U5 (unlike this phase,
§13) and obeys U14 if anything needs a migration (none foreseen).

#### 6.1.19 Phase interface contracts (what 6–22 inherit)

| Phase | Interface with this foundation |
|---|---|
| 6 Discovery | Census of all 496+ files AGAINST DOC_STANDARDS (typology, metadata, mapping, lifecycle, links); inputs: Appendix B.3 drift register + DOCUMENT_ARCHIVE_REVIEW; output = findings register, ZERO fixes |
| 7 Cleanup | Executes Phase-6 findings under §6.1.12 lifecycle rules (banners, archive index, backlog #6 RBAC.md table, canonical_manifest refresh — the manifest is CI-guarded, so Phase 7 IS a code-adjacent phase and runs the battery per U5) |
| 8 Knowledge Graph | Builds knowledge_graph.json as the **single source** `[KOS-v3]`; node kinds ⊇ {app, url, view, service, model, doc, feature, adr}; edge kinds ⊇ {routes_to, gated_by, calls, writes, documented_by, belongs_to_feature, supersedes, cites} `[PROPOSED→R5]`; relationship to canonical_manifest.json (wrap vs generate) decided at R5 |
| 9 Generation | Produces url-cards + feature indexes from the graph inside KOS:GEN fences; regeneration must be deterministic (byte-stable for unchanged inputs) |
| 11–13 Dataset/Seeder/Verification | Each engine ships WITH its canonical T2 doc + cards per §6.1.10; verification receipts = `append-only` class; seeded DEV worlds referenced by docs must carry stable identifiers |
| 14 knowledge_sync | Implements §6.1.17 detection dimensions; detect-and-report only |
| 15–17 Feature builds | U6 + CHANGE_IMPACT_MATRIX bind; a new feature ships with its feature doc + cards + PDD/ADR routing — "docs-complete" is part of feature-DONE |
| 18 Future Feature Doc Updates | Syncs PDD/roadmap/feature docs with 15–17 reality under this standard |
| 19–21 Deployment docs + certificate | Runbook = T2 canonical under this standard; readiness certificate = `evidence-cert`, append-only |
| 22 First Git Checkpoint | Commits the documentation corpus; DOC_STANDARDS must be `frozen-v1` by then |

### 6.2 Required-content register for DOC_STANDARDS.md

DOC-1 is complete only when DOC_STANDARDS.md satisfies every row (checked off in evidence):
philosophy (§6.1.1) · hierarchy+conflict rules (§6.1.2) · typology (§6.1.3) · README/GUIDE
responsibilities (§6.1.4) · knowledge-card responsibilities (§6.1.5) · business/developer/AI/
learning registers (§6.1.6) · ADR relationship (§6.1.7) · memory relationship (§6.1.8) ·
cross-app documentation (§6.1.9) · URL/model/service/view mapping laws (§6.1.10) · ownership
classes (§6.1.11) · lifecycle (§6.1.12) · 7-field metadata (§6.1.13) · naming (§6.1.14) ·
linking (§6.1.15) · generated-vs-handwritten + fences + tool-death (§6.1.16) · validation
(§6.1.17) · automation hooks (§6.1.18) · phase interfaces 6–22 (§6.1.19) · its own metadata
block (the first frontmatter in docs/) · a "how to amend this standard" section (owner-gated
once frozen).

### 6.3 Execution order

**DOC-0:** re-verify §2.1 facts (drift → note in evidence; material contradiction → §16.6) ·
present Appendix A items R1–R12 with defaults · capture owner answers in the Decision half ·
update status file · STOP.
**DOC-1:** author docs/DOC_STANDARDS.md = §6.1 as amended by the Design Record, all provenance
labels carried, status `draft` · run the §6.2 register check + §5 link/non-contradiction proofs
· append evidence · STOP.
**DOC-2:** owner reads DOC_STANDARDS.md · corrections applied (appended to the Design Record as
dated amendments if they alter ratified items) · status → `frozen-v1` · wire entry points (§9
allowlist): DOCUMENTATION_INDEX row, START_HERE pointer, framework README parent-contract note
(if not already live from authoring), campaign status row → ✅ · close evidence · STOP.

## 7. Sub-phase breakdown

| # | Scope | Session type | Status |
|---|---|---|---|
| DOC-0 | Design ratification: present R1–R12, fill Decision half of the Design Record; no authoring | decision (owner + any agent) | ☐ |
| DOC-1 | Author DOC_STANDARDS.md from ratified design; completeness + provenance + link proofs | execution (any agent or human) | ☐ |
| DOC-2 | Owner acceptance → freeze v1; entry-point wiring; phase close | acceptance (owner + any agent) | ☐ |

DOC-0 and DOC-1 may collapse into one session ONLY if the owner is present and ratifies
interactively; the Design Record decision half is still filled BEFORE the first DOC_STANDARDS
line is written. DOC-2 never collapses into DOC-1 (the owner reads the finished artifact).

## 8. Deliverables

- Filled **Design Record** (Appendix A): R1–R12 answers verbatim + acceptance half.
- **`docs/DOC_STANDARDS.md`** — status `frozen-v1` at phase close, carrying its own §6.1.13
  metadata block and provenance labels throughout.
- Entry-point wiring: DOCUMENTATION_INDEX row · START_HERE pointer · framework README
  parent-contract linkage.
- DOC-0/1/2 evidence sections appended to this file (§5 standard).
- Updated DEPLOYMENT_CAMPAIGN_STATUS.md (Phase-5 row + dashboard) and memory (if available) at
  every sub-phase close.

## 9. Files expected to change

**Docs only:** `docs/DOC_STANDARDS.md` (NEW — the only new root doc this phase) ·
`docs/DOCUMENTATION_INDEX.md` (one row, DOC-2) · `docs/START_HERE.md` (one pointer, DOC-2) ·
`docs/campaign_contracts/README.md` (index tick / parent-contract note) ·
`docs/DEPLOYMENT_CAMPAIGN_STATUS.md` · this file (Design Record + evidence appendices — the
frozen-contract rule permits appending these designated sections) · memory files (if agent has
memory). Nothing else.

## 10. Files that must never change (touching one = STOP + report)

- ANY application file: code, tests, migrations, templates, settings, `.env`, media.
- **`docs/LEARNING_2_0/AI_AGENT_GUIDE/canonical_manifest.json`** — CI-guarded
  (PkalsNavigationGuardTests); editing it makes this a code-adjacent phase and voids §13.
  Manifest refresh belongs to Phase 7.
- Every existing doc outside the §9 allowlist — including every drifted doc in Appendix B.3
  (register, don't fix), `docs/pkals_v2/*`, `docs/DOCUMENT_ARCHIVE_REVIEW.md`, all PKALS
  layers, all app READMEs/GUIDEs.
- All tier-1 truth locks (PDD, docs/adr/*, freeze packages, ARCHITECTURE_V2,
  PRE_S1_DESIGN_ADDENDUM, FACTORY_OPERATIONS_MASTER).
- `.claude/skills/*` (existing tooling is Phase-14 input).
- `.git` state (U2) · the 2 pre-existing stashes · no renames/moves/archives/deletions anywhere.

## 11. Documentation update rules

At DOC-0 close: Design Record decision half + status-file Phase-5 row ("design ratified,
awaiting DOC-1") + "Next action". At DOC-1 close: evidence section (register check, provenance
census, link proofs) + status-file row. At DOC-2 close: acceptance in the Design Record +
status-file row → ✅ with pointer to DOC_STANDARDS.md + dashboard "Last docs sync" + the
carry-over row "KOS design" cleared (superseded by the on-disk standard). U6 app-doc lookups
are N/A throughout (no code changes).

## 12. Memory update rules

Agents with persistent memory: at each sub-phase close update
`project_deployment_campaign_2026_07_12.md` (Phase-5 bullet: ratified items, DOC_STANDARDS
status) + the MEMORY.md index line; after DOC-1, memory's KOS summary is DEMOTED to a pointer —
the design of record is DOC_STANDARDS.md + this contract's Appendix B, never memory (§6.1.8).
Agents without memory: skip — §11's on-disk records are the complete binding record.

## 13. Battery policy

**Never runs in this phase.** No code change is possible under §10; there is nothing to test.
Baseline (1526/1526 at authoring) is untouched and NOT re-verified here. Guard note: the only
docs-adjacent file that could reach the test surface is canonical_manifest.json — which is why
§10 forbids it outright. (Contrast: Phase 7 WILL touch it and therefore runs the battery.)

## 14. Regression policy

- The only regressions this phase can cause: (a) contradicting an existing truth lock —
  guarded by the §5 non-contradiction proof and §16.3; (b) breaking a link in the four
  allowlisted docs — guarded by the §5 link proof; (c) scope-creep edits to existing docs —
  guarded by §10 + the §3.6 zero-renames criterion.
- No pins, no tests — U4 vacuously satisfied.
- Prior-phase artifacts (certifications, contracts, status history) are not re-proven here;
  DOC_STANDARDS may cite them but never restates their verdicts.

## 15. Rollback policy

- DOC-1 aborts cleanly: delete the draft DOC_STANDARDS.md (it is this phase's own creation —
  the one permitted deletion, and only while status = `draft`), revert the added index rows.
  Nothing else was touched by construction.
- A partially-authored DOC_STANDARDS.md at session death: keep it, status stays `draft`, next
  session resumes per §17 (never half-freeze).
- Design Record entries are never rolled back — a changed owner decision is appended as a dated
  amendment row (append-only record discipline, U13 analog).
- After DOC-2 freeze: corrections to DOC_STANDARDS follow its own amendment section
  (owner-gated), not this rollback policy.

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. Owner decision missing/ambiguous on any R1–R12 at DOC-1 start.
3. DOC_STANDARDS content would contradict a tier-1 truth lock or an ADR — report the conflict;
   never reconcile unilaterally (framework conflict rule).
4. Any §10 file would be modified, or pressure arises to "quickly fix" a drifted doc
   (register per Appendix B.3 and stop the impulse, or stop the session if scope is forced).
5. Discovery of an on-disk KOS design record that conflicts with Appendix B.1 (a fuller export
   may exist somewhere) — reconcile provenance with the owner BEFORE authoring.
6. §2.1 facts materially drifted (docs restructured, manifest moved, pkals_v2 changed) —
   re-assess before standardizing against the wrong landscape.
7. A ratification answer would require changing application code, a CI guard, or a migration —
   that answer belongs to a later phase's contract; record it as deferred, do not act.

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-5 row: which DOC-* is next?
2. Read `docs/campaign_contracts/README.md` (U1–U14 + environment) → this contract FULLY,
   including Appendices A and B.
3. Check Appendix A: decision half empty → next = DOC-0. Decision half filled, no
   DOC_STANDARDS.md on disk (or status `draft`) → next = DOC-1. DOC_STANDARDS.md exists +
   acceptance half empty → next = DOC-2. Both halves filled → phase done; verify
   DOC_STANDARDS.md still exists, status `frozen-v1`, entry-point links resolve.
4. Re-verify §2.1 facts read-only (file counts, manifest path + version, pkals_v2 presence,
   DOC_STANDARDS.md presence/status). Material drift → stop condition 6.
5. No app login, no password, no dev server needed for this phase.
6. Execute exactly one sub-phase per §6.3. STOP per §16.
7. Anything internally inconsistent across status file / this contract / Design Record →
   report before authoring (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (DOC-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| R1 | Design label + completeness | "KOS v3" = "v3.1"; Appendix B.1 seven-element core = the complete surviving design intent; no hidden delta | **Default accepted** (owner ratification order 2026-07-13) — "KOS v3" is the canonical label; no lost delta claimed behind "v3.1" |
| R2 | Metadata | 7 fields as §6.1.13 (id/type/status/owner/scope/anchors/verified), YAML frontmatter; new docs immediately, ACTIVE-tier retrofit in Phase 7, archive never | **Default accepted** (owner 2026-07-13) — the seven field names of §6.1.13 are RATIFIED as the KOS 7-field core |
| R3 | features/ taxonomy + layout | Seed taxonomy from PROJECT_BRAIN/FEATURE_INDEX.md; layout `docs/features/<slug>/README.md` + cards beside it | **Default accepted** (owner 2026-07-13) |
| R4 | URL-card template + grain | Card fields per §6.1.5; grain = one card per URL_ATLAS row | **Default accepted** (owner 2026-07-13) |
| R5 | Graph schema + manifest relationship | Node/edge kinds per §6.1.19 Phase-8 row; canonical_manifest.json becomes a GENERATED VIEW of the graph in Phase 8/9 (CI guard retained), hand-maintained until then | **Default accepted** (owner 2026-07-13) — manifest stays hand-maintained + CI-guarded until the Phase-9 conversion |
| R6 | Fence syntax | `<!-- KOS:GEN begin/end -->` form per §6.1.16 | **Default accepted** (owner 2026-07-13) — note: PHASE_09 carries a pre-registered dated-amendment REQUEST on the `generated=<ISO-date>` attribute (determinism); that disposition belongs to GEN-0, not here |
| R7 | pkals_v2 tension | KOS v3 (later, owner-frozen) supersedes pkals_v2's "auto-generation NOT WORTH" verdict FOR STRUCTURAL content; pkals_v2's "never auto-rewrite PROSE" adopted permanently | **Default accepted** (owner 2026-07-13) — structural generation licensed; prose never machine-rewritten, permanently |
| R8 | New-artifact naming | Per §6.1.14 defaults | **Default accepted** (owner 2026-07-13) — closed naming set; no fifth style without amendment |
| R9 | Tool-death degradation binding | Per §6.1.16 (static-readable, hand-editable, owner-declared conversion path) | **Default accepted** (owner 2026-07-13) — binding on every generated artifact |
| R10 | Hierarchy tiers + conflict rules | T0–T8 + conflict rules per §6.1.2 | **Default accepted** (owner 2026-07-13) — generated T4 never wins over T1–T3 |
| R11 | Typology + ownership classes + lifecycle | Per §6.1.3 / §6.1.11 / §6.1.12 | **Default accepted** (owner 2026-07-13) — closed typology; 5 ownership classes; lifecycle incl. remove-later-only-after-soak+sign-off |
| R12 | Validation dimensions + Phase-14 boundary | Per §6.1.17 (detect-and-report only) | **Default accepted** (owner 2026-07-13) — automation detects and reports; a human/agent judges and writes; no `--fix` ever (PHASE_14 alignment) |

Date · answered by: **2026-07-13 · Owner (Umesh) — ratification order verbatim: "Ratify R1–R12 exactly as required by the Phase 5 contract." Recorded by the executing agent as "Default accepted" ×12 per §3.1 ("default accepted" is a valid answer); no default overridden; no ambiguity remained (stop §16.2 clear for DOC-1).**

## Acceptance half (DOC-2)

| Field | Value |
|---|---|
| DOC_STANDARDS.md accepted + frozen at | **2026-07-13 — `frozen-v1`** (frontmatter `status: frozen-v1`, `owner: frozen` per §20.2). Owner acceptance order verbatim: "Execute Phase 5 → DOC-2 exactly according to the frozen Phase 5 contract … Perform the owner acceptance review of DOC_STANDARDS.md … Decide each tension strictly according to the contract (report, amend, or retain) … Change the document status from draft to frozen-v1 if—and only if—the acceptance criteria are fully satisfied." Artifact open in the owner's IDE at review; dispositions derived strictly from contract rules (§4 truth-locks-upstream / §3.3 cites-and-subordinates) per that order. §3 acceptance criteria re-verified 7/7 before the flip. |
| Corrections applied before freeze | **6 corrections, all §20.1-path:** (1) tension-1 [MED]: §6 business change-control rewritten to include the freeze-sanctioned owner-ruling channel (FOM §5/§7, MANUFACTURING_V1_FREEZE header cited) — pure `[REPO]` codification fix, no R-item touched; (2) tension-2 [MED]: §11 tier/ownership-class decoupling note added → **dated amendment A1 (alters R11 gloss)**; (3) tension-3 [LOW]: §2 conflict rule + T1 "Wins on" column restored to PDD's own wording "ADRs + ARCHITECTURE_V2 win mechanism" → **dated amendment A2 (alters R10 restatement)**; (4) frontmatter flip draft→frozen-v1 + handwritten→frozen; (5) header banner draft→frozen statement; (6) §20.1 tense ("now → DOC-2" → historical) + Amendments-register label ("v1 draft" → "v1 frozen 2026-07-13", pre-freeze corrections pointered here). Frontmatter self-note from DOC-1 evidence RESOLVED by (4): `owner: frozen` now matches §11's truth-lock class. |
| Entry-point wiring verified (links resolve) | **2026-07-13:** DOCUMENTATION_INDEX row added (Entry points table) ✓ · START_HERE pointer added (map-of-maps footer) ✓ · framework README parent-contract linkage verified ALREADY LIVE (hierarchy §2 names PHASE_05 as parent for 6–9/14/18–19 + master-index row 5 "PARENT contract") — no edit needed ✓ · post-edit link proof: every link in the three changed docs resolves (recorded in §DOC-2 evidence) ✓ |

## Dated amendments

- **A1 (2026-07-13, DOC-2 — amends R11 ownership-classes gloss):** BEFORE: §6.1.11/`§11` implied every T1 truth lock is `frozen` class ("Truth locks; append-only dated corrections/amendments only"). AFTER: class table unchanged, but tier membership does NOT force ownership class — a T1 lock whose own owner-sanctioned change control permits in-body owner rulings (FACTORY_OPERATIONS_MASTER §5/§7 under MANUFACTURING_V1_FREEZE change control) is classed at the Phase-7 retrofit by that sanctioned model; the `owner:` field records, never overrides, the sanctioned change model. WHY: DOC-1 non-contradiction proof, tension 2 — truth-lock governance is upstream (§4); the unamended gloss would have made FOM's owner-blessed editing model non-compliant at retrofit. Owner authority: DOC-2 acceptance order ("decide each tension strictly according to the contract").
- **A2 (2026-07-13, DOC-2 — amends the R10 conflict-rules restatement):** BEFORE: "PDD wins business intent · ADR wins mechanism" (+ T1 "Wins on": "mechanism: ADR"). AFTER: "ADRs and ARCHITECTURE_V2 win mechanism" (+ "mechanism: ADRs + ARCHITECTURE_V2") — restored to the PDD "Layering of truth" verbatim scope. WHY: DOC-1 tension 3 — the restatement was lossy vs the T1 lock's own conflict rule; a restatement of upstream truth must be faithful (§3.3). Tier table T0–T8 and all other R10 conflict rules unchanged. Owner authority: same DOC-2 order.
- **A3 (2026-07-13, Phase-9 GEN-0 — amends the R6 fence-header default, §6.1.16):** BEFORE: fence syntax `<!-- KOS:GEN begin section=<name> generator=<tool> source=knowledge_graph.json generated=<ISO-date> -->`. AFTER: the `generated=<ISO-date>` field is REPLACED by deterministic generation metadata: `graph=<content-hash-prefix> schema=<major.minor> template=<version>` — no wall-clock date may appear in any generated body or fence header (generation dates live in `docs/DOCUMENTATION_GENERATION_LOG.md` only). WHY: the ISO-date field and the campaign-ratified determinism law (PHASE_09 §2.1.6 / GEN-D4/D6: identical graph + identical templates ⇒ byte-identical outputs) cannot both hold — a date-bearing regeneration is never byte-stable. Flagged honestly at PHASE_09 authoring (§6.4 ⚠️ R6 reconciliation), classified at GEN-0 as OI-1. Fence begin/end markers, section discipline, and every other R6 rule unchanged; `docs/DOC_STANDARDS.md` body untouched (this amendment lives here per the permitted process). Owner authority (2026-07-13, verbatim): "OI-1: ACCEPT. Record the dated amendment exactly as proposed. Replace the wall-clock generated-date with deterministic generation metadata (graph hash, schema version, template version). Preserve deterministic, byte-identical generation. Do not modify the body of DOC_STANDARDS beyond the permitted amendment process."

---

# Appendix B — Embedded design record (kills the memory dependency)

## B.1 The KOS v3 core — verbatim recovery

Provenance: campaign memory file `project_deployment_campaign_2026_07_12.md` (the only
cross-session record, per that file and the framework README risk register), recovered
2026-07-12 during this contract's authoring:

> **KOS (phases 5-9) design of record = Version 3** (owner-frozen in design review; features/
> layer = primary aggregation key, URL knowledge cards, knowledge_graph.json single source,
> KOS:GEN fences, manage.py knowledge_sync, 7-field metadata core, graceful tool-death
> degradation). Materialize as DOC_STANDARDS.md in Phase 5 — design lives in chat until then,
> summary here is the only cross-session record.

The full V1→V2→V3 review chain (chat history) is unrecoverable. Everything in this contract
beyond these seven elements is codification of repo precedent or labeled reconstruction (§5).

## B.2 Docs-architecture audit findings (2026-07-11, read-only) — Phase-6/7 primary input

Provenance: same memory file: 490 md in docs/ at audit time (286 committed) · archive index
broken + missing ~80 files · canonical_manifest stale (2026-06-13, 17 topics) · PKALS APPS
missing machines + patterns_ai · 3 drifted app READMEs (production / patterns_ai / accounts) ·
41 broken docs-links in agent memory · DOCUMENT_ARCHIVE_REVIEW = verified-sound base plan for
cleanup. (Counts re-verified 2026-07-12 where cheap: 496 md now; archive index 12 rows vs 104
files; manifest version string confirmed 2026-06-13.)

## B.3 Fresh drift register (2026-07-12 authoring census) — pre-seeded Phase-6 input, NOT fixed in Phase 5

1. "read-4-files" terminology drift: AI_AGENT_GUIDE now routes via ONE file
   (canonical_manifest.json) while CLAUDE.md rule 12 + PROJECT_ATLAS §9b + START_HERE still
   advertise a "read-4-files" path.
2. AI_AGENT_GUIDE canonical row for "roadmap" points to ROADMAP_REVIEW_POST_C1_2026_06_11.md;
   PROJECT_ATLAS §10 names IMPLEMENTATION_ROADMAP_PDD_V1.md canonical (itself superseded for
   current state by MANUFACTURING_V1_FREEZE.md per DOCUMENTATION_INDEX).
3. REQUEST_JOURNEYS/README.md: 9 of 12 journey rows (4–12) unwritten/malformed.
4. CHOKEPOINTS has no history_service page despite *History tables being in the manifest
   never_modify list.
5. docs/archive/README.md: 12 index rows vs 104 archived files; only 42/104 carry the ARCHIVED
   banner; points readers to a root ARCHITECTURE.md that does not exist.
6. docs/apps/README.md role blurbs stale (machines "R10"-only, patterns_ai "P1 Block 1");
   GUIDE column shapes undocumented and divergent; production/GUIDE.md banner accretion buries
   the file map.
7. PAGES: 1 filled contract vs a large declared backlog (acknowledged in its own README).
8. docs/pkals_v2/ (5 proposal files) has no disposition (KEEP/ARCHIVE) recorded anywhere;
   DOCUMENT_ARCHIVE_REVIEW does not list it explicitly.
9. Minor: AI_AGENT_GUIDE ARCHITECTURE_V2 link label/path depth mismatch;
   docs/HTML_CANONICAL_CANDIDATES.md name-collides with "canonical" searches;
   docs/FRONTEND_DESIGN_SYSTEM_INVENTORY.partial.json = stray partial artifact.

---

# Appendix C — Coverage map (owner-mandated contract content → where it lives)

| Mandated item | Section |
|---|---|
| Documentation philosophy | §6.1.1 |
| Documentation hierarchy | §6.1.2 |
| Canonical document types | §6.1.3 |
| README responsibilities | §6.1.4 |
| Knowledge Card responsibilities | §6.1.5 |
| Business / Developer / AI / Learning documentation | §6.1.6 |
| ADR relationship | §6.1.7 |
| Memory relationship | §6.1.8 |
| Cross-app documentation | §6.1.9 |
| URL / Model / Service / View mapping philosophies | §6.1.10 |
| Documentation ownership | §6.1.11 |
| Documentation lifecycle | §6.1.12 |
| Required metadata / frontmatter | §6.1.13 |
| Naming conventions | §6.1.14 |
| Linking conventions | §6.1.15 |
| Generated vs handwritten | §6.1.16 |
| Documentation validation philosophy | §6.1.17 |
| Future automation hooks | §6.1.18 |
| Knowledge Graph / Seeder / Verification / Future-Feature / Deployment relationships | §6.1.19 |
| Success criteria | §3 |
| Deliverables | §8 |
| Stop conditions | §16 |
| Resume instructions | §17 |

# Evidence sections (DOC-0, DOC-1, DOC-2 — appended at close)

## DOC-0 — Design ratification (2026-07-13) ✅ — R1–R12 RATIFIED (all defaults accepted), NO authoring

- **Entry state verified per §17:** status file Phase-5 row ☐ execution → next = DOC-0 ·
  this contract read FULLY from disk (all 655 lines incl. Appendices A/B/C) · Appendix A
  decision half was empty → DOC-0 confirmed as next work · framework README (U1–U14) read
  this session · Phase 4 CLOSED CERTIFIED + post-Phase-4 snapshot REFRESH #1 completed +
  validated earlier this session (PHASE_00 §SNAPSHOT REFRESH #1 — the ordered pre-DOC-0 step).
- **§2.1 fact re-verification (read-only, from disk) — drift verdict: normal authoring
  growth, NOT material (stop §16.6 untriggered):** docs/ md = **518** (was 496 at authoring;
  +22 = the campaign corpus growth since 2026-07-12: contracts 3→22 + CONFIRMED_FINDINGS_LEDGER
  + certification evidence docs — all inside docs/, landscape shape unchanged) · archive
  unchanged **104** · `canonical_manifest.json` present, version string **"2026-06-13"**
  (stale-as-documented; UNTOUCHED, §10) · `docs/features/` **does not exist** ✓ ·
  `docs/pkals_v2/` = 5 md ✓ · `DOCUMENT_ARCHIVE_REVIEW.md` present ✓ · **`DOC_STANDARDS.md`
  absent** ✓ (created at DOC-1, not before) · **frontmatter adoption 0/518** (line-1 `---`
  census = 0 — greenfield confirmed) · FEATURE_INDEX.md seed present ✓ · `.claude/skills/`
  `find-canonical` + `impact` present ✓ (Phase-14 inputs, untouched).
- **Ratification:** the R1–R12 matrix presented with binding defaults; owner order received
  verbatim ("Ratify R1–R12 exactly as required by the Phase 5 contract") → **Decision half
  filled: Default accepted ×12**, dated + attributed; per-item notes recorded (R6 PHASE_09
  amendment-request cross-reference · R7 prose-law permanence · R12 no-`--fix` alignment).
  **The frozen documentation execution rules are now established:** DOC-1 authors
  DOC_STANDARDS.md = §6.1 as ratified (no Record deltas exist — defaults unamended), status
  `draft`, provenance labels mandatory; DOC-2 = owner acceptance → `frozen-v1` + entry-point
  wiring.
- **Scope discipline:** ZERO authoring (DOC_STANDARDS.md still absent at close) · zero code ·
  battery NOT run (never runs this phase, §13) · no existing doc touched outside the §9
  allowlist (this contract's designated sections + status file + memory) · no drifted doc
  fixed (B.3 register untouched; nothing new observed beyond the counted growth) ·
  canonical_manifest.json untouched · no renames/moves/archives/deletions.
- **Stop conditions:** none triggered (§16.1 normal close). **Next: DOC-1 — author
  docs/DOC_STANDARDS.md from the ratified design (owner-gated).**

## DOC-1 — DOC_STANDARDS.md authored (2026-07-13) ✅ — status `draft`, all proofs run; 3 inherited truth-lock tensions REPORTED for DOC-2 disposition

- **Entry state verified per §17:** status file Phase-5 row → next = DOC-1 · this contract
  re-read FULLY from disk (all sections + Appendices A/B/C + DOC-0 evidence) · framework
  README (U1–U14) re-read · **Appendix A Decision half FILLED (R1–R12 Default accepted ×12,
  dated 2026-07-13) — stop §16.2 clear** · §2.1 facts re-verified from disk, ZERO drift since
  DOC-0: 518 md (pre-authoring) · archive 104 · manifest version "2026-06-13" untouched ·
  `docs/features/` absent · pkals_v2 = 5 md · frontmatter **0/518** pre-authoring ·
  FEATURE_INDEX seed + `find-canonical`/`impact` skills + DOCUMENT_ARCHIVE_REVIEW present ·
  DOC_STANDARDS.md absent → DOC-1 confirmed as next work (§17.3).
- **Deliverable:** `docs/DOC_STANDARDS.md` CREATED — §6.1 transcribed as ratified (no Design
  Record deltas exist — defaults unamended), status **`draft`** (flips `frozen-v1` only at
  DOC-2, §4), provenance labels on every section (§1–§20 + Appendix; label census: 3-class
  system carried throughout, zero unlabeled rules), 7-field frontmatter
  (id/type/status/owner/scope/anchors/verified per ratified R2) = **the FIRST frontmatter in
  docs/** — post-authoring census **1/519** (line-1 `---` scan; DOC_STANDARDS.md the sole
  carrier). "How to amend" = §20 (draft-phase path via Design Record dated amendments;
  frozen-phase path via owner-gated Amendments register; closed-set changes always
  amendment-gated; architecture/product locks route to new ADRs).
- **§6.2 required-content register — 21/21 rows satisfied (main-thread):** philosophy→§1 ·
  hierarchy+conflict rules→§2 · typology→§3 · README/GUIDE→§4 · knowledge cards→§5 · audience
  registers→§6 · ADR relationship→§7 · memory relationship→§8 · cross-app→§9 · mapping
  laws→§10 · ownership→§11 · lifecycle→§12 · 7-field metadata→§13 · naming→§14 · linking→§15 ·
  generated/fences/tool-death→§16 · validation→§17 · automation hooks→§18 · phase interfaces
  6–22→§19 · own metadata block (first frontmatter)→lines 1–9 · how-to-amend→§20. No
  owner-approved N/A needed.
- **§5 link proof:** every markdown link target opened via existence check — **38/38 unique
  targets resolve** (61 total link instances); sole scanner hit "path" = the backticked
  `[text](path)` syntax literal in §15, not a link. Zero broken links.
- **§5 non-contradiction proof (all six tier-1 locks consulted main-thread at source):**
  PDD · adr/README (+ADR sweep: none has documentation as subject) · MANUFACTURING_V1_FREEZE ·
  ARCHITECTURE_V2 (no documentation-governance section) · PRE_S1_DESIGN_ADDENDUM
  ("amends-not-rewrites" — consistent) · FACTORY_OPERATIONS_MASTER. Verdict: DOC_STANDARDS
  subordinates correctly, BUT **three tensions found — every one originates in this contract's
  own frozen §6.1 text (transcribed faithfully), NOT in new authoring; per §16.3 REPORTED,
  not reconciled unilaterally; disposition venue = DOC-2 owner review (Design Record dated
  amendment if a ratified item changes):**
  1. **[MEDIUM] §6 "Business intent changes only via ADR/approved PDD revision"**
     (= contract §6.1.6 verbatim) omits the third sanctioned channel: MANUFACTURING_V1_FREEZE
     header ("new ADR **or an owner ruling recorded in FACTORY_OPERATIONS_MASTER.md §5/§7**")
     + FOM header ("changes via owner ruling/ADR"). FOM §5 owner rulings ARE business-intent
     changes outside ADR/PDD-revision.
  2. **[MEDIUM] §2 T1 "(frozen)" + §11 `frozen` class ("append-only dated
     corrections/amendments only")** vs FOM's owner-sanctioned living-body model ("Changes to
     an approved operation happen HERE first"; v1→v2→v3 incorporation-rewrites). Matters for
     the Phase-7 metadata retrofit: which `owner:` class does FOM (and ARCHITECTURE_V2's
     rolling header) get?
  3. **[LOW] §2 conflict rule "ADR wins mechanism"** (= contract §6.1.2) is a lossy
     restatement of PDD "Layering of truth": PDD grants ADRs **and ARCHITECTURE_V2** co-equal
     mechanism-win status.
- **Transcription deltas (disclosed; none alters a ratified rule):** sanctioned-by-§6-preamble
  ratification carry-ins (R2 field names RATIFIED · R4 grain · R5 answer stated · R12
  "no `--fix` ever" from the owner answer verbatim · R9 label on tool-death) + 7
  self-containment clarifications applied to the draft after adversarial review (each
  provenance-labeled, DOC-2 reviewable): U1–U14 definition pointer added to legend ·
  MGT-H glossed + status-file link · §12 note "versioned frozen labels = instances of
  `frozen`" [REPO this contract §4] · §14 "no fifth style" → "no NEW naming style beyond this
  closed set" (arithmetic fix — source lists six styles; rule content unchanged) · §19
  Phase-6 census dual-stated "496 at contract authoring; 518 at DOC-0 re-verification"
  (the bare "518+" under a "transcribed" label was a silent divergence) · §19 post-table
  note covering row-less phases (10, 15–17 remainder, 20) via the parent-preamble clause ·
  backlog #6 linked to DEPLOYMENT_BACKLOG.md.
- **Sub-agent disclosure (U7):** 3 supplemental adversarial verifiers ran (truth-lock
  contradiction hunt · §6.2/fidelity audit · zero-history self-containment review); fidelity
  auditor: ZERO gaps, 21/21 register + 30-phrase load-bearing sweep intact; the 3 truth-lock
  tensions and 7 self-containment items above were **each re-verified main-thread at source
  lines before acceptance** — no verdict rests on a sub-agent alone. No finder failures.
- **Scope discipline:** files changed this sub-phase = `docs/DOC_STANDARDS.md` (NEW) + this
  evidence section + status file + memory — the §9 allowlist exactly.
  DOCUMENTATION_INDEX/START_HERE NOT touched (DOC-2 wiring) · zero code · battery NOT run
  (never runs this phase, §13) · canonical_manifest.json untouched · no drifted doc fixed
  (B.3 register untouched; nothing new observed) · no renames/moves/archives/deletions ·
  zero git writes.
- **Stop conditions:** §16.3 EXERCISED in report-mode for the three inherited tensions
  (reported above, reconciliation deliberately withheld); otherwise §16.1 normal close.
  **Next: DOC-2 — owner reads DOC_STANDARDS.md, disposes the 3 reported tensions
  (+ frontmatter self-note: `type: truth-lock`/`owner: handwritten` is the transient draft
  state, §20.2 specifies the freeze flip), corrections applied, status → `frozen-v1`,
  entry-point wiring (DOCUMENTATION_INDEX row + START_HERE pointer + framework README note),
  phase close (owner-gated).**

## DOC-2 — Owner acceptance → FREEZE (2026-07-13) ✅ — `frozen-v1`; 3 tensions DISPOSED; wiring live → 🏁 PHASE 5 CLOSED

- **Entry state verified per §17.3:** DOC_STANDARDS.md on disk, `status: draft` · Appendix A
  Decision half filled (R1–R12) + Acceptance half `_(pending)_` ×3 + Dated amendments
  `_(none)_` · DOC-1 evidence present · status file → next = DOC-2 → DOC-2 confirmed.
  DOC_STANDARDS.md re-read IN FULL from disk (owner had the artifact open in the IDE at
  review); contract + Design Record + status re-read from disk.
- **Owner acceptance:** order verbatim recorded in the Acceptance half; dispositions decided
  **strictly by contract rules** per that order (§4 truth-locks-upstream · §3.3
  cites-and-subordinates · §20.1 draft-correction path · dated-amendment mechanism for
  ratified items).
- **Tension dispositions (all three RESOLVED by subordination — the standard now defers to
  the truth locks' own wording):**
  1. [MED] §6 change-control → **AMENDED** (direct §20.1 correction, no R-item): the
     freeze-sanctioned third channel (owner ruling recorded in FOM §5/§7) restored, MANUFACTURING_V1_FREEZE
     header cited; FOM §5/§7 verified to exist on disk (lines 271/310).
  2. [MED] §11 frozen-class vs FOM living-body → **AMENDED via dated Design Record amendment
     A1** (alters the R11 gloss): tier membership decoupled from ownership class; the
     `owner:` field records the sanctioned change model, never overrides it — decides the
     Phase-7 retrofit question.
  3. [LOW] mechanism conflict-rule → **AMENDED via dated amendment A2** (alters the R10
     restatement): "ADRs and ARCHITECTURE_V2 win mechanism" restored per PDD "Layering of
     truth" (both the conflict-rules bullet and the T1 "Wins on" column).
- **Frontmatter transient state RESOLVED per contract:** `status: draft → frozen-v1` (§4) ·
  `owner: handwritten → frozen` (§20.2) · `verified: 2026-07-13` current (§20.5) · header
  banner draft→frozen · §20.1 tense historicized · Amendments register label →
  "v1 frozen 2026-07-13" with pre-freeze-corrections pointer. 6 corrections total, itemized
  in the Acceptance half.
- **Entry-point wiring:** DOCUMENTATION_INDEX Entry-points row ADDED (2nd row, after
  START_HERE) · START_HERE map-of-maps pointer ADDED · framework README parent-contract
  linkage VERIFIED ALREADY LIVE (hierarchy §2 + master-index row 5) — untouched.
- **Post-edit verification (all green):** DOC_STANDARDS link proof **40/40** unique targets
  (sole scanner hit = the backticked `[text](path)` literal, §15) · wiring-row targets
  resolve · frontmatter = exactly 7 ratified fields, values valid against the closed sets
  (`frozen-v1` = versioned instance of `frozen` per the §12 note; `owner: frozen` ∈ §11) ·
  frontmatter census still **1/519** (no accidental adoption) · amended sentences quote the
  truth locks' own wording (non-contradiction resolved by construction) · **§3 success
  criteria 7/7**: (1) Record filled both halves ✓ (2) §6.2 register 21/21 stands, DOC-2
  edits removed no section ✓ (3) zero unresolved T1 contradiction — DOC-1 reported per
  §16.3, DOC-2 disposed ✓ (4) provenance labels intact incl. on A1/A2 mirror text ✓
  (5) inheritance + routing live ✓ (6) zero code · zero out-of-allowlist doc edits · battery
  untouched and never run ✓ (7) status file + Design Record + evidence + memory updated ✓.
- **Scope discipline:** files changed at DOC-2 = DOC_STANDARDS.md (8 §20.1 correction edits)
  · DOCUMENTATION_INDEX.md (1 row) · START_HERE.md (1 pointer) · this contract (Acceptance
  half + Dated amendments + this evidence — designated sections) · status file · memory =
  the §9 allowlist exactly. Zero code · battery never ran phase-wide · canonical_manifest
  untouched · B.3 drift register untouched (nothing fixed, nothing new observed) · no
  renames/moves/archives/deletions · zero git writes.
- **Stop conditions:** none triggered (§16.1 normal close). **🏁 PHASE 5 COMPLETE — all §3
  criteria met; DOC_STANDARDS.md is the frozen documentation constitution. Phase-6 gate
  (DOCDISC-0: Phase 5 closed + Standard `frozen-v1`) is now OPEN — execution owner-gated.**
