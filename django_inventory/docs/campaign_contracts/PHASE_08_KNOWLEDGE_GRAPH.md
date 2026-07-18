---
id: docs-campaign-contracts-phase-08-knowledge-graph
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 8 Execution Contract — Knowledge Graph

> Authored 2026-07-12 under the contract-first directive. Inherits U1–U14 from
> [README.md](README.md), **every definition of the parent contract
> [PHASE_05_DOCUMENTATION_FOUNDATION.md](PHASE_05_DOCUMENTATION_FOUNDATION.md)** (tiers,
> typology incl. `machine-index (json)`, ownership classes, lifecycle, metadata core,
> mapping laws §6.1.10, generated-vs-handwritten + tool-death rules §6.1.16, phase interfaces
> §6.1.19 — none restated), and the execution outputs of Phases 6–7
> ([PHASE_06](PHASE_06_DOCUMENTATION_DISCOVERY.md) graph-readiness section ·
> [PHASE_07](PHASE_07_DOCUMENTATION_CLEANUP.md) DOCCLEAN-G clean-substrate handoff).
> **Third CHILD contract — deltas only.** "The Standard" = `docs/DOC_STANDARDS.md` (frozen-v1).
> Evidence doc (created at KG-0): `docs/KNOWLEDGE_GRAPH_BUILD_LOG.md`.
> **Precision note on "single source" `[KOS-v3]`:** knowledge_graph.json is the single source
> **for generated documentation** — Phase-9 generators and Phase-14 knowledge_sync consume ONLY
> the graph, never code or docs directly. It is NOT the source of project truth: code + T1
> truth-locks remain the territory; the graph is a machine-readable derivation of them
> (parent §6.1.1-P4). A graph↔truth divergence is ALWAYS fixed at the source, never in the
> graph (§4).

## 1. Phase objective

Build `docs/knowledge_graph.json`: a validated, deterministic, machine-readable derivation of
the project's knowledge — apps, URLs, views, services, models, docs, features, decisions, and
the relationships among them — complete against the Standard's mapping laws, so that Phase 9
can generate documentation from it and Phase 14 can detect code⇄docs drift against it.
Deliverables are the graph, its schema, its builder + validator tooling, and the proof that
rebuilding is byte-stable. **Nothing is generated FROM the graph in this phase** (that is
Phase 9), and the graph adds no runtime behavior to the application.

## 2. Scope

### 2.1 Facts of record (authoring-time; KG-0 re-verifies via the Phase-6/7 outputs)

| Fact | Evidence |
|---|---|
| Design mandate | KOS v3 core element 3: "knowledge_graph.json single source" (parent Appendix B.1); parent §6.1.19 Phase-8 row: node kinds ⊇ {app, url, view, service, model, doc, feature, adr}; edge kinds ⊇ {routes_to, gated_by, calls, writes, documented_by, belongs_to_feature, supersedes, cites} `[PROPOSED→R5, ratified at DOC-0]` |
| Manifest relationship | Phase-5 R5 default: canonical_manifest.json becomes a GENERATED VIEW of the graph "in Phase 8/9", CI guard retained, hand-maintained until then. **This contract defers the conversion to Phase 9** (the manifest-view is a generated artifact = generation-phase work); Phase 8 only PROVES graph ⊇ manifest coverage, read-only (§6.5) — keeping Phase 8 battery-free and honoring the manifest quarantine |
| Substrate | Phase-7 DOCCLEAN-G handoff = cleaned corpus + re-confirmed mapping-law censuses; Phase-6 DOCDISC-F = graph-readiness section (coverage arithmetic, FEATURE_INDEX→features seed per R3, CI-guard constraints) — Phase 8's §2 facts are PRE-BUILT there; a dirty-substrate discovery returns to Phase 7 via dated amendment (PHASE_07 evidence-note rule) |
| Census instruments | route census = programmatic root-URLConf walk (MGT-H precedent, 528 routes then); models via Django apps registry; services/docs via file census + Phase-6 report rows; features via PROJECT_BRAIN/FEATURE_INDEX.md seed + the R3-ratified taxonomy |
| Existing tooling precedent | `scripts/pkals_canonical.py` + `.claude/skills/find-canonical` + `/impact` — read-only-over-truth wrappers (pkals_v2 law "v2 reads v1, never weakens"); no builder/graph precedent exists → KG-D9 |
| Prior graph artifacts | none — `docs/knowledge_graph.json` does not exist; 2 json files in docs/ (manifest + a stray partial inventory) at parent authoring |

