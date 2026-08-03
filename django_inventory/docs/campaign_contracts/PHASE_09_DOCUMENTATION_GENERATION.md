---
id: docs-campaign-contracts-phase-09-documentation-generation
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 9 Execution Contract — Documentation Generation

> Authored 2026-07-12 under the contract-first directive. Inherits U1–U14 from
> [README.md](README.md), **every definition of the parent contract
> [PHASE_05_DOCUMENTATION_FOUNDATION.md](PHASE_05_DOCUMENTATION_FOUNDATION.md)** (typology,
> ownership classes incl. `generated`/`hybrid`, KOS:GEN fence rules + structural-only law +
> tool-death degradation §6.1.16, card responsibilities §6.1.5, naming §6.1.14, mapping laws
> §6.1.10 — none restated), the execution outputs of Phases 6–7 (cleaned corpus + generation-
> candidate register), and **the Phase-8 contract + its artifacts**
> ([PHASE_08_KNOWLEDGE_GRAPH.md](PHASE_08_KNOWLEDGE_GRAPH.md): the graph, its schema, the KG-F
> generator input spec + manifest-view mapping table, the schema-major pinning rule).
> **Fourth CHILD contract — deltas only.** "The Standard" = `docs/DOC_STANDARDS.md`
> (frozen-v1). Evidence doc (created at GEN-0): `docs/DOCUMENTATION_GENERATION_LOG.md`.

## 1. Phase objective

Generate every machine-generated documentation artifact from `docs/knowledge_graph.json` —
URL knowledge cards, the features layer, generated indexes, fenced structural sections in
hybrid docs, and the manifest-derived view — deterministically, validated, and clearly marked,
so that the corpus's structural knowledge is regenerable from the graph while every
handwritten doc remains authoritative and untouched outside its fences. Phase 9 is the KOS
"GEN" in KOS:GEN: after it, structural documentation is maintained by regeneration, not by
hand-editing.

## 2. Scope

### 2.1 Generation philosophy (normative; all derived)

1. **The graph is the ONLY machine input.** Generators read `knowledge_graph.json` (through
   its schema, pinned to the schema major) and their templates — never code, never other docs
   (single-source discipline, PHASE_08 header + KG-F spec). A generator needing data the graph
   lacks = a graph gap → dated Phase-8 amendment, never a side-channel read.
2. **The graph is NOT project truth** (PHASE_08 precision note). Generated docs therefore
   carry derived knowledge only: they route and summarize with citations; they never assert
   what a truth-lock or the code does not (parent §6.1.5 cards-are-never-truth).
