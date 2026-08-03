---
id: doc-standards
type: truth-lock
status: frozen-v1
owner: frozen
scope: all apps, all features — the documentation system itself
anchors: docs/campaign_contracts/PHASE_05_DOCUMENTATION_FOUNDATION.md
verified: 2026-07-13
---

# DOC_STANDARDS.md — The Documentation Constitution (KOS v3)

> **Status: 🔒 `frozen-v1`** — authored at Phase-5 DOC-1 (2026-07-13) from the owner-ratified
> KOS v3 design; **accepted and FROZEN at DOC-2 owner acceptance, 2026-07-13** (acceptance
> record: PHASE_05 Appendix A). From this point it is `frozen` ownership class (§11): never
> rewritten; changes ONLY via the owner-gated Amendments register (§20.2). It binds ALL
> documentation work — campaign phases 6–22 and every post-campaign doc change.
>
> **What this document is:** the documentation constitution of the Kapil Enterprises Inventory
> project — philosophy, hierarchy, document typology, layer responsibilities, code→doc mapping
> laws, ownership, lifecycle, metadata, naming, linking, generated-vs-handwritten rules,
> validation philosophy, and the interface every campaign phase (6–22) has with documentation.
> It is the parent standard that documentation phases 6 (Discovery), 7 (Cleanup),
> 8 (Knowledge Graph), 9 (Generation), 14 (knowledge_sync), 18 (Future Feature Documentation
> Updates) and 19 (Deployment Documentation) execute against; phases 10–17 and 20–22 are bound
> by it wherever they produce or modify documentation.
>
> **Design of record:** the seven-element KOS v3 core plus twelve owner-ratified decisions
> (R1–R12, all defaults accepted 2026-07-13), embedded in
> [campaign_contracts/PHASE_05_DOCUMENTATION_FOUNDATION.md](campaign_contracts/PHASE_05_DOCUMENTATION_FOUNDATION.md)
> (Appendix A = Design Record, Appendix B = verbatim design core). This document is the
> materialization of that design; where a future amendment to the Design Record and this file
> disagree, the later dated amendment wins (see §20).
>
> **This file carries the FIRST YAML frontmatter in docs/** (adoption was 0/518 at authoring —
> greenfield). Its own metadata block above is the reference instance of the §13 7-field core.

## Provenance legend (mandatory on every rule in this document)

Every rule below traces to exactly one of three provenance classes — no unlabeled invention:

| Label | Meaning |
|---|---|
| `[KOS-v3]` | From the owner-frozen seven-element KOS v3 design core (Appendix, below) |
| `[REPO <path>]` | Codification of an existing repo convention, citing the file(s) that prove it |
| `[PROPOSED→R#]` | Reconstructed/new default, **ratified** under Design Record item R# (all R1–R12 ratified as defaults, owner order 2026-07-13) |

Campaign invariants referenced throughout this standard (U5 battery, U6 docs-sync, U11
evidence-over-assertion, U12 backlog discipline, U14 migration gate) are defined in the
campaign framework: [campaign_contracts/README.md](campaign_contracts/README.md), U1–U14
table.

---

## §1 Philosophy `[REPO + KOS-v3]`

1. **Docs are the resumability substrate.** Any session, any AI, any human resumes from
   documentation alone — the deployment campaign itself is the proof
   (`[REPO docs/campaign_contracts/README.md, docs/DEPLOYMENT_CAMPAIGN_STATUS.md]`).
2. **Drift is an architecture bug.** Code change ⇒ docs change, same session
   (`[REPO CLAUDE.md rule 12; docs/LEARNING_2_0/LIVING_DOCUMENTATION_SYSTEM/CHANGE_IMPACT_MATRIX.md (PKALS-LIVE); campaign invariant U6]`).
   A stale doc is a defect with a register, not an annoyance.
3. **One canonical doc per topic.** Every question has exactly ONE authoritative answer
   document; everything else routes to it
   (`[REPO docs/LEARNING_2_0/AI_AGENT_GUIDE/canonical_manifest.json "how_to_use"; docs/START_HERE.md]`).
4. **Docs are the map; code + truth locks are the territory.** PKALS "routes you to
   code/tests/ADRs — it is not the source of truth, it is the map"
   (`[REPO docs/LEARNING_2_0/README.md]`). Exception: tier-1 truth locks
   ([PDD](PRODUCT_DESIGN_DOCUMENT.md) = product truth; [ADRs](adr/README.md) = mechanism truth).
5. **Dual-register by default.** Operational docs serve the junior developer AND the owner
   (Hinglish welcome — `[REPO config/expense/README.md]` precedent) AND the AI agent
   (token-cheap routing).
6. **Evidence over assertion** (`[REPO campaign invariant U11, docs/campaign_contracts/README.md]`).
   Claims about system behavior carry probe artifacts; receipts and certifications are
   append-only.
7. **Nothing binding lives only in memory or chat.** Agent memory is a convenience mirror
   (`[REPO campaign contracts §12 pattern]`). The KOS design itself nearly dying in chat is the
   founding incident of this rule (PHASE_05 Appendix B provenance note).
8. **Lazy-load layering.** Entry docs stay small and route; deep context loads only when
   needed (`[REPO CLAUDE.md header pattern]`).

## §2 Hierarchy — tiers and conflict rules `[REPO, tiers formalized: PROPOSED→R10]`

| Tier | Class | Members (today) | Wins on |
|---|---|---|---|
| T0 | Entry / routing | [START_HERE](START_HERE.md) · [DOCUMENTATION_INDEX](DOCUMENTATION_INDEX.md) · [PROJECT_KNOWLEDGE_MAP](PROJECT_KNOWLEDGE_MAP.md) · [canonical_manifest.json](LEARNING_2_0/AI_AGENT_GUIDE/canonical_manifest.json) · [CLAUDE.md](../CLAUDE.md) | where to read |
| T1 | Truth locks (frozen) | [PDD](PRODUCT_DESIGN_DOCUMENT.md) · [ADRs 0001–0011](adr/README.md) · [MANUFACTURING_V1_FREEZE](MANUFACTURING_V1_FREEZE.md) · [ARCHITECTURE_V2](ARCHITECTURE_V2.md) · [PRE_S1_DESIGN_ADDENDUM](PRE_S1_DESIGN_ADDENDUM.md) · [FACTORY_OPERATIONS_MASTER](FACTORY_OPERATIONS_MASTER.md) · frozen design/requirement docs | WHAT is true (product intent: PDD · mechanism: ADRs + ARCHITECTURE_V2) |
| T2 | Canonical topic/system docs | [SYSTEM_DESIGN](../SYSTEM_DESIGN.md) · [GLOSSARY](../GLOSSARY.md) · [UI_COMPONENTS](../UI_COMPONENTS.md) · docs/production/* incl. [RBAC](production/RBAC.md) · [CHOKEPOINTS pages](LEARNING_2_0/CHOKEPOINTS/README.md) | HOW a subsystem works |
| T3 | App layer | `config/<app>/README.md` + `docs/apps/<app>/GUIDE.md` (index: [apps/README.md](apps/README.md)) | one app's business view + file map |
| T4 | Feature / URL layer (KOS, new) | `docs/features/*` + URL knowledge cards (built in Phase 9; does not exist yet) | cross-app feature aggregation + per-route routing |
| T5 | Operational / live state | status files · backlogs · certifications · campaign contracts · SOAK_TRACKER | current state + procedure |
| T6 | Learning | [LEARNING/ lessons](LEARNING/README.md) · [LEARNING_2_0 academy layers](LEARNING_2_0/README.md) | teaching |
| T7 | Receipts / evidence | `*_EXECUTION_PLAN` with results · `*_RECEIPT_*` · certification evidence | what actually happened |
| T8 | Archive | [docs/archive/](archive/README.md) | history only |

**Conflict rules** (existing rules restated + completed):

- PDD wins business intent · **ADRs and ARCHITECTURE_V2 win mechanism**
  (`[REPO docs/PRODUCT_DESIGN_DOCUMENT.md "Layering of truth"; CLAUDE.md; docs/adr/README.md]`
  — restored to the PDD's own wording at DOC-2; Design Record dated amendment **A2**,
  2026-07-13).
- Status file wins *state*, contract wins *procedure*, evidence wins *observation*
  (`[REPO docs/campaign_contracts/README.md]`).
- PROJECT_KNOWLEDGE_MAP wins overview conflicts (`[REPO docs/START_HERE.md]`).
- Lower-tier docs cite upward and never override; generated T4 artifacts NEVER win over
  T1–T3 — they cite `[PROPOSED→R10]`.

## §3 Canonical document types — the closed typology `[REPO, typology formalized: PROPOSED→R11]`

A doc's `type` metadata field takes exactly one of:

`entry-index` · `truth-lock` · `adr` · `topic-canonical` · `app-readme` · `app-guide` ·
`feature-doc` · `url-card` · `page-contract` · `data-flow` · `request-journey` ·
`chokepoint` · `database-guide` · `lesson` · `receipt` · `evidence-cert` ·
`campaign-contract` · `status-anchor` · `machine-index` (json) · `archive-record`.

**New types require a DOC_STANDARDS amendment** (owner-gated once frozen, §20).

## §4 README responsibilities `[REPO docs/apps/README.md, config/expense/README.md]`

- **`config/<app>/README.md`** = the app's **business view, code-adjacent, dual-register**:
  purpose · one-sentence business responsibility · tables-created table ("one row means /
  lifecycle") · data-flow diagram · invariants and money rules · dated hardening narratives.
  It is NEVER a file-by-file map (that is the GUIDE) and never machine-generated.
- **Root README** = repo front door.
- **`docs/apps/<app>/GUIDE.md`** = developer's file-by-file map: per-directory tables,
  ★ marks chokepoint/sole-writer files, header cross-links to the business README + governing
  🔒 docs. Example: [apps/expense/GUIDE.md](apps/expense/GUIDE.md).
- **New code file ⇒ GUIDE table row, same session** (`[REPO CLAUDE.md rule 12]`).

## §5 Knowledge Card responsibilities `[KOS-v3 + PROPOSED→R4]`

A URL knowledge card is the **smallest routable knowledge unit**, keyed by URL name. It
answers, for one route:

- route/mount · view · gate(s) (mixin + SidebarItemRule + service re-gate) · services invoked ·
  models written (naming the single writer) · governing docs (page contract, flow, journey,
  ADR) · mobile strategy.

Cards ROUTE and SUMMARIZE with citations; **they are never truth**. Cards are `generated` or
`hybrid` class (§16), produced in Phase 9 from the knowledge graph. Until Phase 9 ships,
**[URL_ATLAS.md](LEARNING_2_0/URL_ATLAS.md) remains the interim canonical** for route
knowledge. Grain: **one card per URL_ATLAS row** `[PROPOSED→R4]`.

## §6 Audience registers `[REPO]`

- **Business documentation:** [PDD](PRODUCT_DESIGN_DOCUMENT.md) (product truth) ·
  [GLOSSARY](../GLOSSARY.md) · [FACTORY_OPERATIONS_MASTER](FACTORY_OPERATIONS_MASTER.md) ·
  business flows ([stage_earnings_flow](LEARNING_2_0/DATA_FLOWS/stage_earnings_flow.md),
  [fnf_business_flow](LEARNING_2_0/DATA_FLOWS/fnf_business_flow.md)) · owner-register sections
  of app READMEs. Business intent changes only via the truth-lock-sanctioned channels: a new
  ADR, an approved PDD revision, or an owner ruling recorded in
  [FACTORY_OPERATIONS_MASTER](FACTORY_OPERATIONS_MASTER.md) §5/§7
  (`[REPO docs/MANUFACTURING_V1_FREEZE.md header change-control]` — third channel restored at
  DOC-2, tension 1 disposition).
- **Developer documentation:** [SYSTEM_DESIGN](../SYSTEM_DESIGN.md) · app GUIDEs ·
  [DATABASE_GUIDE](LEARNING_2_0/DATABASE_GUIDE/README.md) ·
  [DJANGO_GUIDE](LEARNING_2_0/DJANGO_GUIDE/README.md) ·
  [CHOKEPOINTS](LEARNING_2_0/CHOKEPOINTS/README.md) · [UI_COMPONENTS](../UI_COMPONENTS.md) ·
  [PAGES contracts](PAGES/README.md) ·
  [DATA_FLOWS](LEARNING_2_0/DATA_FLOWS/README.md)/[REQUEST_JOURNEYS](LEARNING_2_0/REQUEST_JOURNEYS/README.md).
- **AI documentation:** [CLAUDE.md](../CLAUDE.md) ·
  [AI_AGENT_GUIDE](LEARNING_2_0/AI_AGENT_GUIDE/README.md) +
  [canonical_manifest.json](LEARNING_2_0/AI_AGENT_GUIDE/canonical_manifest.json) · campaign
  contracts · (Phase 8+) knowledge_graph.json. **Law: no AI-only truth** — every binding rule
  readable by machines must also exist in human-readable form; machine indexes are generated
  views or CI-guarded mirrors, never sole records.
- **Learning documentation:** [LEARNING/](LEARNING/README.md) `NN_TOPIC.md` lessons (generic
  concepts) · [LEARNING_2_0 academy](LEARNING_2_0/README.md) (project-specific why/how).
  Teaching register; routes to truth, never holds it.

## §7 ADR relationship `[REPO docs/adr/README.md]`

ADRs are **append-only, immutable, supersede-not-rewrite**, numbered `NNNN-kebab-slug`.
Format: Status · Context · Decision · Consequences (+ observed extensions: Source,
guardrails). This standard is **subordinate to every ADR** and must link rather than restate
(link-don't-fork prevents truth divergence). Any decision surfaced during documentation
phases that locks architecture or product behavior routes to a **NEW ADR** — documentation
phases never lock decisions inside documentation-system files. PKALS-v2-style proposal packs
([pkals_v2/](pkals_v2/PKALS_V2_ARCHITECTURE.md)) are explicitly NOT ADRs and bind nothing.

## §8 Memory relationship `[REPO campaign contracts §12 pattern]`

Agent memory (any vendor) is a **per-agent convenience mirror**. Binding order: **on-disk
docs > memory**; a contradiction is a finding
(`[REPO docs/campaign_contracts/README.md conflict rule]`). Nothing may exist ONLY in
memory — the standing test: *"could a memory-less agent execute from docs alone?"* Every
phase contract carries a §12 memory rule with the "agents without memory: skip" clause.
Memory files may cite docs; **docs never cite agent memory**.

## §9 Cross-app documentation `[REPO + KOS-v3]`

Cross-app knowledge lives in exactly four places:

1. [DATA_FLOWS](LEARNING_2_0/DATA_FLOWS/README.md) — write paths;
2. [REQUEST_JOURNEYS](LEARNING_2_0/REQUEST_JOURNEYS/README.md) — call chains
   (16-section template);
3. [CHOKEPOINTS](LEARNING_2_0/CHOKEPOINTS/README.md) — single-writer services (one page per
   manifest `never_modify` writer);
4. the **features/ layer** `[KOS-v3]` — a feature = the primary aggregation key spanning apps;
   seed = [PROJECT_BRAIN/FEATURE_INDEX.md](LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md).

Import boundaries (`config/.importlinter`, AI_AGENT_GUIDE boundary rules) are documented at
T2. **An app doc never narrates another app's internals** — it links the flow/journey/feature
doc.

## §10 Code→doc mapping laws `[KOS-v3 + REPO + PROPOSED→R4/R5]`

| Code object | Must map to | Completeness instrument |
|---|---|---|
| URL (every live route) | exactly ONE url-card (Phase 9+; interim: [URL_ATLAS](LEARNING_2_0/URL_ATLAS.md) row) + membership in ≥1 feature | route census (MGT-H — the campaign's Phase-2 route-census instrument, 528 routes at last count; [DEPLOYMENT_CAMPAIGN_STATUS](DEPLOYMENT_CAMPAIGN_STATUS.md)) vs card/atlas inventory |
| Model (every concrete model) | owning app README "one row means" row + DATABASE_GUIDE/GUIDE coverage; append-only/money tables ADDITIONALLY a chokepoint page naming the sole writer | model census vs rows |
| Service (every service module) | app GUIDE row; single-writer services ADDITIONALLY: CHOKEPOINTS page + manifest `never_modify` entry | service census vs GUIDE/CHOKEPOINTS |
| View | documented at URL grain (its card/atlas row), file grain (GUIDE row); significant pages ADDITIONALLY a PAGES 10-section contract | view census vs rows |

Mapping completeness is **MEASURED in Phase 6, ENFORCED by Phase 14 knowledge_sync, and
NEVER assumed**. Known gap example at authoring: CHOKEPOINTS lacks a history_service page
(drift register, PHASE_05 Appendix B.3 — registered, not fixed here).

## §11 Documentation ownership `[PROPOSED→R11, precedent: docs/LEARNING_2_0/LIVING_DOCUMENTATION_SYSTEM/OWNERSHIP_MATRIX.md]`

Every doc declares exactly one ownership class in metadata (`owner` field):

| Class | Meaning |
|---|---|
| `handwritten` | Human/agent-authored; machines never write it |
| `generated` | Machine-owned in full; regenerated from the graph; hand edits forbidden and overwritten; carries a generated-banner |
| `hybrid` | Handwritten body + KOS:GEN fenced generated sections (§16) |
| `frozen` | Truth locks; append-only dated corrections/amendments only |
| `append-only` | Receipts, evidence, certifications — closed sections never edited, corrections appended |

**Tier membership does not force ownership class** (Design Record dated amendment **A1**,
2026-07-13): a T1 truth lock whose OWN owner-sanctioned change control permits in-body owner
rulings (precedent: [FACTORY_OPERATIONS_MASTER](FACTORY_OPERATIONS_MASTER.md) §5/§7 under
[MANUFACTURING_V1_FREEZE](MANUFACTURING_V1_FREEZE.md) change control) is classed at the
Phase-7 metadata retrofit by that sanctioned model — truth-lock governance is upstream of
this standard (§1.4/§7 mirror); the `owner:` field records the ACTUAL sanctioned change
model, never overrides it.

The existing [OWNERSHIP_MATRIX](LEARNING_2_0/LIVING_DOCUMENTATION_SYSTEM/OWNERSHIP_MATRIX.md)
(doc → human owner + update trigger) is **extended, not replaced**, when Phase 7 touches it.

## §12 Documentation lifecycle `[REPO archive convention + DOCUMENT_ARCHIVE_REVIEW taxonomy]`

`draft → active → (frozen) → superseded → archived`, plus **`remove-later`** (delete only
after soak + explicit owner sign-off — never before). Versioned frozen labels
(`frozen-v1`, `frozen-v2`, …) are dated instances of the `frozen` state
(`[REPO campaign_contracts/PHASE_05_DOCUMENTATION_FOUNDATION.md §4 — this file itself flips draft → frozen-v1 at DOC-2]`).

Transitions:

- Supersession NAMES the successor and stamps the banner:
  `> **ARCHIVED <date>** — superseded by <successor>. Kept for history.`
- Archived files move under [docs/archive/](archive/README.md) **AND** gain an archive-index
  row (**both, always** — the 12-rows-vs-104-files state at authoring is the counterexample;
  registered for Phase 7 via [DOCUMENT_ARCHIVE_REVIEW](DOCUMENT_ARCHIVE_REVIEW.md)).
- **Truth is never deleted; it is superseded.**
- Receipts/evidence are born `append-only` and skip `draft`.
- Lifecycle state lives in the metadata `status` field (§13).

## §13 Metadata — the 7-field core `[KOS-v3 count; fields PROPOSED→R2]`

KOS v3 fixes the count at **seven**; the field names below are RATIFIED (R2, 2026-07-13).
YAML frontmatter (this file is the first adopter — 0/518 before it):

```yaml
---
id: stable-kebab-slug            # unique across docs/
type: url-card                   # one of the closed typology, §3
status: active                   # lifecycle state, §12
owner: hybrid                    # ownership class, §11 (+ optional maintainer)
scope: expense, settlement       # apps/features this doc binds
anchors: config/expense/services/settlement_service.py   # code paths documented (drift probes)
verified: 2026-07-12             # last verified-against-code date
---
```

**Adoption strategy** `[PROPOSED→R2]`: mandatory on all NEW docs from Phase-5 execution
onward; retrofit onto ACTIVE-tier docs during Phase 7 (not before); **archive NEVER
retrofitted**. Machine-index files (json) carry the same seven as top-level keys.

## §14 Naming conventions `[REPO, codified; new-artifact names PROPOSED→R8]`

The existing styles are codified as the **closed set**:

| Style | Used for |
|---|---|
| `ALL_CAPS_TOPIC.md` | root/system topic docs |
| `*_YYYY_MM_DD.md` | dated receipts/audits |
| `PHASE_NN_SLUG.md` | campaign contracts |
| `lowercase_snake.md` | flow/page/card files |
| `NN_TOPIC.md` | LEARNING lessons |
| `NNNN-kebab-slug.md` | ADRs |

New KOS artifacts (RATIFIED, R8): `docs/DOC_STANDARDS.md` (this file) ·
`docs/features/<feature_slug>/README.md` (feature doc) ·
`docs/features/<feature_slug>/<url_name>.md` (url-cards) · `docs/knowledge_graph.json`
(Phase 8). **No new naming style beyond this closed set without a DOC_STANDARDS
amendment** (§20).

## §15 Linking conventions `[REPO]`

- Relative markdown links, always to the **CANONICAL** doc (never to a copy).
- `[text](path)` clickable form, not bare backticks.
- Section anchors for deep links.
- Archived docs are linked only via their supersession banners or the archive index —
  **active docs never cite archive as truth**.
- `[[wiki-links]]` are an agent-memory idiom and **never appear in docs/**.
- Every active doc must be reachable from [DOCUMENTATION_INDEX](DOCUMENTATION_INDEX.md) or a
  parent index (orphan = Phase-6 finding).
- Link integrity of machine-indexed paths is CI-guarded
  (`[REPO core.tests PkalsNavigationGuardTests]` precedent; extended by Phase 14).

## §16 Generated vs handwritten `[KOS-v3 + pkals_v2 stance; fence syntax PROPOSED→R6]`

- **Fence syntax** (RATIFIED, R6):

  ```html
  <!-- KOS:GEN begin section=<name> generator=<tool> source=knowledge_graph.json generated=<ISO-date> -->
  …generated content…
  <!-- KOS:GEN end section=<name> -->
  ```

  Note: a pre-registered dated-amendment REQUEST exists on the `generated=<ISO-date>`
  attribute (determinism concern); its disposition belongs to Phase-9 GEN-0, not here
  (Design Record R6 note).
- Humans/agents **never edit inside a fence**; generators **never write outside one**. A
  `generated`-class doc is one fence with a banner; a `hybrid` doc mixes fenced and
  handwritten sections.
- **Prose is never machine-rewritten** `[PROPOSED→R7]`. The pkals_v2 law
  "detect-and-notify, never auto-rewrite" (`[REPO docs/pkals_v2/PKALS_V2_REQUIREMENTS.md]`)
  is adopted **permanently for PROSE**; KOS generation produces STRUCTURAL content (tables,
  indexes, cards, cross-reference lists) from the graph. This reconciles pkals_v2's
  "auto-generation NOT WORTH" verdict with KOS v3 generation: structural generation licensed;
  prose never machine-rewritten (RATIFIED, R7).
- **Graceful tool-death degradation** `[KOS-v3 + PROPOSED→R9]`: every generated artifact must
  remain valid, readable, hand-editable static markdown if the tooling never runs again.
  **No doc may REQUIRE tooling to be read.** If the owner ever declares generation dead,
  generated docs convert to `handwritten` via a dated banner — content survives, the fence
  discipline retires. Binding on every generated artifact (RATIFIED, R9).

## §17 Validation philosophy `[REPO PKALS-LIVE + KOS-v3; dimensions PROPOSED→R12]`

**Drift = bug.** Validation dimensions (RATIFIED, R12):

link integrity · metadata completeness · fence integrity · mapping coverage (§10 censuses) ·
index completeness (no orphans) · staleness (`verified` date vs anchor-file changes) ·
non-contradiction spot-checks.

Until Phase 14: manual, per campaign invariant U6 +
[CHANGE_IMPACT_MATRIX](LEARNING_2_0/LIVING_DOCUMENTATION_SYSTEM/CHANGE_IMPACT_MATRIX.md)
(+ the existing `/impact` and `/find-canonical` repo skills wrapping
`scripts/pkals_canonical.py`). Phase 14 automates **detection**; per the adopted pkals_v2
law, **automation DETECTS and REPORTS — a human or agent judges and writes; a `--fix` flag
must never exist** (R12, aligned with the PHASE_14 contract). Validation failures are
findings under campaign U12 discipline.

## §18 Future automation hooks `[KOS-v3 + REPO pkals_v2 + repo skills; defined-not-built]`

Named hooks, all **documented-not-implemented** until their phase:

- `knowledge_graph.json` builder (Phase 8);
- card/index generators (Phase 9);
- `manage.py knowledge_sync` code⇄graph⇄docs drift detector (Phase 14; **extends — does not
  duplicate** — `scripts/pkals_canonical.py`, the `/find-canonical` + `/impact` skills, and
  PkalsNavigationGuardTests);
- CI-guard extension points.

Every hook is code ⇒ its building phase runs the test battery per campaign invariant U5
(unlike Phase 5, which is docs-only) and obeys U14 if anything needs a migration (none
foreseen).

## §19 Phase interface contracts — what phases 6–22 inherit

`[REPO docs/campaign_contracts/PHASE_05_DOCUMENTATION_FOUNDATION.md §6.1.19 — transcribed]`

| Phase | Interface with this standard |
|---|---|
| 6 Discovery | Census of ALL docs/ md files (496 at contract authoring; 518 at the DOC-0 re-verified census) AGAINST this standard (typology, metadata, mapping, lifecycle, links); inputs: PHASE_05 Appendix B.3 drift register + [DOCUMENT_ARCHIVE_REVIEW](DOCUMENT_ARCHIVE_REVIEW.md); output = findings register, ZERO fixes |
| 7 Cleanup | Executes Phase-6 findings under §12 lifecycle rules (banners, archive index, backlog #6 ([DEPLOYMENT_BACKLOG](DEPLOYMENT_BACKLOG.md) row 6: RBAC.md role table), canonical_manifest refresh — the manifest is CI-guarded, so Phase 7 IS a code-adjacent phase and runs the battery per U5) |
| 8 Knowledge Graph | Builds `knowledge_graph.json` as the **single source for generated documentation** `[KOS-v3]`; node kinds ⊇ {app, url, view, service, model, doc, feature, adr}; edge kinds ⊇ {routes_to, gated_by, calls, writes, documented_by, belongs_to_feature, supersedes, cites} `[PROPOSED→R5]`; canonical_manifest.json stays hand-maintained + CI-guarded until it becomes a GENERATED VIEW of the graph at the Phase-9 conversion (RATIFIED, R5) |
| 9 Generation | Produces url-cards + feature indexes from the graph inside KOS:GEN fences; regeneration must be deterministic (byte-stable for unchanged inputs) |
| 11–13 Dataset/Seeder/Verification | Each engine ships WITH its canonical T2 doc + cards per §10; verification receipts = `append-only` class; seeded DEV worlds referenced by docs must carry stable identifiers |
| 14 knowledge_sync | Implements the §17 detection dimensions; **detect-and-report only** |
| 15–17 Feature builds | U6 + CHANGE_IMPACT_MATRIX bind; a new feature ships with its feature doc + cards + PDD/ADR routing — **"docs-complete" is part of feature-DONE** |
| 18 Future Feature Doc Updates | Syncs PDD/roadmap/feature docs with 15–17 reality under this standard |
| 19–21 Deployment docs + certificate | Runbook = T2 canonical under this standard; readiness certificate = `evidence-cert`, append-only |
| 22 First Git Checkpoint | Commits the documentation corpus; **this file must be `frozen-v1` by then** |

Phases without a row above (10 UI Component Library, 15–17 feature builds beyond the shared
row, 20) hold no dedicated documentation interface; they are bound by this standard wherever
they produce or modify documentation (parent-contract preamble clause,
`[REPO campaign_contracts/PHASE_05_DOCUMENTATION_FOUNDATION.md header]`).

## §20 How to amend this standard

`[REPO frozen-contract amendment pattern, docs/campaign_contracts/README.md; lifecycle §12 applied to itself]`

1. **While `status: draft`** (the authoring period, DOC-1 → DOC-2 — now closed): corrections
   are applied directly at DOC-2 owner review; if a correction alters a ratified Design
   Record item (R1–R12), it is FIRST
   appended to the Design Record
   ([PHASE_05 Appendix A](campaign_contracts/PHASE_05_DOCUMENTATION_FOUNDATION.md), "Dated
   amendments") as a dated amendment, then mirrored here.
2. **Once `status: frozen-v1`** (after DOC-2 owner acceptance): this document is `frozen`
   ownership class (§11) — **never rewritten**. Changes land ONLY as dated entries in the
   **Amendments register** below, owner-approved, each naming: date · what changed · why ·
   the Design Record item touched (if any). The body text is corrected in place ONLY when an
   amendment entry authorizes it, and the entry quotes the before/after.
3. **New document types (§3), naming styles (§14), metadata fields (§13), ownership classes
   (§11), or tiers (§2)** always require an amendment — these are closed sets.
4. Decisions that lock **architecture or product behavior** never land here — they route to a
   new ADR (§7); this standard then cites it.
5. The `verified` frontmatter date is refreshed whenever an amendment lands or a phase
   re-verifies this standard against the landscape.

### Amendments register

**A3 — 2026-07-18 · the permanent feature-documentation protocol (owner-authorized,
"OWNER AUTHORIZATION — PHASE 18 / FFD-E" Phase 5 permanence declaration).**
What: [campaign_contracts/PHASE_18_FUTURE_FEATURE_DOCUMENTATION_UPDATES.md](campaign_contracts/PHASE_18_FUTURE_FEATURE_DOCUMENTATION_UPDATES.md)
**IS the standing feature-documentation protocol** (the contract-is-the-protocol
pattern, PHASE_04 precedent): lifecycle (BEFORE-coding PDD entry/Design Records/slug →
DURING same-session U6 + diff-sync → MERGE-GATE BLOCKER-clean → FEATURE-CLOSE rebuild→
regenerate→registers→certification-sweep → rollback-docs). The six OFFICIAL workflows
(lifecycle · synchronization · certification · audit · ownership · regeneration) are
recorded at [FEATURE_DOC_SYNC_LOG.md](../FEATURE_DOC_SYNC_LOG.md) §FFD-E Permanence
Declaration. Why: Phase 18 completed its acceptance demonstration (FFD-D on Phase 17)
and close-sweep (FFD-E) — the protocol is proven, so this standard now points to it.
Authorized by: owner, 2026-07-18.

_(Prior: none since freeze — v1 frozen 2026-07-13. The pre-freeze DOC-2 corrections,
including Design Record dated amendments A1 (§11 ownership-class/tier decoupling) and
A2 (§2 mechanism co-win), are recorded in PHASE_05 Appendix A and were applied under
§20.1 before freeze.)_

---

## Appendix — the KOS v3 design core (design of record)

`[KOS-v3 — verbatim provenance in PHASE_05 Appendix B.1]`

The seven owner-frozen elements this standard materializes:

1. **features/ layer = the primary aggregation key** of project knowledge.
2. **URL knowledge cards** — per-route knowledge units.
3. **knowledge_graph.json = single source** for generated documentation.
4. **KOS:GEN fences** — generated content lives inside marked fences.
5. **`manage.py knowledge_sync`** — code⇄docs drift detection (built in Phase 14).
6. **7-field metadata core** on documents.
7. **Graceful tool-death degradation** — documentation survives its tooling.

Ratification record: Design Record items R1–R12, all defaults accepted by the owner
2026-07-13 —
[PHASE_05_DOCUMENTATION_FOUNDATION.md Appendix A](campaign_contracts/PHASE_05_DOCUMENTATION_FOUNDATION.md).