### 2.2 In / out

**In:** graph schema authoring (docs/knowledge_graph.schema.json — KG-D1) · source-extraction
census (read-only code introspection + corpus indexes) · builder + validator tooling (location
per KG-D9) · first build · validation suite + determinism proof · consistency proofs against
existing routers (read-only) · certification + Phase-9/14 handoff.
**Out:** generating ANY documentation from the graph (Phase 9 — including the manifest-view
conversion and all KOS:GEN fences) · knowledge_sync / drift automation (Phase 14) · CI-guard
test for the graph (Phase-14 hook by default; adding one now = owner-gated + battery, KG-D9) ·
editing canonical_manifest.json or any corpus doc (a source defect found here = dated Phase-6/7
amendment, never an inline fix) · any application-code change · any DB write (introspection is
read-only shell).

## 3. Success criteria

Phase 8 is DONE when ALL hold:
1. `docs/knowledge_graph.schema.json` exists (KG-D1-ratified schema, versioned) and
   `docs/knowledge_graph.json` validates against it.
2. **Completeness with arithmetic:** node counts reconcile against the census instruments —
   every live URL, view, service module, concrete model, active-tree doc, ADR, app, and
   R3-taxonomy feature is a node; counted, not asserted (mapping laws §6.1.10 made total).
3. **All graph invariants (§6.3) hold**, proven by the validator's recorded run: unique IDs ·
   referential integrity · cardinality rules · supersedes-acyclicity · doc-path existence ·
   no unclassifiable nodes.
4. **Determinism proven:** two independent builds from the same inputs are byte-identical
   (KG-D4 rules); the proof (double-build diff = empty + content hash) is in the log.
5. **Consistency proofs (read-only):** graph ⊇ canonical_manifest topics/paths (every manifest
   canonical resolvable as a doc node + topic routing expressible) · graph ⊇ FEATURE_INDEX ·
   graph agrees with DOCUMENTATION_INDEX tier assignments — divergences are findings routed to
   Phase-6/7 amendments, and the phase cannot close CERTIFIED while an unresolved divergence
   stands.
6. The graph carries its §6.6 meta block (schema_version, content hash, built-from anchors)
   and its ownership/lifecycle declaration (`generated` class — hand-edits forbidden).
7. Zero application-code changes; canonical_manifest untouched; battery baseline untouched and
   NOT re-run (unless the owner-gated KG-D9 CI-guard deviation was invoked — then its
   arithmetic is recorded).
8. Phase-9/14 handoff written (§6.7); status file + memory synced every sub-phase.

## 4. Rules of engagement (deltas beyond U1–U14 + parent)

- **Fix-at-source law:** the graph never "corrects" reality. A divergence between graph inputs
  (code vs docs vs indexes) is a FINDING (dated Phase-6/7 amendment or backlog per U12 if
  code-side) — the graph either represents the current true state or the build stops. No
  massaging, no manual node edits.
- **Hand-edits forbidden forever:** knowledge_graph.json is `generated`-class from birth
  (parent §6.1.11). Every change = rebuild. The validator refuses (fails) a graph whose content
  hash does not match its body.
- **Tool-death degradation (parent §6.1.16 applied):** the graph is plain, readable,
  pretty-printed JSON; consumers must survive its absence (md + code stay authoritative; the
  Phase-9 generators and Phase-14 sync fail soft to "stale graph" warnings, never invent).
  No doc may cite the graph as truth — only as index.
- **Read-only introspection:** census shell runs are read-only (URLConf walk, apps registry);
  no ORM writes, no test client POSTs, no login needed. DB row data is NOT graph content
  (the graph maps structure, not records — DEV-world data stays out).
- Builder/validator scripts follow the pkals_v2 law: they READ code + corpus, they WRITE only
  the graph artifacts + scratchpad reports; they never modify their inputs.
- Naming per parent §6.1.14 (R8-ratified): `docs/knowledge_graph.json` + schema beside it; no
  dated graph copies in the repo (regenerable artifact; history arrives with phase-22+ git).