3. **Handwritten docs remain authoritative.** Generation is structural-only (parent §6.1.16:
   prose is never machine-rewritten — the pkals_v2 detect-don't-rewrite law); hybrid docs are
   written ONLY inside their fences; a `handwritten`-class doc is never touched by a generator.
4. **Generated docs are disposable.** Every `generated`-class artifact is fully reproducible
   from graph + templates; deleting one loses nothing (rollback = regenerate).
5. **Regeneration replaces manual editing.** The maintenance path for generated content is:
   fix the SOURCE (code/docs/frontmatter) → rebuild the graph (Phase-8 builder) → regenerate.
   **Fix-at-source law** (PHASE_08 §4) extends to outputs: a wrong generated doc is never
   hand-patched.
6. **Deterministic generation:** identical graph + identical templates ⇒ byte-identical
   outputs (§6.4). No wall-clock timestamps in any generated body or fence (§6.5 — dates live
   in the generation log only).
7. **Tool-death graceful degradation** `[KOS-v3]`: every output is plain markdown, readable
   and hand-editable if generation dies forever; conversion path = parent §6.1.16 (owner
   declares generation dead → generated docs re-class to `handwritten` via dated banner).
   No reader workflow may REQUIRE the generator to exist.

### 2.2 Generated outputs (GEN-D2 tiers)

**v1 MANDATORY (design-of-record targets — parent §6.1.19 Phase-9 row + R4/R8 + KG-F):**
- **URL knowledge cards** — one per URL (R4 grain), content per parent §6.1.5 (route, view,
  gates, services, models-with-sole-writer, governing docs, mobile note where the graph
  carries it), at `docs/features/<feature_slug>/<url_name>.md` (R8).
- **Feature documentation + feature indexes** — `docs/features/<slug>/README.md` per
  R3-taxonomy feature (member cards, apps touched, governing docs) + the features master
  index.
- **Manifest-derived output** — `canonical_manifest.json` converted to a GENERATED VIEW of
  the graph (the R5 default, deferred here by PHASE_08 §2.1): same consumer contract
  (`entry`/`topics`/`never_modify`/`hard_rules` semantics preserved — never_modify/hard_rules
  content changes remain owner-gated exactly as in PHASE_07 §6.6c), CI guard retained,
  ownership flips to `generated`. **Battery-bearing; isolated in GEN-D (§7).**
**v1 OWNER-ACTIVATED (owner-listed 2026-07-12; scope ratified at GEN-D2):** app summaries ·
model summaries · service summaries · view summaries · navigation indexes — realized as
**KOS:GEN fenced sections inside the existing owning canonicals** (GUIDE file-tables, index
tables, URL_ATLAS-class tables — the DOCDISC-F generation-candidate register names them), NOT
as parallel new files (a parallel summary file would violate one-canonical-per-topic;
fencing into the canonical preserves it — GEN-D8).
**Future targets:** added only via GEN-D9's extension rule.
**Supersession note:** where a generated artifact fully replaces a handwritten one
(URL_ATLAS-class), the replacement is owner-gated at GEN-D2 and executes with PHASE_07 §6.4
mechanics (banner, index row, inbound rewrite, no stubs) inside GEN-E.

### 2.3 In / out

**In:** templates + render pipeline (GEN-A) · generating the §2.2 targets · the manifest-view
conversion (GEN-D) · validation suite + determinism proofs (GEN-E) · corpus integration
(index/START_HERE routing rows; owner-gated supersessions) · certification + handoffs (GEN-F).
**Out:** any prose authoring (missing handwritten docs stay with their DC-D1 venues) · graph
or schema changes (Phase-8 amendments) · knowledge_sync/drift automation (Phase 14 — Phase 9
only plants the stale-detection markers §6.6) · application code · new Python dependencies
(GEN-D1 default; adding one = owner-gated) · manage.py commands (phases 12–14 charter) ·
hand-edits to anything generated.

## 3. Success criteria

Phase 9 is DONE when ALL hold:
1. Every GEN-D2-ratified target generated, valid against §6.6 checks, and present at its
   GEN-D8 location with correct metadata (frontmatter `owner: generated` for whole files;
   compliant fence headers for hybrid sections).
2. **Completeness with arithmetic:** generated-set counts reconcile against the graph
   selections from the KG-F input spec (every url node with a card-selection ⇒ exactly one
   card; every feature ⇒ one feature doc; counted, not asserted).
3. **Determinism proven:** full double-run ⇒ byte-identical output tree (diff empty, hashes
   logged); regeneration after a no-op graph rebuild ⇒ zero diffs.
4. **Fence integrity corpus-wide:** every fence well-formed, paired, non-nested; zero
   generator writes outside fences; zero fences in `handwritten`-class docs; hand-edit
   detection mechanism proven (a deliberately mutated fence in a scratch copy is caught).
5. Manifest-view conversion done (if GEN-D2 confirms it): generated manifest byte-stable,
   consumer contract intact, `/find-canonical` + `scripts/pkals_canonical.py` smoke-pass,
   **full battery green** with arithmetic recorded; manifest ownership flipped to `generated`
   in its index row + OWNERSHIP_MATRIX.
6. Corpus integration done: DOCUMENTATION_INDEX + START_HERE route to the features layer;
   interim-canonical handoffs (URL_ATLAS-class) executed per their GEN-D2 ruling; no orphan
   generated files (every output reachable from an index).
7. Version pinning live: outputs record graph content-hash + schema major + template version
   (§6.5); the stale-detection contract for Phase 14 is written (§6.6).
8. Zero handwritten content modified outside fences and owner-gated supersessions — proven by
   a corpus diff census in GEN-F (files changed = generated outputs + fenced sections +
   allowlisted integration rows, nothing else).
9. Status file + memory synced every sub-phase; battery untouched outside GEN-D.

## 4. Rules of engagement (deltas beyond U1–U14 + parent + PHASE_07/08 laws)

- **Validation before generation, always:** no generator runs unless the Phase-8 validator
  passed on the current graph in the same session (stale/hash-mismatched graph = treated as
  absent, PHASE_08 §17.3).
- **Write-fencing:** generators may write ONLY (a) whole files of `generated` class at GEN-D8
  locations, (b) inside existing KOS:GEN fences of hybrid docs. First-time fence insertion
  into a hybrid doc is a HUMAN-reviewed edit (per-file diff review, PHASE_07 batch discipline)
  — the generator fills fences, it does not carve them.
- **Hand-edit-in-fence = refuse + report:** before writing, the generator compares each
  fence's recorded content-hash; a mismatch (someone hand-edited generated content) stops the
  run for that file — the owner decides fold-to-source or discard. Never silently clobbered.
- **Manifest quarantine holds:** outside GEN-D, `canonical_manifest.json` untouched
  (PHASE_07 §4 quarantine, inherited).
- **One target at a time within a session** (PHASE_04 serial discipline adapted): a target
  class is generated → validated → logged before the next class starts.
- Scripts follow the pkals_v2 law: read graph + templates, write only §9 outputs + scratchpad.

## 5. Evidence standard

- Per target class: selection arithmetic (graph query → expected count → produced count) ·
  sample render diffed against its template + graph slice (one per class, hand-verified) ·
  validation output quoted.
- Determinism: double-run tree hashes + empty diff, commands shown.
- Fence integrity: scanner output (counts of fences checked / passed / failed) + the
  hand-edit-detection proof.
- GEN-D: manifest diff summary + consumer-contract check (topic routing equivalence table
  from the KG-E mapping table) + smoke outputs + battery arithmetic.
- Corpus-diff census at GEN-F: every changed file accounted to a target class or an
  allowlisted integration row.
- Sub-agent renders/sweeps supplemental (U7): template decisions, per-class sample
  verification, supersession judgments, certification = main-thread.

## 6. Methodology

### 6.1 Generator architecture (GEN-D1/D8 defaults)

Generators live beside the Phase-8 builder/validator (KG-D9 location, `scripts/`), one thin
renderer per target class + a shared render pipeline: load graph → verify schema major +
content hash → apply the KG-F selection for the class → render via templates → serialize with
canonical ordering → validate → write. **Template engine (GEN-D1 default): stdlib-only Python
templating (no new dependency — a dependency addition is a requirements change = owner-gated;
executor may use an engine ONLY if it already exists in `requirements`/venv, verified not
assumed).** Templates are versioned files stored with the generators; template changes bump
the template version (recorded in outputs, §6.5).

### 6.2 Render pipeline determinism (GEN-D4 default)

Sorted selections (by node id), sorted sections, canonical whitespace, LF endings,
trailing-newline; no environment-dependent state; **full regeneration is the default run
mode** — partial/incremental regeneration is permitted only as an optimization whose output
is PROVEN byte-identical to a full run (proof logged each time it is used, else forbidden).

### 6.3 Overwrite policy (GEN-D3 default)

`generated`-class whole files: fully overwritten on every run (they are disposable, §2.1.4).
`hybrid` docs: only fence interiors replaced; text outside fences byte-preserved (verified by
the writer: pre/post diff limited to fence spans). Hand-edit-in-fence → §4 refuse+report.
Deletions: a target removed from the graph ⇒ its generated file is superseded per PHASE_07
§6.4 mechanics (banner + index + inbound rewrite), not silently deleted — ZERO hard deletions
(DC-D3 discipline carried).

### 6.4 Output markers (GEN-D5/D6 defaults)

Whole generated files: frontmatter per the Standard's 7 fields with `owner: generated`,
`type` per typology (`url-card`, `feature-doc`, …), plus a top banner line naming the
generator and the regeneration command. Fenced sections: parent-R6 fence syntax with header
fields `generator=<tool-id> source=knowledge_graph.json graph=<content_hash_prefix>
schema=<major.minor> template=<version>` — **and NO wall-clock date** (a date field would
break §2.1.6 byte-stability; generation dates live in the generation log).
⚠️ **R6 reconciliation:** the parent's R6 default included `generated=<ISO-date>` in fence
headers. That default and determinism cannot both hold. GEN-0 therefore requests a dated
amendment to the Phase-5 Design Record (R6: date → graph-hash/template-version fields) —
flagged honestly here rather than silently diverged (framework corrections rule).

### 6.5 Version pinning (from PHASE_08 §6.6)

Every output records the graph content-hash + schema major it was rendered from + the
template version. Generators refuse a graph whose schema major exceeds their pin (update the
generator in the same change that bumps the major — PHASE_08 consumer rule).

### 6.6 Validation + stale-output contract (GEN-D7 default; Phase-14 interface)

Pre-generation: Phase-8 validator green (§4). Post-generation, per run: completeness
arithmetic (§3.2) · determinism double-run (§3.3) · fence-integrity scan corpus-wide ·
metadata/frontmatter validity on outputs · zero-writes-outside-allowlist diff census ·
graph/template version stamps present and correct. **Stale-output detection contract (built
here, run continuously by Phase 14):** an output whose recorded graph hash ≠ the current
graph's hash is STALE — Phase 14's knowledge_sync reports it (detect-and-notify, never
auto-rewrite; regeneration is a human/agent-ordered act). Phase 14 extends these validators,
never forks them (PHASE_08 §6.7 rule).

### 6.7 Phase interfaces

| Phase | Interface |
|---|---|
| 8 (producer) | Graph + schema + KG-F input spec are read-only inputs; graph gaps = dated Phase-8 amendments; schema-major pinning per §6.5 |
| 14 (knowledge_sync) | Consumes §6.6's stale-output contract + the fence/validator tooling; adds continuous drift detection + (per its own contract) CI-guard integration; never regenerates on its own authority |
| 18 (future feature docs) | New features (phases 15–17) enter docs by: source update → graph rebuild → regeneration; Phase 18's contract may add GEN-D9 targets; hand-written feature prose stays outside fences |
| 19 (deployment docs) | The runbook remains `handwritten`-class T2 (parent §6.1.19); Phase 19 may adopt fenced structural sections (e.g. command/route tables) via GEN-D9 — never whole-file generation of the runbook |

## 7. Sub-phase breakdown

Every sub-phase: one session, STOP after (U3); evidence into the generation log; battery runs
ONLY in GEN-D.

| # | Scope · Inputs · Outputs · Evidence · Stop deltas |
|---|---|
| **GEN-0** — Charter + gate + ratification | Gate: Phase 8 closed (KG-F handoff + validated graph present; transitively 5–7 closed). Owner ratifies GEN-D1..GEN-D9 + the R6 amendment request (§6.4). Create log skeleton; re-verify graph (validator run + hash). **Stop:** gate fails; any GEN-D unanswered; validator red. |
| **GEN-A** — Templates + render pipeline | Author templates per target class (v1 mandatory first) + the shared pipeline; render SAMPLES only (scratchpad): one per class, hand-verified against graph slice + Standard requirements (card content per parent §6.1.5). No corpus writes yet. **Evidence:** sample renders + review notes. **Stop:** a template needs graph data that doesn't exist (→ Phase-8 amendment). |
| **GEN-B** — URL cards + features layer | Generate the features tree (`docs/features/**`: feature READMEs + cards + master index) — the first corpus write of the phase; per-class validation + selection arithmetic; DOCUMENTATION_INDEX/START_HERE routing rows added. **Evidence:** counts + samples + fence/metadata checks. **Stop:** completeness delta unexplained; any write outside GEN-D8 locations. |
| **GEN-C** — Hybrid fenced sections (owner-activated targets) | For each GEN-D2-activated summary/index target: human-reviewed fence carving into the owning canonical (per-file diff review) → generator fills; URL_ATLAS-class supersessions executed per their GEN-D2 ruling with PHASE_07 §6.4 mechanics. **Evidence:** per-file fence diffs + supersession tables. **Stop:** fence would land in a `handwritten`-class doc; supersession lacks its owner gate. |
| **GEN-D** — Manifest-view conversion (BATTERY-BEARING) | One coordinated session: generate the manifest from the graph (KG-E mapping table = spec); consumer-contract equivalence proof (every old topic routes identically or better, never_modify/hard_rules semantics preserved); ownership flip recorded (index row + OWNERSHIP_MATRIX); `/find-canonical` + pkals script smoke; **full sequential battery per U5** (expected = entry baseline; red ⇒ revert session diff wholesale → green → report). **Stop:** equivalence proof fails; battery red after revert; never_modify/hard_rules delta without owner gate. |
| **GEN-E** — Validation suite + integration audit | Full §6.6 suite corpus-wide: determinism double-run, fence integrity, metadata validity, zero-writes-outside-allowlist diff census, stale-marker mechanics proof, orphan check on generated outputs (all index-reachable). **Evidence:** raw suite output. **Stop:** unexplained corpus diff (§16.6). |
| **GEN-F** — Certification + handoff | Completeness/determinism/fence summary · corpus-diff census reconciled · residual register (deferred targets, DC-D1 prose venues untouched) · Phase-14/18/19 handoff (§6.7 obligations written concretely: stale contract, extension rule, regeneration runbook — the "how to regenerate" instructions live HERE and in each output's banner) · PHASE-9 VERDICT. **Stop:** unaccounted output or diff. |

## 8. Deliverables

- The generated corpus layer: `docs/features/**` (cards + feature docs + index), fenced
  sections in GEN-D2-activated canonicals, the generated manifest-view (if confirmed).
- Templates + generators + validation additions at the KG-D9 location (versioned).
- `docs/DOCUMENTATION_GENERATION_LOG.md`: ratifications · sample reviews · per-class
  arithmetic · determinism/fence proofs · manifest conversion evidence + battery number ·
  corpus-diff census · certification + handoffs + the regeneration runbook.
- Filled Design Record (GEN-D1..GEN-D9) + the R6 amendment disposition.
- Updated DOCUMENTATION_INDEX / START_HERE / OWNERSHIP_MATRIX rows per §9; status file +
  memory per sub-phase.

## 9. Files expected to change

**New:** `docs/features/**` (generated tree) · templates/generators beside the Phase-8
tooling · `docs/DOCUMENTATION_GENERATION_LOG.md`.
**Updated:** GEN-D2-activated hybrid canonicals (FENCE INTERIORS + the one-time human-reviewed
fence carving only) · `canonical_manifest.json` (GEN-D ONLY) · OWNERSHIP_MATRIX (ownership
flips) · `docs/DOCUMENTATION_INDEX.md` + `docs/START_HERE.md` (routing/integration rows) ·
URL_ATLAS-class superseded docs (banner per owner-gated ruling) + `docs/archive/**` if a
supersession archives · `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` · this file (Design Record +
amendments) · the Phase-5 Design Record (the R6 dated amendment, at GEN-0, per its own
amendment rules) · memory files. **Scratchpad:** sample renders, suite outputs.
Nothing else — proven by the GEN-F corpus-diff census.

## 10. Files that must never change (touching one = STOP + report)

- ANY application file: code, tests, migrations, templates, settings, media, `.env`.
- `handwritten`-class docs outside allowlisted integration rows; ANY text outside a fence in
  hybrid docs; T1 truth-lock content; `docs/DOC_STANDARDS.md` (except the R6 dated amendment
  in its Design Record, which lives in PHASE_05's appendix, not the Standard body — if the
  ratified Standard text itself must change, that is owner change-control, stop first).
- `knowledge_graph.json` + schema BY HAND (rebuild only, via the Phase-8 builder; graph
  changes = Phase-8 amendments).
- `canonical_manifest.json` outside GEN-D; never_modify/hard_rules semantics without owner
  gate.
- Closed logs/reports of phases 6–8 (amendments are dated additions per their own rules).
- `.claude/` tooling · non-DEV data · the 2 stashes · `.git` state (U2; `mv` never `git mv`).
- NOTHING hard-deleted (supersession mechanics only).

## 11. Documentation update rules

At every sub-phase close, same session: (a) generation-log section appended (closed sections
append-only, corrections dated); (b) status-file Phase-9 row + dashboard (battery row updates
ONLY at GEN-D) + "Next action"; (c) DOCUMENTATION_INDEX: log row at GEN-0, features-layer +
generated-artifact rows at GEN-B/D/E as created (each marked `generated` — "index, not
truth" wording per PHASE_08 §11); (d) OWNERSHIP_MATRIX rows for every new/flipped artifact;
(e) U6 app-doc lookups N/A (no code changes — stated once).

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-9
bullet: sub-phase closed, per-class counts, battery number at GEN-D, log pointer) + MEMORY.md
index line at each sub-phase close. Agents without memory: skip — the generation log + status
file are the complete binding record; regeneration instructions live in the log + output
banners, never only in memory.

## 13. Battery policy

**Exactly one battery-bearing sub-phase: GEN-D** (the manifest-view conversion — the one
generated artifact with a CI test surface, PkalsNavigationGuardTests). There: full sequential
fresh-DB canonical per U5; expected = entry baseline (status dashboard at GEN-0; no pins from
generation); red ⇒ revert session diff → green → report. Every other sub-phase: battery never
runs — generators/templates live outside the app test surface (KG-D9), and the features tree
has no test surface. A battery-relevant surprise outside GEN-D = stop condition §16.7, not a
battery run.

## 14. Regression policy

- The phase's regression surface = the handwritten corpus: guarded by write-fencing (§4), the
  zero-writes-outside-allowlist diff census (§6.6), and the fence-interior-only overwrite
  proof (§6.3).
- Determinism double-run = the generation regression instrument; consumer-contract
  equivalence proof = the manifest regression instrument; PkalsNavigationGuardTests green =
  its CI confirmation.
- Certified truths, closed phase records, and the graph are inputs — never edited to make a
  render work (fix-at-source).
- No pins (U4 — no fixes; generation adds no tests by default; a GEN-D9-extension adding CI
  guards belongs to Phase 14's contract).

## 15. Rollback policy

- `generated`-class outputs are disposable: rollback = delete + regenerate (or simply
  regenerate — overwrite is total, §6.3).
- Hybrid docs: fence interiors regenerate; the one-time fence carving reverts per-file (the
  carving diff is logged both ways).
- GEN-D red: revert the whole session diff (manifest + flips), battery to green, report —
  never leave the tree red between sessions (PHASE_07 §15 rule carried).
- Supersessions reverse per PHASE_07 §15 (mv back + reference-edit revert, both sides logged).
- The generation log + Design Record are append-only (dated amendments).
- Session crash mid-generation: outputs are disposable — next session re-verifies the graph
  (validator + hash), then regenerates the interrupted class from scratch; hybrid docs get a
  fence-integrity check FIRST (a half-written fence is restored from the carving log or the
  fence refilled by a clean run).

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. GEN-0 gate fails (Phase 8 not closed / graph absent / validator red / hash mismatch) or
   any GEN-D1..D9 unanswered (incl. the R6 amendment disposition).
3. A generator needs data the graph lacks, or a template contradicts the Standard/a ratified
   answer (→ dated amendment to the owning contract; never a side-channel).
4. Hand-edit detected inside a fence (§4 refuse+report — owner decides fold-to-source or
   discard).
5. A write would land outside the §9 allowlist, outside a fence, or in a `handwritten` doc;
   or a supersession lacks its owner gate.
6. Unexplained corpus diff at GEN-E/GEN-F (a file changed that no target class accounts for).
7. Battery-relevant surface touched outside GEN-D (manifest quarantine breach).
8. GEN-D battery red after the session-diff revert, or the consumer-contract equivalence
   proof fails.
9. Determinism failure that survives a builder/template fix attempt (nondeterministic input —
   report with the diff).
10. Corpus/graph drift from non-campaign activity mid-phase (hashes diverge unexplained).

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-9 row: which GEN-* is next; battery
   baseline.
2. Read `docs/campaign_contracts/README.md` (U1–U14 + environment) → parent
   [PHASE_05_DOCUMENTATION_FOUNDATION.md](PHASE_05_DOCUMENTATION_FOUNDATION.md) → the Standard
   → [PHASE_08_KNOWLEDGE_GRAPH.md](PHASE_08_KNOWLEDGE_GRAPH.md) + the KG build log (KG-F
   handoff = the input spec) → this contract → `docs/DOCUMENTATION_GENERATION_LOG.md` if it
   exists (absent ⇒ next = GEN-0).
3. Verify read-only: the graph validates (run the Phase-8 validator; hash-mismatched graph =
   absent → Phase-8 rebuild first); template versions vs the log; fence-integrity spot-scan
   if GEN-C has closed.
4. Never trust generated files as state: the log + Design Record are the state; outputs are
   disposable derivations.
5. No app login, no passwords; GEN-D needs only the battery environment (venv + Postgres,
   framework env facts).
6. Execute exactly ONE sub-phase per §7, one target class at a time. STOP per §16.
7. Anything inconsistent across status file / Standard / parent / Phase-8 record / generation
   log / this contract → report before working (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (GEN-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| GEN-D1 | Template engine | Stdlib-only Python templating in the KG-D9 scripts location; NO new dependency (a dependency = requirements change = owner-gated); pre-existing venv engines usable only if verified present | **DEFAULT RATIFIED** (owner proceed-order 2026-07-13; no override) |
| GEN-D2 | Generation targets | v1 mandatory: URL cards + features layer + manifest-view (§2.2); owner-activated: app/model/service/view summaries + navigation indexes as hybrid fences in existing canonicals; URL_ATLAS-class supersessions each individually gated here | **v1 MANDATORY TRIO RATIFIED**; owner-activated lane + URL_ATLAS supersessions **⏸ OI-2/OI-3** (generation log §GEN-0.6 — classified, not assumed). Owner rulings of record bind the lane: hybrid model kept · structural-only · prose permanently handwritten/hybrid · no prose expansion · R7 unchanged |
| GEN-D3 | Overwrite policy | Generated files: total overwrite; hybrid: fence interiors only, outside-fence bytes preserved; hand-edit-in-fence = refuse+report; zero hard deletions (supersession mechanics only) | **DEFAULT RATIFIED** |
| GEN-D4 | Partial regeneration | Full-run default; partial permitted only with a logged byte-equality proof against a full run | **DEFAULT RATIFIED** |
| GEN-D5 | KOS:GEN fence policy | Parent-R6 syntax, headers per §6.4; one fence per section, no nesting; fences never in `handwritten`-class docs; carving = one-time human-reviewed edit | **DEFAULT RATIFIED** (live only if OI-2 activates a hybrid target) |
| GEN-D6 | Generated metadata | Whole files: 7-field frontmatter with `owner: generated` + generator banner + regeneration command; fences: generator/graph-hash/schema/template header fields; **no wall-clock dates in bodies or fences** (dates in the log) — requires the R6 dated amendment (§6.4 ⚠️) | **DEFAULT RATIFIED, contingent on OI-1** (R6 amendment disposition — awaiting owner; recommendation ACCEPT, log §GEN-0.6) |
| GEN-D7 | Validation policy | §6.6 suite: pre-gen validator green, completeness arithmetic, determinism double-run, fence integrity, metadata validity, zero-writes-outside-allowlist census, version stamps; stale-output contract handed to Phase 14 (detect-and-notify only) | **DEFAULT RATIFIED** — with the R-10 law: until Phase 14 ships the temp-path validator, "pre-gen validator green" = the read-only recompute equivalent (log §GEN-0.1 dated deviation note) |
| GEN-D8 | Output directory strategy | R8-ratified features tree for cards/feature docs; summaries as fences in existing owning canonicals (no parallel files, no docs/generated/ ghetto — one-canonical-per-topic preserved); manifest stays at its CI-guarded path | **DEFAULT RATIFIED** (+ `docs/features/_unassigned/` bucket for cards of urls with no feature membership — explicit countable gap surface, log §GEN-0.4 def 8) |
| GEN-D9 | Future extensibility | New target class = template + KG-F-style selection spec + a dated GEN-D2 amendment (owner-gated); phases 14/18/19 add targets only via their own contracts referencing this rule; generators remain graph-only consumers forever | **DEFAULT RATIFIED** + owner permanent ceiling: no extension may ever target prose (ruling of record, log §GEN-0.2) |

Date · answered by: 2026-07-13 · owner proceed-order ("Proceed to Phase 9 … GEN-0 … ratify
the generation architecture" + the five verbatim hybrid/prose/R7 rulings); defaults binding
per this table's own rule. **OI-1..OI-3 DISPOSED by owner 2026-07-13 (generation log
§GEN-0.8, verbatim): OI-1 ACCEPT (R6 dated amendment A3 recorded in PHASE_05 Appendix A;
GEN-D6 contingency resolved) · OI-2 NONE for v1 (owner-activated lane EMPTY; GEN-C =
documented no-op; future activation only via owner-approved Design Record amendment) ·
OI-3 DEFER (URL_ATLAS not superseded; revisit after the generated layer exists on disk).
GEN-0 CLOSED.**

## Dated amendments

- **A1 (2026-07-16, GEN-D — re-scopes §2.2 "Manifest-derived output", §7 GEN-D row, and §13
  for v1; owner GA-F1 ruling Option (b), verbatim authority quoted in
  DOCUMENTATION_GENERATION_LOG.md §GEN-D.4):** For v1 the manifest-view conversion is **NOT
  executed**. `canonical_manifest.json` REMAINS `handwritten` + CI-guarded
  (PkalsNavigationGuardTests unchanged); its ownership does NOT flip; **no `topic` node kind
  is added; Phase 8 is not reopened** — graph, schema, builder, validator, and certification
  remain untouched, certified, and un-rebuilt. **Permanent v1 architectural decision
  (owner-ordered):** the knowledge graph remains the ONLY machine-readable knowledge source
  for generated documentation, EXCEPT the handwritten manifest, which intentionally remains
  outside graph generation for v1. Consequences: the §3.5 success criterion resolves via its
  own conditional ("if GEN-D2 confirms it" — NOT confirmed for v1); **Phase 9 carries NO
  battery-bearing sub-phase** (§13's GEN-D battery obligation lapses with the conversion; the
  battery expectation travels with any future conversion decision); Phase-14's manifest drift
  domain keeps its existing CI guard (no regenerate-compare for the manifest in v1). Future
  conversion = a new owner decision (naturally post-Phase-14) requiring a non-circular
  handwritten topic-SOURCE design + a dated Phase-8 additive-minor amendment (`topic` kind);
  the GA-F1 quantified census (generation log §GEN-D.2) is that decision's input. WHY: GA-F1 —
  the manifest consumer contract (25 topics/117 match terms · entry · how_to_use · hard_rules ·
  never_modify · chokepoint marking) is absent from the graph; a graph-only generator is
  impossible without new graph content; a side-channel read violates §2.1.1; invention
  violates the no-fabrication law (§16.3 stop honored 2026-07-16, ruling same day).

# Evidence note

All generation evidence lives in `docs/DOCUMENTATION_GENERATION_LOG.md` (created at GEN-0) —
contract = procedure, log = what was generated and proven (framework hierarchy rule). The
regeneration runbook (how any future agent re-runs generation safely) is written into the log
at GEN-F and into every output's banner — never only in memory.