## 5. Evidence standard

- Every census number: command/introspection snippet + raw count (route walk, model registry,
  file counts) — MGT-H instrument style.
- Completeness: per-node-kind reconciliation table (census count vs node count vs explained
  delta; unexplained delta = stop §16.6).
- Invariants/validation: the validator's full output quoted in the log (pass = named checks
  each with counts; fail = the offending rows).
- Determinism: both build hashes + the empty diff, commands shown.
- Consistency proofs: per-router tables (manifest topic → doc node → verdict; FEATURE_INDEX
  row → feature node → verdict).
- Sub-agent extraction sweeps supplemental (U7): schema decisions, invariant definitions,
  divergence judgments, and the certification = main-thread.

## 6. Methodology

### 6.1 Node taxonomy (KG-D2 default)

Node kinds (closed set v1; extension = KG-D6 policy): `app` · `url` · `view` · `service` ·
`model` · `doc` · `feature` · `adr`. Per-kind required attributes (schema-enforced): every node
carries `id`, `kind`, `label`, `anchors` (repo-relative paths proving existence); kind-specific:
url → route pattern + mount + url_name + gate summary (from the census, informational);
model → app_label, table, single-writer service id where the never_modify registry names one;
doc → path, tier, type, ownership class, lifecycle status (from frontmatter post-Phase-7
retrofit); feature → R3-taxonomy slug + seed source; adr → number + status.

### 6.2 Edge taxonomy (KG-D3 default)

Edge kinds (closed set v1): `routes_to` (url→view) · `gated_by` (url→service|doc describing
the gate — informational, RBAC truth stays in code) · `calls` (view→service) · `writes`
(service→model) · `documented_by` (url|model|service|view|app→doc) · `belongs_to_feature`
(url|doc|service|model→feature) · `supersedes` (doc→doc) · `cites` (doc→doc|adr). Every edge:
`from`, `to`, `kind`, optional `note`. Extraction sources per kind are declared in the schema
annex (URLConf for routes_to; the Phase-6/7-verified doc registers for documented_by/supersedes;
service/model relations from the chokepoint + never_modify registries + GUIDE tables — NOT from
runtime call tracing, which this phase does not do; `calls`/`writes` edges are therefore
declared-coverage, sourced from the certified registers, and marked with their source).

### 6.3 IDs + graph invariants (KG-D2/D4/D5 defaults)

**IDs:** `<kind>:<stable-natural-key>` — `app:<label>` · `url:<namespace>:<url_name>` ·
`view:<module.ClassOrFunc>` · `service:<app>.<module>` · `model:<app_label>.<ModelName>` ·
`doc:<repo-relative-path>` · `feature:<r3-slug>` · `adr:<NNNN>`. Natural keys only — never
positional/auto-increment (rename = new node + supersedes-style continuity note, KG-D6).
**Invariants (validator-enforced, all fatal):**
1. ID uniqueness; 2. referential integrity (every edge endpoint exists); 3. kind-closed sets
(unknown kind = fail); 4. cardinality: url —routes_to→ exactly 1 view · url —documented_by→
≤1 `url-card`-type doc (one-card-per-URL law) · doc —supersedes→ n, but a superseded doc has
exactly one successor (parent §6.1.12 names-the-successor rule); 5. `supersedes` edges acyclic;
6. every doc node's path exists on disk (the PkalsNavigationGuardTests principle, script-level);
7. no node without at least one edge UNLESS its kind permits islands (apps never; a doc island
= orphan signal → finding); 8. completeness floors: node counts ≥ census counts per kind (§3.2).

### 6.4 Deterministic generation (KG-D4 default)

Byte-stability rules: canonical JSON serialization (sorted object keys, nodes sorted by id,
edges sorted by (from, kind, to), fixed indentation, UTF-8, trailing-newline) · **no wall-clock
timestamps in the graph body** · the `meta` block carries `schema_version`, `content_hash`
(hash of the body excluding the hash field itself), and `built_from` anchors (git HEAD string +
corpus file-count + census totals — values that change only when inputs change) · builder
reads no environment-dependent state (no locale/ordering dependence; directory walks sorted).
Proof: build twice, `diff` = empty (§3.4). A nondeterministic input discovered (e.g. unordered
introspection) is fixed in the BUILDER, logged.

### 6.5 Consistency proofs (read-only; the manifest stays untouched)

Graph ⊇ manifest: every canonical_manifest topic's canonical + also[] paths resolve to doc
nodes; the topic routing is expressible as documented_by/cites edges (recorded as a mapping
table — the Phase-9 manifest-view generator's input spec). Graph ⊇ FEATURE_INDEX rows. Graph
tier/type attributes agree with DOCUMENTATION_INDEX + census rows. Divergence = finding routed
out (§4), never absorbed.

### 6.6 Versioning + backward compatibility (KG-D6/D8 defaults)

`meta.schema_version` = semver, starts `1.0.0`. Additive changes (new optional attribute, new
node/edge kind) = minor bump; breaking changes (id scheme, required attributes, kind removal)
= major bump + owner approval + a recorded consumer-migration note (Phase-9 generators and
Phase-14 sync pin the major version and must be updated in the same change that bumps it).
Content revisions (same schema, new build) change only `content_hash` + `built_from`. No graph
history is kept in-repo (regenerable; git history covers it from phase 22).

### 6.7 Phase-9 / Phase-14 handoff (forward compatibility)

The certification writes: (a) the generator input spec — which node/edge selections produce
url-cards, feature docs, index tables, and the manifest-view (from §6.5's mapping table);
(b) the sync contract sketch — which invariants Phase-14 re-checks continuously and what
"drift" means per edge kind (code-side change vs doc-side change vs graph-stale); (c) the
schema/consumer version-pinning rule (§6.6); (d) open items routed to those phases' Design
Records. Phase 9 consumes the graph ONLY through the schema; Phase 14 extends the validator,
never forks it.

## 7. Sub-phase breakdown

Every sub-phase: one session, STOP after (U3); evidence into the build log; battery never runs
(§13; sole exception = owner-invoked KG-D9 deviation).

| # | Scope · Inputs · Outputs · Evidence · Stop deltas |
|---|---|
| **KG-0** — Charter + gate + ratification | Gate: Phase 7 closed (DOCCLEAN-G handoff present; transitively Standard frozen-v1 + clean substrate). Re-verify Phase-6 graph-readiness facts. Owner ratifies KG-D1..KG-D9. Create build-log skeleton. **Outputs:** filled Design Record + verified fact base. **Stop:** gate fails; any KG-D unanswered. |
| **KG-A** — Source-extraction census | Read-only censuses, each with arithmetic: route walk (URLConf) · view census · service-module census · model census (apps registry) · doc census (Phase-6/7 registers + frontmatter) · ADR census · feature taxonomy (R3 seed). Per-kind extraction tables = the builder's input contract. **Evidence:** counts + commands. **Stop:** census diverges materially from the Phase-6/7 handoff numbers (substrate drift → dated amendment + stop). |
| **KG-B** — Schema authoring | Write `docs/knowledge_graph.schema.json` per the ratified KG-D1/D2/D3/D6 decisions (kinds, per-kind attributes, edge shapes, meta block, version). Schema itself carries the §6.6 version. **Evidence:** schema validates against its own examples (one valid + several deliberately-invalid samples shown failing). **Stop:** a schema need contradicts a ratified KG-D answer (→ dated Design-Record amendment, owner). |
| **KG-C** — Builder + first build | Implement the builder at the KG-D9 location (reads code + corpus per KG-A extraction tables; writes only the graph; §6.4 determinism rules); run the first build. **Evidence:** builder source path + first-build stats (node/edge counts per kind). **Stop:** builder needs an input the censuses don't provide (back to KG-A as amendment); any temptation to write outside the graph artifacts. |
| **KG-D** — Validator + validation run | Implement the validator (schema check + §6.3 invariants + §3.2 completeness floors + §6.4 determinism double-build); run the full suite. Failures = source findings routed out (§4) or builder fixes (logged), then re-run to green. **Evidence:** full validator output + determinism hashes. **Stop:** an invariant can only pass by hand-editing the graph or a source doc (fix-at-source law → amendment + stop). |
| **KG-E** — Consistency proofs | §6.5 read-only proofs vs manifest / FEATURE_INDEX / DOCUMENTATION_INDEX; produce the manifest-view mapping table (Phase-9 input). **Evidence:** per-router verdict tables. **Stop:** unresolved divergence (cannot certify over it). |
| **KG-F** — Certification + handoff | §6.7 handoff · completeness/invariant/determinism summary · ownership + tool-death declaration recorded in the log and in the graph's DOCUMENTATION_INDEX row · residual register (deferred items → Phase-9/14 Design Records) · PHASE-8 VERDICT. **Stop:** unaccounted census row or open divergence. |

## 8. Deliverables

- `docs/knowledge_graph.json` (validated, deterministic, `generated`-class) +
  `docs/knowledge_graph.schema.json` (versioned).
- Builder + validator tooling at the KG-D9 location (read-only over inputs).
- `docs/KNOWLEDGE_GRAPH_BUILD_LOG.md`: censuses · schema decisions · build stats · validator
  output · determinism proof · consistency tables · certification + Phase-9/14 handoff.
- Filled Design Record (KG-D1..KG-D9); status file + memory updates per sub-phase.

## 9. Files expected to change

**New:** `docs/knowledge_graph.json` · `docs/knowledge_graph.schema.json` ·
`docs/KNOWLEDGE_GRAPH_BUILD_LOG.md` · builder/validator scripts at the KG-D9 location.
**Updated:** `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` · `docs/DOCUMENTATION_INDEX.md` (rows for
the three new docs artifacts, at KG-0/KG-F per §11) · this file (Design Record + dated
amendments) · memory files. **Scratchpad:** census outputs, sample fail-cases.
Nothing else — in particular NO corpus doc edits (findings route to amendments).

## 10. Files that must never change (touching one = STOP + report)

- ANY application file: code, tests, migrations, templates, settings, media, `.env` (the
  builder READS code; it never touches it).
- `canonical_manifest.json` (read-only §6.5 comparison; conversion = Phase 9) and every
  quarantine-class path; `docs/DOC_STANDARDS.md`; T1 truth-lock content; closed
  receipts/reports/logs of phases 6–7 (amendments are dated additions in THEIR files, made
  only per their own rules).
- The corpus at large: Phase 8 writes NO md except its own build log.
- `.claude/` tooling · non-DEV data · the 2 stashes · `.git` state (U2).
- The graph itself, BY HAND, ever (§4 — hand-edit = stop condition, not a shortcut).

## 11. Documentation update rules

At every sub-phase close, same session: (a) build-log section appended (closed sections
append-only, corrections dated); (b) status-file Phase-8 row + dashboard (battery row
untouched unless KG-D9 deviation; docs-sync; memory-sync) + "Next action"; (c)
DOCUMENTATION_INDEX rows: build log at KG-0; graph + schema at KG-F (with `generated`-class
+ "index, not truth" wording); (d) U6 app-doc lookups N/A (no code changes — stated once).

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-8
bullet: sub-phase closed, node/edge counts, schema version, log pointer) + MEMORY.md index
line at each sub-phase close. Agents without memory: skip — the build log + status file are
the complete binding record; the graph and its schema are on-disk artifacts, never
memory-described.

## 13. Battery policy

**Never runs in this phase by default.** No application file is touchable (§10); the builder/
validator live outside the app test surface (KG-D9 default: `scripts/`, mirroring
pkals_canonical.py — `manage.py test` does not collect scripts/). The manifest — the one
docs-side file with a test surface — is read-only here. Sole exception: if the owner invokes
the KG-D9 deviation (a CI-guard test for the graph NOW instead of Phase 14), that change is
test code ⇒ full sequential battery per U5 with arithmetic recorded (expected = entry baseline
+ the new guard's tests).

## 14. Regression policy

- The phase can regress nothing at runtime (no app/test/corpus writes). Its regression surface
  is truth-fidelity: guarded by the fix-at-source law (§4), the consistency proofs (§6.5), and
  the completeness floors (§3.2).
- Validator green = the phase's regression instrument; determinism double-build = the build
  regression instrument.
- Certified truths and closed phase records are inputs, never re-litigated; divergences route
  out as dated amendments (§4).
- No pins (U4 — no fixes; the validator is tooling, not a test-suite pin).

## 15. Rollback policy

- The graph + schema + builder are new files: rollback = delete them (regenerable by
  construction; pre-certification they are `draft` lifecycle in their own meta/log).
- A bad build is overwritten by the next build (no dated copies, §6.6); the log records both
  hashes.
- Builder/validator script mistakes: revert the script file; inputs were never writable.
- The build log + Design Record are append-only (dated amendments).
- Session crash mid-build: artifacts are disposable — next session re-runs KG-A count checks,
  then rebuilds from the last closed sub-phase (the log's state, never memory).

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. KG-0 gate fails (Phase 7 not closed / handoff absent / Standard not frozen-v1) or any
   KG-D1..D9 unanswered at KG-A start.
3. Substrate drift: censuses contradict the Phase-6/7 handoff numbers beyond explained deltas.
4. Fix-at-source violation temptation: a divergence "fixable" only by hand-editing the graph
   or by editing a corpus/source file (route to dated Phase-6/7 amendment or U12 backlog; if
   code-side and money-adjacent, U8 applies).
5. A ratified KG-D answer proves unimplementable as specified (dated Design-Record amendment
   needed — owner).
6. Unexplained completeness delta (census vs nodes) at KG-D/KG-F.
7. Any §10 file would change; any DB write would occur; the builder wants network access
   (it must not).
8. Owner-invoked KG-D9 CI-guard deviation goes battery-red on anything other than the new
   guard's own target behavior.

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-8 row: which KG-* is next.
2. Read `docs/campaign_contracts/README.md` (U1–U14 + environment) → parent
   [PHASE_05_DOCUMENTATION_FOUNDATION.md](PHASE_05_DOCUMENTATION_FOUNDATION.md) → the Standard
   → the Phase-6 report's graph-readiness section + the Phase-7 DOCCLEAN-G handoff → this
   contract → `docs/KNOWLEDGE_GRAPH_BUILD_LOG.md` if it exists (absent ⇒ next = KG-0).
3. Verify read-only: gate state; if the graph exists, run the validator BEFORE trusting it
   (schema check + content hash) — a hash-mismatched graph is treated as absent (rebuild).
4. Re-verify the KG-A census baselines cheaply (route count, model count) — material drift →
   §16.3.
5. No app login, no passwords, no dev server; read-only `manage.py shell` census only
   (framework env facts for the venv path).
6. Execute exactly ONE sub-phase per §7. STOP per §16.
7. Anything inconsistent across status file / Standard / parent / Phase-6/7 records / build
   log / this contract → report before working (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (KG-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| KG-D1 | Graph schema version + artifact | JSON Schema at `docs/knowledge_graph.schema.json`; schema_version semver starting `1.0.0`; graph validates against it | **Default accepted** (owner 2026-07-13; rationale in build log §KG-0) |
| KG-D2 | Node taxonomy | Closed set v1 per §6.1: app · url · view · service · model · doc · feature · adr, with the per-kind attributes listed there; IDs = `<kind>:<natural-key>` per §6.3 | **Default accepted — owner-directed verbatim:** "Adopt the default v1 graph with the currently ratified 8 node kinds. Explicitly record the additional long-term Knowledge Operating System concepts … as additive-minor future candidates only. Do not silently expand the schema. Ensure nothing from KOS_TARGET_VISION is forgotten; anything outside v1 should be recorded as a future Design Record input, not implemented now." → additive-minor future register = build log §KG-0 (deliverable 8) |
| KG-D3 | Edge taxonomy | Closed set v1 per §6.2: routes_to · gated_by · calls · writes · documented_by · belongs_to_feature · supersedes · cites, with declared extraction sources (calls/writes = register-sourced, not runtime-traced) | **Default accepted** (owner 2026-07-13; register-sourcing keeps edges derived from CERTIFIED truth — ADR-0002 single-writer registry, chokepoints, GUIDE tables) |
| KG-D4 | Deterministic generation rules | §6.4: canonical serialization (sorted keys/nodes/edges), no timestamps in body, content_hash + built_from meta, sorted directory walks, double-build byte-identical proof | **Default accepted** (owner: "deterministic, reproducible, evidence-backed") |
| KG-D5 | Graph validation rules | §6.3 invariants 1–8, all fatal; validator output recorded in full; failures route to source findings, never graph edits | **Default accepted** (fix-at-source law absolute) |
| KG-D6 | Backward compatibility policy | Additive = minor bump; breaking = major bump + owner approval + same-change consumer update (Phase-9/14 pin major); node renames = new id + continuity note, never id reuse | **Default accepted** — the additive-minor lane is the RATIFIED vehicle for the KOS_TARGET_VISION concepts (per KG-D2 owner directive) |
| KG-D7 | Ownership of graph nodes | The graph file = `generated` class (machine-owned, hand-edits forbidden, tool-death → frozen-with-banner + consumers fall back to md/code truth); node-level truth ownership stays with the SOURCES (code for structure, docs for documentation attributes, ADRs for decisions) — the graph owns nothing, it derives | **Default accepted** (graph = first-class ARTIFACT per vision §5 while truth-ownership stays at the single canonical sources — SCH preserved) |
| KG-D8 | Graph versioning strategy | §6.6: schema semver + content_hash revisions; no in-repo graph history (regenerable; git covers it from phase 22); consumers pin schema major | **Default accepted** |
| KG-D9 | Builder/validator location + battery implication | `scripts/` (pkals_canonical.py precedent), read-only over inputs, NOT a manage.py command (management commands = phases 12–14 charter), outside the app test surface ⇒ battery never runs; a graph CI-guard test = Phase-14 hook by default — pulling it into Phase 8 is an owner-gated deviation that makes that session battery-bearing | **Default accepted — CI-guard deviation NOT invoked** (battery stays never; guard = Phase-14 hook) |

Date · answered by: **2026-07-13 · Owner (Umesh) — approval order: "Proceed to Phase 8 … Begin with KG-0 ONLY … For KG-D2: Adopt the default v1 graph …" — recorded as Default accepted ×9 with the KG-D2 directive verbatim; no default overridden; per-decision alternatives/rationale/rejections/compatibility = build log §KG-0 Design-Record rationale (owner-required format); NO decision changes the roadmap. Stop §16.2 clear for KG-A.**

## Dated amendments

- **2026-07-13 (KG-D validation, schema patch 1.0.0 → 1.0.1 — validator-proven contract-level
  defect, per the owner's KG-D exception clause "do not modify the schema unless the
  validator proves a genuine contract-level defect"):** the KG-B id regexes were NARROWER
  than the KG-D2-ratified natural-key law. Evidence (3 real nodes failed shape validation):
  (a) `url:media-protected` + `url:media-public` — legitimate NAMESPACE-LESS url names
  containing hyphens; the url pattern's first segment `[a-z0-9_]+` assumed namespace-style
  tokens; (b) `view:allauth...adapter_view.<locals>.view` — a vendor closure qualname with
  `<locals>`, outside `[A-Za-z0-9_.]+`. **Fix (minimal, constraint-WIDENING only — every
  previously-valid id stays valid = backward-compatible patch per KG-D6):** url first segment
  → `[a-z0-9_-]+`; view charset → `[A-Za-z0-9_.<>]*`. Schema `1.0.1`; builder now READS the
  version from the schema file (removes a hardcoded-version drift risk — same defect chain);
  graph rebuilt + full suite re-run. No node/edge content changed; NOT silent — classified in
  the build log §KG-D with the three offending ids quoted.

- **2026-07-13 (KG-E/KG-F merge — owner order):** the owner's KG-E approval directed "KG-E is
  the certification and handoff phase only … certify Phase 8 as complete", merging §7's KG-E
  (§6.5 consistency proofs) and KG-F (§6.7 certification + handoff) into ONE terminal session.
  **No contract content skipped**: §6.5 proofs executed in full (build log §KG-E — zero
  divergences; findings E-1 directory-pointer + E-2 archive-boundary classified, routed to
  GEN-0/recorded) and §6.7 handoff produced in full (build log §KG-F + permanent artifact
  `docs/KNOWLEDGE_GRAPH_CERTIFICATION.md`). Sub-phase ORDER unchanged; only the session
  boundary collapsed, per owner directive verbatim.

# Evidence note

All build evidence lives in `docs/KNOWLEDGE_GRAPH_BUILD_LOG.md` (created at KG-0) — contract =
procedure, log = what was built and proven (framework hierarchy rule). Phase 9 consumes the
graph ONLY through the schema + the KG-F handoff; Phase 14 extends the validator, never forks
it; neither re-derives what the log already proves.
