---
id: documentation-generation-log
type: evidence-log
status: active
owner: append-only
scope: all — Campaign Phase 9 (Documentation Generation) evidence
anchors: docs/campaign_contracts/PHASE_09_DOCUMENTATION_GENERATION.md, docs/knowledge_graph.json, docs/KNOWLEDGE_GRAPH_CERTIFICATION.md
verified: 2026-07-13
---

# DOCUMENTATION GENERATION LOG — Campaign Phase 9 (created GEN-0, append-only)

> Contract = procedure ([PHASE_09_DOCUMENTATION_GENERATION.md](campaign_contracts/PHASE_09_DOCUMENTATION_GENERATION.md));
> this log = what was decided, generated, and proven. Regeneration instructions live HERE
> (§GEN-F, at close) and in every output's banner — never only in memory.

---

## GEN-0 — Charter + gate + ratification — EXECUTED 2026-07-13 · ⏸ 3 classified owner items

**Owner order honored verbatim:** GEN-0 = Design Record and generation charter ONLY. Nothing
generated (0 cards, 0 feature docs, 0 fences, 0 manifest changes); no existing documentation
modified (index log-row per contract §11c only); graph/schema/builder/validator/certification
untouched; Phase-8 residual register unchanged — every residual consumed here is cited to its
Phase-8-certified routing, none silently absorbed.

### 1. Gate (contract §7 GEN-0 row) — PASS

| Check | Result |
|---|---|
| Phase 8 closed | ✓ — [KNOWLEDGE_GRAPH_CERTIFICATION.md](KNOWLEDGE_GRAPH_CERTIFICATION.md) VERDICT "PHASE 8 COMPLETE"; build log §KG-F "Phase 9 CLEARED"; owner approval 2026-07-13 verbatim ("Phase 8 is APPROVED. The Knowledge Graph certification is accepted.") |
| Phases 5–7 closed (transitive) | ✓ — Standard frozen-v1 · Phase 6 CENSUS-COMPLETE · Phase 7 cert |
| KG-F handoff present | ✓ — generator input spec (cert §7) + 25-row manifest-view mapping table (KG build log §KG-E.5) + version-pinning rule + additive-minor register |
| Graph present + valid | ✓ — READ-ONLY re-verification (below): certified hash recompute MATCH, canonical form byte-exact, 1,345 nodes unique+sorted, 635 edges 0-dangling, schema 1.0.1, no timestamps, 528 urls↔528 routes_to, 28 features |
| Evidence log absent pre-session | ✓ — this file created now |
| Battery baseline (entry) | 1530/1530 (untouched; Phase 9 battery = GEN-D only) |

**Dated deviation note (2026-07-13, disclosed — not silent):** the contract's GEN-0 row says
"re-verify graph (validator run + hash)". The full Phase-8 validator was NOT run: its
reproducibility section re-runs the builder IN PLACE, and the corpus has legitimately grown
since the certified build (the certification artifact itself — the disclosed bootstrap
boundary), so a validator run would OVERWRITE the certified graph — exactly Phase-8 residual
**R-10**, whose recorded law is "post-cert verification = read-only recompute only." The
owner's GEN-0 order ("Do not change the graph, schema, builder, validator, or certification
artifacts") makes the read-only equivalent the only lawful reading. Verification performed =
every non-mutating validator check reimplemented read-only (hash law · serialization law ·
uniqueness/sortedness · referential integrity · timestamp scan · selection-basis counts) —
ALL PASS, quoted in the session record. Phase 14's temp-path validator extension (R-10)
restores the literal "validator run" for future phases.

### 2. Owner rulings of record (2026-07-13, verbatim — bind GEN-D2/D5/D6 and all of Phase 9)

> "Keep the current hybrid model. Structural content remains machine-generated. Prose remains
> permanently handwritten or hybrid. Do not expand generation into prose. Keep R7 unchanged."

Recorded as permanent Phase-9 law: generation is and remains **structural-only**; the
KOS_TARGET_VISION long-term direction executes within the hybrid model — no future GEN-D9
extension may target prose (an extension request that would = owner change-control at the
Phase-5 Design Record, not a Phase-9 decision).

### 3. GEN-D1..GEN-D9 ratification (defaults are "binding unless overridden" — contract Appendix A; owner proceed-order 2026-07-13 = the ratification authority; no default overridden)

Per-decision record (alternatives · why the default · rejections · compatibility · roadmap):

**GEN-D1 — Template engine = stdlib-only Python templating, scripts/ location. RATIFIED.**
Alternatives: Jinja2 (not in the frozen venv — verified: a dependency addition = owner-gated
requirements change, U-invariant environment freeze), Django templates (drags app settings
into generation = violates graph-only law §2.1.1). Why: zero new dependencies; deterministic;
same toolchain class as the Phase-8 builder (KG-D9). Compat: Standard §tooling · P8 (sits
beside builder/validator) · P14 (extends, never forks). Roadmap unchanged.

**GEN-D2 — Targets: v1 MANDATORY = URL cards + features layer (docs/features/**) +
manifest-view conversion. RATIFIED.** Owner-ACTIVATED lane (app/model/service/view summaries
+ navigation indexes as hybrid fences) and URL_ATLAS-class supersessions = **NOT activated by
default — ⏸ owner items OI-2/OI-3 below** (activating nothing is the default state; assuming
an activation would violate the owner's classify-don't-assume instruction). Why the mandatory
trio: they are the R4/R8/R5 design-of-record targets, whole-file `generated` class (no fence
complexity), and the KG-F input spec + KG-E mapping table exist for exactly them. Compat:
one-canonical-per-topic preserved (no parallel summary files); PHASE_07 quarantine honored
(manifest only at GEN-D). Roadmap unchanged.

**GEN-D3 — Overwrite policy. RATIFIED as written:** `generated` whole files = total overwrite
(disposable, §2.1.4); hybrid = fence interiors ONLY, outside-fence bytes byte-preserved and
verified per write; hand-edit-in-fence = REFUSE + report (owner decides fold-to-source or
discard — never clobbered); **zero hard deletions** (graph-removed target ⇒ PHASE_07 §6.4
supersession mechanics). Alternatives (merge-on-write, prompt-per-file) rejected:
nondeterministic, unauditable. Compat: DC-D3 no-deletions discipline carried.

**GEN-D4 — Regeneration policy = full-run default. RATIFIED.** Partial/incremental permitted
ONLY with a logged byte-equality proof against a full run, else forbidden. Why: determinism is
provable only against the full tree; the corpus is small enough that full regeneration is
cheap. Rejection: mtime/dirty-flag incremental schemes (hidden state = drift).

**GEN-D5 — Fence policy. RATIFIED as written:** parent-R6 syntax; one fence per section,
never nested; **fences NEVER in `handwritten`-class docs**; first-time carving = one-time
HUMAN-reviewed edit (per-file diff, PHASE_07 batch discipline) — the generator fills fences,
it never carves them. Owner ruling §2 binds: fences carry structural content only, prose
around them is permanently handwritten. (Live only if OI-2 activates any hybrid target.)

**GEN-D6 — Generated metadata. RATIFIED, contingent on OI-1:** whole files = the Standard's
7-field frontmatter with `owner: generated` + `type` per typology (`url-card`,
`feature-doc`, …) + a top banner naming the generator and the regeneration command; fenced
sections = header fields `generator= source=knowledge_graph.json graph=<hash-prefix>
schema=<major.minor> template=<version>`; **NO wall-clock dates in any generated body or
fence** — dates live in this log only. This requires the ⚠️ R6 dated amendment (OI-1): the
parent's R6 default fence header includes `generated=<ISO-date>`, which cannot coexist with
byte-stable regeneration (§2.1.6). Flagged at contract-authoring time; disposition = owner's.

**GEN-D7 — Validation policy. RATIFIED as written:** pre-generation graph verification green
in-session (per the §1 R-10 law: read-only recompute until Phase 14 ships the temp-path
validator) · completeness arithmetic (graph selection count == produced count, counted never
asserted) · determinism double-run (byte-identical tree) · corpus-wide fence-integrity scan ·
output metadata validity · zero-writes-outside-allowlist diff census · version stamps
(graph hash + schema major + template version) present on every output. Stale-output contract
(recorded-hash ≠ current-hash ⇒ STALE) handed to Phase 14 as detect-and-notify — regeneration
is always a human/agent-ordered act, never automatic.

**GEN-D8 — Output locations. RATIFIED as written:** cards + feature docs at
`docs/features/<feature_slug>/…` (R8); summaries (if OI-2 activates any) as fences INSIDE the
existing owning canonicals — no parallel files, no `docs/generated/` ghetto
(one-canonical-per-topic); manifest stays at its CI-guarded path
`docs/LEARNING_2_0/AI_AGENT_GUIDE/canonical_manifest.json` (ownership flips to `generated` at
GEN-D only).

**GEN-D9 — Extensibility. RATIFIED as written:** a new target class requires template +
KG-F-style selection spec + a dated GEN-D2 amendment (owner-gated); Phases 14/18/19 add
targets only via their own contracts citing this rule; generators remain graph-only consumers
FOREVER (a generator needing non-graph data = Phase-8 graph-gap amendment, never a
side-channel read). Owner ruling §2 adds the permanent ceiling: no extension may target prose.

### 4. The eleven owner-ordered definitions (explicit, of record)

1. **Generation boundaries** — input boundary: `knowledge_graph.json` through schema major-1
   pin + versioned templates, NOTHING else (no code reads, no doc reads, no DB). Output
   boundary: §9 allowlist only — `docs/features/**` whole files · fence interiors of
   OI-2-activated canonicals · the manifest at GEN-D · allowlisted integration rows
   (DOCUMENTATION_INDEX/START_HERE routing). Everything else = write-refused.
2. **Ownership boundaries** — `generated`: whole outputs, disposable, hand-edits forbidden
   (fix-at-source → rebuild → regenerate). `hybrid`: handwritten prose owns the file; the
   fence interior alone is generated. `handwritten`: generator may never write, period.
   Truth-locks (T1): inputs only. The graph: never project truth — cards cite, never assert.
3. **Fence policy** — GEN-D5 above (syntax, no nesting, human-reviewed carving,
   handwritten-class prohibition, structural-only interiors).
4. **Regeneration policy** — GEN-D4 above (full-run default; proof-gated partial; the
   maintenance path is fix-source → rebuild graph → regenerate; manual editing of generated
   content is never the fix).
5. **Overwrite policy** — GEN-D3 above (total overwrite for generated files; fence-interior-
   only for hybrid; refuse+report on hand-edit; zero hard deletions).
6. **Handwritten protection rules** — write-fencing (§4 contract): generator writes are
   location-allowlisted BEFORE content is considered; pre/post diff per hybrid write proves
   outside-fence bytes identical; corpus-diff census at GEN-E/GEN-F proves phase-wide
   integrity; prose is permanently out of scope (owner ruling §2); R7 unchanged.
7. **Graph-to-document mapping** — from the KG-F generator input spec: `url` nodes +
   `routes_to`(+`gated_by`/`calls` when those registers ever exist — absent rows OMITTED, not
   faked) → URL cards; `feature` nodes + `belongs_to_feature` → feature docs; kind censuses →
   generated indexes; the 25-row KG-E mapping table → manifest-view. Every card cites its
   governing docs via `documented_by`/`cites` edges — derived knowledge only.
8. **Card template architecture** — one card per url node (R4 grain) at
   `docs/features/<feature_slug>/<url_name>.md`; content per parent §6.1.5: route + view +
   gates + services + models-with-sole-writer + governing docs + mobile note **where the
   graph carries the data**; absent edge kinds render as an honest "not machine-known —
   see <canonical>" line, never invented. Cards for urls with NO feature membership land in
   the reserved `docs/features/_unassigned/` bucket (an explicit, countable gap surface —
   arithmetic in GEN-B will show how many; resolution = FEATURE_INDEX enrichment at source,
   never guessed membership).
9. **Feature document architecture** — one `docs/features/<slug>/README.md` per feature node:
   member cards (via belongs_to_feature), apps touched, governing docs; the 4 edge-less
   features (Phase-8 R-5) render honestly as "no machine-provable members — enrich
   FEATURE_INDEX at source"; plus the features master index (one generated root README).
10. **Manifest-view generation** — GEN-D only, battery-bearing: render the manifest FROM the
    graph per the KG-E mapping table; consumer contract preserved (`entry`/`topics`/
    `never_modify`/`hard_rules` semantics identical — content changes to never_modify/
    hard_rules stay owner-gated); topic-13 directory pointer carried as prose (Phase-8 R-8
    routing consumed as certified); equivalence proof + smoke + full battery per U5.
11. **Additive-minor growth policy** — GEN-D9 above + the Phase-8 additive-minor register
    (12 rows, every KOS_TARGET_VISION concept mapped): graph growth = minor schema bumps at
    the Phase-8 record; generation growth = dated GEN-D2 amendments; consumers pin majors;
    prose forever excluded (owner ruling §2).

### 5. Phase-8 residual intake (cited routings — nothing silently absorbed, register unchanged)

| Phase-8 residual | Certified routing (verbatim class) | GEN-0 disposition |
|---|---|---|
| R-4 ledger_and_payment filename-miss | "explicit mapping candidate at GEN-0" | Consumed as a MAPPING note: the KG-E table row for topic 4 already routes the manifest topic to the page via cites — manifest-view generation needs nothing more. The missing `documented_by` edge is a GRAPH gap = Phase-8 amendment lane if ever needed; NOT absorbed into Phase-9 scope. |
| R-5 four unparsable feature rows | "Phase-9 feature-doc authoring input" | Feature docs render the 4 honestly (definition §9); the FIX is FEATURE_INDEX source enrichment → graph rebuild → regenerate — recorded as a fix-at-source pointer, not Phase-9 work. |
| R-6 298 doc islands | "Phase-9 card/documented_by authoring = the designed resolution" | Cards + feature docs ARE the designed fill; no extra scope. |
| R-8 manifest directory pointer | "GEN-0 Design Record: manifest-view generator carries it as prose/dir-listing" | Adopted into definition §10 verbatim. |
| R-10 validator in-place-repro | "Phase-14 first validator extension" | NOT absorbed — Phase-14's. GEN-0's read-only gate law (§1 deviation note) works around it lawfully. |

Remaining residuals R-1/R-2/R-3/R-7/R-9: not Phase-9-routed; register stands exactly as
certified.

### 6. ⏸ Classified owner items (per the owner's "stop and classify rather than assuming")

| # | Item | Default if unanswered | Recommendation |
|---|---|---|---|
| **OI-1** | **R6 dated amendment disposition** (Phase-5 Design Record): fence header field `generated=<ISO-date>` → replaced by `graph=<hash-prefix> schema=<ver> template=<ver>`. Contract §6.4 flags that the R6 date-field default and byte-stable determinism (§2.1.6, campaign-ratified) CANNOT both hold. | None — contract stop-condition 2 names this disposition as required before GEN-0 fully closes. | **ACCEPT the amendment** (dates → version stamps; generation dates live in this log). Rejecting it = rejecting byte-identical regeneration. On acceptance the dated amendment is written into PHASE_05's Design Record per its own amendment rules (the Standard's body text is NOT touched). |
| **OI-2** | **Owner-activated hybrid targets** (GEN-D2 lane): activate any of app summaries · model summaries · service summaries · view summaries · navigation indexes as KOS:GEN fences inside their owning canonicals? | NONE activated ⇒ GEN-C = documented no-op; v1 ships the mandatory trio only. | Ship v1 with NONE activated (smallest correct slice; fences can be activated later via dated GEN-D2 amendment without rework). |
| **OI-3** | **URL_ATLAS-class supersession**: replace the handwritten URL_ATLAS (≈40 rows vs 528 certified urls) with the generated cards layer, PHASE_07 §6.4 mechanics? | NOT superseded ⇒ URL_ATLAS stays handwritten-interim; cards coexist; supersession possible later via its individual owner gate. | Defer to after GEN-B evidence exists (judge the generated layer against the atlas with both on disk). |

**Sequencing impact:** OI-1 gates any FENCE template (GEN-C class) and formal GEN-0 closure;
it does NOT block GEN-A's mandatory-trio templates (whole files, no fences). OI-2/OI-3 gate
GEN-C only. GEN-A is executable immediately on owner approval of this record.

### 7. Scope discipline

Files touched this sub-phase: this log (NEW) · PHASE_09 Appendix A (Design Record fill) ·
DOCUMENTATION_INDEX (log row, §11c) · status file · memory. **Zero generation. Zero graph/
schema/builder/validator/cert changes. Zero manifest reads-for-write. Zero corpus edits.
Battery not run (baseline 1530/1530 stands).** git HEAD `49404001` · 0 staged · 2 stashes.

### 8. GEN-0 CLOSURE — owner rulings 2026-07-13 (verbatim)

- **OI-1: "ACCEPT. Record the dated amendment exactly as proposed. Replace the wall-clock
  generated-date with deterministic generation metadata (graph hash, schema version, template
  version). Preserve deterministic, byte-identical generation. Do not modify the body of
  DOC_STANDARDS beyond the permitted amendment process."** → R6 dated amendment written into
  PHASE_05 Appendix A "Dated amendments" (the permitted process; Standard body untouched).
- **OI-2: "NONE for v1. Do not activate any optional hybrid fence targets. GEN-C remains a
  documented no-op for v1. Future activation may occur only through a future owner-approved
  Design Record amendment."** → GEN-D2 owner-activated lane = EMPTY; GEN-C = documented no-op.
- **OI-3: "DEFER. Do not supersede URL_ATLAS or similar existing documentation during GEN-0.
  Revisit only after the generated documentation layer exists and both systems can be compared
  on disk."** → URL_ATLAS stays handwritten-interim canonical; comparison after GEN-B.

**GEN-0 CLOSED 2026-07-13.** All GEN-D1..D9 answered; R6 disposition recorded; stop-condition
2 cleared. GEN-A authorized by the same owner order.

## GEN-A — Templates + render pipeline — DONE 2026-07-13

**Scope held:** templates + pipeline + SCRATCHPAD samples only. Zero corpus writes
(`docs/features/` does not exist at close); graph/schema/builder/validator/cert untouched
(hash `85b7fd6d…` intact); no Phase 5–8 artifact modified beyond the contract-permitted
Design-Record fills; structural content only, prose untouched (owner rulings §GEN-0.2/.8).

### 1. Instruments created (§9 "templates/generators beside the Phase-8 tooling")

| File | Role |
|---|---|
| `scripts/generate_docs.py` | Shared pipeline + one thin renderer per class (GEN-D1). Read-only graph verification per the R-10 law (hash recompute + schema major-1 pin; REFUSES mismatch) · selections sorted by node id · LF + trailing newline · `--out` REQUIRED with no default corpus path (accidental corpus write structurally impossible) · `--sample` = GEN-A mode |
| `scripts/doc_templates/url_card.md.tpl` | url-card v1.0.0 (stdlib `string.Template`) |
| `scripts/doc_templates/feature_readme.md.tpl` | feature-doc v1.0.0 (also renders the `_unassigned` bucket index) |
| `scripts/doc_templates/features_index.md.tpl` | features-index v1.0.0 |

Template files carry a first-line provenance comment that the pipeline STRIPS from output
(frontmatter must be line 1 of every rendered file — frontmatter-parser law).

### 2. Derived conventions (inside ratified GEN-D6; recorded, not silent)

- **`verified:` field in generated frontmatter = `graph:<hash12>`, never a date** — the OI-1
  principle (A3 amendment) applied to frontmatter: a date field breaks byte-stable
  regeneration exactly as it does in fence headers; "verified against graph X" is the
  meaningful statement for a generated file. Dates live in this log.
- **Filename collision rule (deterministic, order-independent):** when >1 url maps to the
  same (directory, `<url_name>.md`), EVERY collider renders as `<namespace>__<url_name>.md`.
  Census: exactly 3 collision groups, all in `_unassigned/` (`home` ×2 · `logout` ×2 ·
  `dashboard` ×4).
- **App section = labeled render derivation, not a graph edge:** view-module first segment
  exact-token-matched against app labels; no match (vendor/config views, 298 urls) renders
  "not derivable" honestly. The card SAYS it is a render rule.
- **Honest-absence lines** for gates (R-2), services (R-1), models-at-route-grain, mobile:
  each names the reason and the Phase-8 residual — never an invented fact.
- **`_unassigned/README.md` generated index** — required by §3.6 (every output
  index-reachable): a bare directory link would orphan 515 cards.

### 3. Sample verification (one per class, hand-verified against graph slice + Standard)

Samples (scratchpad `gen_a/run5`): `login/login.md` (url-card, deterministic pick = first
feature-assigned url) · `login/README.md` (feature-doc) · `README.md` (features-index).
Field-by-field check vs the graph nodes `url:accounts:login` / `view:accounts.views.LoginView`
/ `feature:login`: route, namespace, mount, view, module, anchors, feature label, seed source,
member model `accounts.User` (single_writer null → "not machine-known") — all exact.

**Three template defects caught BY this review and fixed within GEN-A** (the sub-phase's
purpose): (1) empty url-pattern rendered inside backticks as if a literal pattern → plain
italic placeholder; (2) doc-link labels used basenames (`README.md` ×N ambiguous) → full
paths; (3) template provenance comment preceded frontmatter → pipeline strip rule; plus a
link-depth error in feature-README app links (`../` where `../../` is correct from
`docs/features/<slug>/`) → fixed, re-verified (`../../../config/…` and `../../apps/…` both
resolve). Final samples re-rendered and re-checked after every fix.

### 4. Selection arithmetic (graph queries — the GEN-B expected-counts contract)

| Selection | Count |
|---|---|
| url nodes → cards | **528** (1:1; 13 in feature dirs + 515 in `_unassigned/`) |
| feature nodes → feature READMEs | **28** |
| `_unassigned` bucket index | 1 |
| features master index | 1 |
| **GEN-B expected total** | **558 files** |
| urls with machine-provable feature membership | 13 (via 13 url-side `belongs_to_feature` edges; model-side 26 = the other 39-edge half) |
| filename collisions resolved | 3 groups (deterministic namespace-prefix rule) |

### 5. Determinism proof

Double sample-render to two fresh scratchpad trees → `diff -r` EMPTY (byte-identical);
tree sha256 logged (card `ae4d192a…` · feature `d2af7c52…` · index `aee6b49f…`). Stamps:
graph `85b7fd6d5204` · schema 1.0.1 · template v1.0.0 on every output.

### 6. Validation summary (samples vs the Standard) — ALL PASS (38/38 checks)

Per file: frontmatter line-1 ✓ · 7-field core exact ✓ · `owner: generated` ✓ · type in
typology (`url-card`/`feature-doc`) ✓ · verified = graph-hash-not-date ✓ · banner +
regeneration command ✓ · version stamps ✓ · zero wall-clock dates ✓ · LF + trailing
newline ✓ · zero unsubstituted placeholders ✓. Card carries all eight §6.1.5 sections ✓.

### 7. Classified findings

| # | Finding | Class | Route |
|---|---|---|---|
| GA-F1 | **Manifest-view is NOT graph-derivable v1** — the manifest's `topics[].match` term lists, `entry`, `how_to_use`, `hard_rules`, `never_modify` prose, and the chokepoint-service marking exist ONLY in the manifest body; the graph carries none of them (cites edges = canonical→also links only; the KG-E mapping table records match[0] + counts, not full term lists). A graph-only generator for the GEN-D conversion is impossible without new graph content. Per §2.1.1: "a generator needing data the graph lacks = a graph gap → dated Phase-8 amendment, never a side-channel read." | contract-anticipated graph gap (GEN-A stop-condition class — but its sub-phase is GEN-D, so classified now, blocking nothing before it) | ⏸ OWNER at/before GEN-D: **(a)** dated Phase-8 amendment adding topic content to the graph (e.g. minor-version `topic` node kind carrying match terms + rule/entry attributes; builder change, owner-gated), or **(b)** dated PHASE_09 amendment re-scoping GEN-D (manifest stays handwritten/CI-guarded; conversion deferred to a later owner decision). GEN-B/GEN-C unaffected either way. |
| GA-F2 | Feature-membership sparsity: 13/528 urls machine-provable (FEATURE_INDEX rows carry few exact url tokens) — the features tree v1 is honest but thin; `_unassigned` holds 515 cards | coverage statement, not a defect | fix-at-source lane (enrich FEATURE_INDEX → rebuild → regenerate); already the designed gap surface (GEN-0 def 8) |

### 8. Scope discipline

Files created: the 4 instruments (§1). Files changed: this log · PHASE_09 Appendix A (GEN-0
closure, owner rulings) · PHASE_05 Appendix A (dated amendment A3, owner-ordered) · status ·
memory. Battery not run (GEN-D only; 1530/1530 stands). git HEAD `49404001` · 0 staged ·
2 stashes.

**GEN-B READY:** templates verified · pipeline refuses bad graphs · expected counts fixed
(558) · output locations ratified (GEN-D8) · corpus-write mode requires only
`--out docs/features` + the §11c routing rows. GA-F1 does not gate GEN-B.

_Section closed 2026-07-13. Next: GEN-B (owner-gated)._

## GEN-B — URL cards + features layer — DONE 2026-07-16

**Scope held:** the first corpus write of the phase — `docs/features/**` (whole `generated`-class
files) + the two §9-allowlisted integration rows (DOCUMENTATION_INDEX, START_HERE) + this log +
status + memory. Zero other writes (census §6). Graph/schema/builder/validator/cert untouched;
manifest untouched (quarantine holds — GEN-D only); zero fences created (whole files only;
GEN-C = documented no-op per OI-2); zero hard deletions; battery not run (GEN-D only;
1530/1530 stands).

### 1. Gate (pre-generation, per GEN-D7 + the R-10 read-only law)

| Check | Result |
|---|---|
| git state | HEAD `49404001` · 0 staged · 2 stashes ✓ (unchanged at close) |
| `docs/features/` absent pre-session | ✓ (`ls: cannot access` quoted in session) |
| Graph hash recompute | MATCH `sha256:85b7fd6d5204…` ✓ |
| Canonical serialization | byte-exact ✓ · schema 1.0.1 (≤ major-1 pin) ✓ |
| Node uniqueness/sortedness | 1,345 unique ✓ sorted ✓ |
| Edge integrity | 635 edges · 0 dangling ✓ · sorted by `(from,kind,to)` ✓ |
| Timestamp scan | 0 ISO timestamps in the serialized graph ✓ |
| Selection basis | url 528 · routes_to 528 · feature 28 · url-side belongs_to_feature 13 ✓ (= GEN-A arithmetic) |

Probe note (instrument, not artifact): the first sortedness probe used the wrong edge sort key
`(kind,from,to)` and read False; the certified key is `(from,kind,to)` (True). Hash recompute +
byte-exact canonical form already proved the graph identical to the certified artifact.

### 2. Determinism proof (GEN-D4 — full double-run BEFORE any corpus write)

Two full renders to fresh scratchpad trees → `diff -r` EMPTY (byte-identical), 558 files each;
tree sha256 `f429aab0a70b…` (sorted per-file sha256 list, hashed). Stamps on every file:
graph `85b7fd6d5204` · schema 1.0.1 · template v1.0.0.

### 3. Corpus write + byte-proof

`env/bin/python scripts/generate_docs.py --out docs/features` → 558 files, 29 directories
(28 feature dirs + `_unassigned/`). `diff -r <proven-scratchpad-tree> docs/features` EMPTY —
the corpus tree IS the determinism-proven tree, byte-identical.

### 4. Selection arithmetic (counted, not asserted — matches the GEN-A contract exactly)

| Selection | Expected (GEN-A §4) | Produced | Match |
|---|---|---|---|
| url nodes → cards | 528 | 528 | ✓ |
| — in feature dirs | 13 | 13 | ✓ |
| — in `_unassigned/` | 515 | 515 | ✓ |
| feature READMEs | 28 | 28 | ✓ |
| `_unassigned/README.md` index | 1 | 1 | ✓ |
| features master index | 1 | 1 | ✓ |
| **Total** | **558** | **558** | ✓ |
| filename-collision renames | 3 groups / 8 files | 3 groups / 8 files (`home` ×2 · `logout` ×2 · `dashboard` ×4, all `_unassigned/`) | ✓ |

### 5. Validation suite (corpus-wide, scripted, main-thread)

- **Metadata (558/558):** frontmatter line 1 ✓ · 7-field core ✓ · `owner: generated` ✓ ·
  `type` in typology (`url-card`/`feature-doc`/`features-index`) ✓ · `verified: graph:85b7fd6d5204`
  (never a date) ✓ · banner + regeneration command ✓ · graph/schema/template stamps ✓ ·
  LF + trailing newline, zero CRLF ✓ · zero unsubstituted `$` placeholders ✓.
- **Orphan check (§3.6): 0 orphans** — every card linked from its directory README (feature
  README or `_unassigned/README.md`); every directory README linked from the master index.
- **Link resolution: 1,056/1,056 relative links resolve** (every `](…)` target in the tree
  exists on disk — card→README, README→cards, app-doc links `../../apps/…` + `../../../config/…`).
- **Fence scan: zero fences** in the generated tree (whole files only, as ratified) and zero
  generator writes into any hybrid/handwritten doc.
- **Sample hand-verification (per §5 evidence standard):** `login/login.md` re-verified
  field-by-field against graph nodes `url:accounts:login` / `view:accounts.views.LoginView` /
  `feature:login` — route/namespace/mount/empty-pattern/named/view/module/anchor/vendor/feature/
  seed all exact; honest-absence lines name residuals R-1 (services) and R-2 (gates); all eight
  parent-§6.1.5 card sections present.

### 6. Integration rows (§11c) + write census

- **DOCUMENTATION_INDEX.md**: one `features/README.md` row added beside the knowledge-graph
  rows — marked ⚙️ `generated`, "an INDEX … not truth" wording per PHASE_08 §11, with counts,
  version stamps, and the regeneration command.
- **START_HERE.md**: one additive routing paragraph (route-level structural lookup →
  `features/README.md`, marked generated/index-not-truth). No existing prose modified.
- **Doc-guard smoke after the two edits: 11/11 OK** (`core.tests.{PkalsNavigationGuardTests,
  DocAccuracyTests}` — the DOCCLEAN-B precedent class: stdlib no-DB smoke, **NOT a battery run**).
- **Diff census (git-status delta vs pre-session capture):** sole delta = the new untracked
  `docs/features/` tree. DOCUMENTATION_INDEX/START_HERE were already modified-uncommitted
  pre-session (campaign-wide state), so their edits don't move the status line; both edits are
  the two quoted rows above, nothing else. Log/status/memory = this close's own writes.
  0 staged · 2 stashes · HEAD unchanged.

### 7. Classified findings

| # | Finding | Class | Route |
|---|---|---|---|
| GB-F1 | Four generated files carry the string `2026-07-05` — **verbatim graph content**, not generation-time stamps: 3 feature-node LABELS from FEATURE_INDEX rows ("stage-trio spec 2026-07-05", "R10-A, 2026-07-05", "OP-1, 2026-07-05") rendered into their READMEs + the master index. GEN-D6's no-wall-clock-dates law targets *generation* dates (byte-stability); graph-carried label text is deterministic and reproduces byte-identically (proven §2). | conformant-by-construction; recorded so no future validator misreads it | None. If the owner ever wants date-free labels: fix at source (FEATURE_INDEX row text) → rebuild → regenerate. |
| GB-F2 | Validation-probe imprecision (instrument, disclosed): a `__`-in-basename census matched 54 files, of which 46 are `_unnamed__*` **id-derived stems for unnamed routes** (KG-B `url:_unnamed:<slug>` law), not collision renames. True collision renames = 8 files = exactly the GEN-A census. | instrument note | none |

GA-F1 (manifest-view graph gap) and GA-F2 (membership sparsity 13/528) stand unchanged —
GEN-B is exactly the honest surface GA-F2 predicted (`_unassigned/` = 515 countable cards).

### 8. Scope discipline

Files created: `docs/features/**` (558, all `generated`-class). Files changed:
DOCUMENTATION_INDEX.md (+1 row) · START_HERE.md (+1 paragraph) · this log · status file ·
memory. Battery not run; no pins; git HEAD `49404001` · 0 staged · 2 stashes.

**GEN-C READY:** per OI-2 (owner ruling, §GEN-0.8) GEN-C = **documented no-op** — its session
records the no-op + the activation path (future owner-approved Design Record amendment), then
GEN-D (manifest-view, battery-bearing) which FIRST needs the GA-F1 owner disposition
(graph amendment vs GEN-D re-scope). OI-3 (URL_ATLAS comparison) is now judgeable: both layers
exist on disk.

_Section closed 2026-07-16. Next: GEN-C (owner-gated)._



## GEN-C — Hybrid fenced sections — DOCUMENTED NO-OP, CLOSED 2026-07-16

**Owner authority:** OI-2 ruling of record (§GEN-0.8, verbatim: "NONE for v1. Do not activate
any optional hybrid fence targets. GEN-C remains a documented no-op for v1.") + owner
re-confirmation 2026-07-16 ("GEN-C is the documented no-op exactly as previously ratified …
Do not activate any hybrid targets. Do not introduce fence-based generation."). The same
2026-07-16 owner order authorized continuing to GEN-D in this session (a dated, owner-granted
exception to the one-sub-phase-per-session default — recorded, not assumed).

**What GEN-C is on the record:**
- Owner-activated GEN-D2 lane = EMPTY. Zero fences carved, zero fence templates authored,
  zero hybrid docs touched, zero URL_ATLAS-class supersessions (OI-3 DEFER stands).
- **Activation path (for any future v-next):** owner-approved dated GEN-D2 amendment naming the
  target canonical(s) → fence template authored + version-stamped → one-time HUMAN-reviewed
  fence carving (per-file diff, PHASE_07 batch discipline) → generator fills interiors only.
  Nothing about v1 has to be reworked to activate later (GEN-A §GEN-0.6 recommendation held).

**No-op verification (evidence, not assertion):**
| Check | Result |
|---|---|
| GEN-B tree untouched | tree sha256 recompute `f429aab0…` == GEN-B close value ✓ |
| Live `KOS:GEN` fences corpus-wide | **0** — every `begin/end` marker string in the active tree is spec text (DOC_STANDARDS §16 example block · PHASE_05 R6 row + A3 amendment quote), none a live fence; remaining hits are prose mentions in contracts/logs/index rows ✓ |
| Graph/schema/builder/validator/cert | untouched (graph hash re-verified MATCH at the GEN-D gate below) ✓ |
| Manifest | untouched (quarantine holds) ✓ |
| git | HEAD `49404001` · 0 staged · 2 stashes ✓ |

Battery not run (no-op; 1530/1530 stands). Files changed this sub-phase: this log · status ·
memory only.

_Section closed 2026-07-16. GEN-D opened same session per owner order._

## GEN-D — Manifest-view conversion (battery-bearing) — ⏸ STOPPED 2026-07-16 AT GA-F1 (owner decision point; contract §16.3)

**Owner order honored:** "Do not solve GA-F1 by assumption. If GA-F1 requires an owner
decision, stop exactly at that point, classify it, present the available options with their
trade-offs, and wait for my ruling." GA-F1 requires exactly that decision — GEN-D stopped at
its gate, BEFORE any manifest read-for-write, any generation, or any battery-relevant action.
**Manifest untouched · battery NOT run · zero corpus writes this sub-phase** (log/status/memory
only).

### 1. Gate portion executed (read-only)

Graph re-verified per the R-10 law: hash recompute MATCH `sha256:85b7fd6d5204…`, schema 1.0.1
(≤ major-1 pin). GEN-B outputs intact (tree sha256 `f429aab0…`). git HEAD `49404001` ·
0 staged · 2 stashes.

### 2. GA-F1 quantified (read-only census of `canonical_manifest.json` v2026-07-13 vs the certified graph — evidence for the ruling, NOT a generation input read)

| Manifest consumer-contract field | Content | In the graph? |
|---|---|---|
| `topics[].match` term lists | 25 topics · **117 match terms total** | ❌ absent — graph carries 25 `cites` edges (canonical→also doc links) + the KG-E mapping table records `match[0]` + counts only; 117-term lists unreconstructible |
| `topics[].canonical` / `also[]` role semantics | 25 canonical + also[] routings | ⚠️ partial — doc nodes + 25 cites edges exist, but canonical-vs-also role and per-topic grouping are manifest-only |
| `entry` | 5-key routing dict | ❌ absent |
| `how_to_use` | 206-char prose | ❌ absent (prose — owner ruling §GEN-0.2 forbids generating it anyway) |
| `hard_rules` | 4 rules | ❌ absent (owner-gated content, PHASE_07 §6.6c) |
| `never_modify` | 5 entries | ⚠️ partial — the 9 `writes` edges were SOURCED from never_modify/ADR-0002, but the rule text/semantics are manifest-only |
| `chokepoint_services` | 7 services | ❌ marking absent — service nodes exist, chokepoint flag does not |
| `version` | wall-clock date "2026-07-13" | n/a — would become a graph-hash stamp under conversion (OI-1/A3 principle) |

**Verdict (= GEN-A GA-F1, now counted):** a graph-only GEN-D generator is impossible without
new graph content. §2.1.1 law: "a generator needing data the graph lacks = a graph gap → dated
Phase-8 amendment, never a side-channel read." Proceeding by reading the manifest as generation
input would be the forbidden side-channel; proceeding by inventing content would fabricate.
STOP per contract §16.3.

### 3. ⏸ The owner decision — two classified options (as routed at GEN-A §7; neither assumed)

**Option (a) — dated Phase-8 amendment: the graph grows topic content.**
Additive-minor lane (KG-D6; the certified additive-minor register exists for exactly this):
new `topic` node kind (25 nodes) carrying match terms + canonical/also role + entry/hard_rules/
never_modify/chokepoint attributes; schema 1.0.1 → 1.1.0; builder + validator extended; graph
rebuilt (new hash) → GEN-D then runs as a true graph-only conversion.
- **For:** manifest becomes a real generated view (the R5 design-of-record target shipped in
  v1); Phase-14 gets regenerate-compare drift detection for the manifest; graph-only law holds
  with zero exceptions.
- **Against / costs:** reopens certified Phase-8 tooling (builder+schema+validator churn —
  lawful via the additive-minor lane, but churn on a certified artifact); graph rebuild ⇒ new
  content hash ⇒ **all 558 GEN-B outputs go STALE and must be regenerated** (cheap and proven,
  but a whole-layer churn); **unresolved design question that needs its own pass:** the
  SOURCE-of-truth for topic content — the builder must read the 117 match terms from somewhere
  handwritten. Today that somewhere IS the manifest, giving manifest → graph → generated-
  manifest circularity; a clean design needs a handwritten topics register (FEATURE_INDEX-
  style) as source, which is new-doc scope no current contract carries.
- **Blast radius:** Phase-8 amendment + builder/validator code + schema + rebuild + GEN-B
  regeneration + then GEN-D battery session.

**Option (b) — dated PHASE_09 amendment: GEN-D re-scoped.**
Manifest stays handwritten + CI-guarded (PkalsNavigationGuardTests unchanged); ownership does
NOT flip; the conversion is deferred to a later owner decision (naturally post-Phase-14, when
the sync tooling and a topic-source design can be judged together). GEN-D closes as a
documented re-scope; **Phase 9 then has NO battery-bearing sub-phase** (the U5 battery
expectation moves to wherever the conversion eventually lands).
- **For:** zero risk to certified Phase-8 artifacts; campaign momentum (GEN-E validation +
  GEN-F certification can proceed immediately); consistent with the owner's v1-minimalism
  pattern (OI-2 NONE · OI-3 DEFER); the §3.5 success criterion is already conditional ("if
  GEN-D2 confirms it"); avoids designing the topic-source model under sub-phase pressure.
- **Against:** the R5 target ships unconverted in v1 (manifest maintenance stays manual);
  Phase-14's manifest drift domain keeps only its existing CI guard (no regenerate-compare).
- **Blast radius:** one dated amendment row in PHASE_09 Appendix A + log/status records.

**Recommendation: (b) for v1.** Matches every prior v1 ruling (smallest correct slice); (a)
remains fully available later via the certified additive-minor register once a non-circular
topic SOURCE is designed — that design deserves its own owner-reviewed pass, not a GEN-D
side-quest.

**Awaiting owner ruling. GEN-D resumes (or closes by amendment) on that ruling; GEN-E is not
started.**

_Section paused 2026-07-16 — resolved same day below._

### 4. CLOSURE — owner ruling 2026-07-16 (verbatim): **Option (b)**

> "I choose **Option (b)**. … Approve the dated Phase 9 amendment to re-scope GEN-D exactly as
> proposed. For v1: The manifest remains handwritten. The manifest remains CI-guarded. Do NOT
> convert the manifest into a generated artifact. Do NOT add a new Topic node kind. Do NOT
> reopen Phase 8. Do NOT modify the certified Knowledge Graph. Do NOT modify the schema. Do
> NOT modify the builder. Do NOT modify the validator. Do NOT regenerate the existing graph.
> Do NOT invalidate the Phase 8 certification. Record this as the permanent v1 architectural
> decision. The graph remains the only machine-readable knowledge source for generated
> documentation, except for the handwritten manifest, which intentionally remains outside
> graph generation for v1."

→ **Dated amendment A1 recorded in PHASE_09 Appendix A** (the §16.3-mandated venue: "dated
amendment to the owning contract"). **GEN-D CLOSED BY AMENDMENT** — zero manifest changes,
zero Phase-8 changes, battery never ran; per A1, **Phase 9 now has no battery-bearing
sub-phase** (baseline 1530/1530 stands untouched phase-wide). GA-F1 = RESOLVED (this ruling).
The same owner order authorizes GEN-E + GEN-F continuation in this session (second dated,
owner-granted exception to the one-sub-phase-per-session default — recorded, not assumed).

**GEN-D CLOSED 2026-07-16.** _Next: GEN-E (same owner order)._

## GEN-E — Validation suite + integration audit — DONE 2026-07-16

**Authority:** owner order 2026-07-16 ("Execute: GEN-E, GEN-F") — same-session continuation
recorded at §GEN-D.4. **Scope held:** read-only suite + one §9-allowlisted row
(OWNERSHIP_MATRIX, §11d — the generated-family row GEN-B had not yet added) + log/status/
memory. Zero corpus mutations to `docs/features/**` (tree hash unchanged at close); manifest/
graph/Phase-5–8 artifacts untouched; battery not run (Phase 9 has no battery-bearing
sub-phase per A1; 1530/1530 stands).

### 1. Full §6.6 suite (raw results, all in-session)

| # | Check | Result |
|---|---|---|
| E1 | Determinism double-run (two fresh full renders) | `diff -r` EMPTY — byte-identical, 558 files each · **PASS** |
| E2 | Regeneration vs corpus (unchanged graph ⇒ zero diffs — the §3.3 no-op-regeneration proof; the literal "no-op graph REBUILD" variant deliberately not run: builder rebuilds IN PLACE = R-10 hazard + owner do-not-regenerate order; dated deviation, the read-only equivalent shown) | `diff -r <fresh render> docs/features` EMPTY · **PASS** |
| E3 | Hand-edit detection mechanism (deliberately mutated scratch copy) | 1-byte mutation in scratch `login/login.md` → regenerate-compare caught EXACTLY that file, that line · **PASS** |
| E4 | Stale-output mechanics (§6.6 Phase-14 contract) | corpus scan: 558/558 stamps == current graph `85b7fd6d5204` (0 stale) · scratch copy with doctored stamp → detector flags EXACTLY 1 · **PASS** |
| E5 | Metadata validity corpus-wide | 558/558: frontmatter line-1 · 7-field · `owner: generated` · graph-stamp verified-field · banner+regen command · stamps (graph/schema/template) · LF/trailing-newline/no-CRLF · zero unsubstituted placeholders (GB-F1's 4 graph-content dates excluded as classified) · **PASS** |
| E6 | Orphan check (§3.6) | 0 orphans — every card ← its directory README ← master index · **PASS** |
| E7 | Link resolution | 1,056/1,056 relative links resolve on disk · **PASS** |
| E8 | Fence integrity corpus-wide | live `KOS:GEN begin/end` markers: only DOC_STANDARDS §16 spec example (2) + PHASE_05 R6/A3 spec-quote lines (3) — zero live fences, zero fences in `handwritten` docs, zero in generated tree · **PASS** |
| E9 | Integration reachability | `features/README.md` routed from DOCUMENTATION_INDEX (1 row) + START_HERE (1 paragraph) · **PASS** |
| E10 | Doc-guard smoke (post-OWNERSHIP_MATRIX edit; DOCCLEAN-B precedent, NOT a battery) | `core.tests.{PkalsNavigationGuardTests,DocAccuracyTests}` **11/11 OK** |
| E11 | Zero-writes-outside-allowlist census | git-status delta vs pre-GEN-E capture = ZERO new lines (all session writes inside already-dirty/untracked campaign paths); GEN-B tree sha256 `f429aab0…` unchanged; 0 staged · 2 stashes · HEAD `49404001` · **PASS** |

### 2. Integration audit

- OWNERSHIP_MATRIX: `docs/features/**` generated-family row ADDED (owner concept =
  graph+templates; trigger = graph rebuild/template bump ⇒ regenerate whole tree; never
  hand-edit). This closes the §11d obligation GEN-B had left open — disclosed, not silent.
- §11c generated-artifact index rows at GEN-E: N/A — GEN-E created no new artifacts.
- U6 app-doc lookups: N/A phase-wide — zero code changes (stated once, §11e).

### 3. Findings

No new classified findings. Standing: GB-F1 (graph-content dates, conformant) · GB-F2
(instrument note) · GA-F2 (sparsity, fix-at-source). GA-F1 = RESOLVED (A1).

_Section closed 2026-07-16. Next: GEN-F (same owner order)._

## GEN-F — Certification + handoff — DONE 2026-07-16 · 🏁 PHASE 9 VERDICT

### 1. Completeness (counted, never asserted)

| Target class (GEN-D2 as amended by A1) | Expected | Produced | State |
|---|---|---|---|
| URL cards (R4 grain, 1:1 url nodes) | 528 | 528 (13 feature-dirs + 515 `_unassigned/`) | ✅ |
| Feature READMEs | 28 | 28 | ✅ |
| `_unassigned/` bucket index | 1 | 1 | ✅ |
| Features master index | 1 | 1 | ✅ |
| **Generated corpus total** | **558** | **558** | ✅ |
| Hybrid fenced sections | 0 (OI-2: lane EMPTY) | 0 | ✅ no-op, documented (§GEN-C) |
| Manifest-view conversion | NOT executed for v1 (**A1**) | — | ✅ deferred by dated amendment |

### 2. Determinism + fence + stale summary

Proven at every stage: GEN-A sample double-render byte-identical → GEN-B full double-run
BEFORE first corpus write (tree sha256 `f429aab0…`) + corpus byte-proof → GEN-E fresh
double-run + regeneration==corpus. Stamps on all 558 outputs: graph `85b7fd6d5204` · schema
1.0.1 · template v1.0.0; zero wall-clock dates (GB-F1 classified as graph content). Fences:
zero generated, zero live corpus-wide. Hand-edit + stale detection mechanics PROVEN on scratch
copies (E3/E4).

### 3. Corpus-diff census — the complete Phase-9 file ledger (§3.8)

**Created:** `docs/features/**` (558 generated files, GEN-B) · `scripts/generate_docs.py` +
`scripts/doc_templates/*.tpl` ×3 (GEN-A) · this log (GEN-0). **Changed (all §9-allowlisted):**
PHASE_09 contract (Appendix A Design-Record fills GEN-0 + dated amendment A1 GEN-D) ·
PHASE_05 Appendix A (dated amendment A3, GEN-0, owner-ordered) · DOCUMENTATION_INDEX (log row
GEN-0 + features row GEN-B) · START_HERE (routing paragraph GEN-B) · OWNERSHIP_MATRIX
(generated-family row GEN-E) · status file + memory (every close). **Zero:** app code ·
tests · migrations · manifest · graph/schema/builder/validator/cert · hand-edits to generated
content · hard deletions · fences in handwritten docs. Every changed file accounts to a target
class or an allowlisted integration row — §16.6 never triggered.

### 4. Residual register (final, Phase-9)

| Residual | State | Venue |
|---|---|---|
| GA-F1 manifest-view graph gap | **RESOLVED** — owner Option (b), dated amendment A1 | closed |
| Manifest-view conversion itself | **DEFERRED by A1** (permanent v1 decision: manifest handwritten+CI-guarded, outside graph generation) | future owner decision, naturally post-Phase-14; needs non-circular topic-SOURCE design + Phase-8 additive-minor (`topic` kind); GA-F1 census (§GEN-D.2) = input |
| GA-F2 membership sparsity 13/528 | OPEN (honest surface: 515 cards in `_unassigned/`) | fix-at-source: enrich FEATURE_INDEX → rebuild → regenerate |
| GB-F1 graph-content dates ×4 | recorded, conformant-by-construction | fix-at-source iff owner wants date-free labels |
| GB-F2 probe imprecision | instrument note | none |
| OI-3 URL_ATLAS supersession | DEFER stands (owner); both layers now on disk, comparison possible on order | owner, any time |
| Hybrid fence lane | EMPTY by OI-2 | future owner-approved Design Record amendment (path recorded §GEN-C) |
| DC-D1 missing-prose venues | untouched (prose never generated — owner permanent law) | their DC-D1 venues |
| Phase-8 register R-1..R-10 | UNCHANGED | as certified |

### 5. Phase-14/18/19 handoffs (§6.7, written concretely)

- **Phase 14 (knowledge_sync):** stale-output detection = compare each generated file's
  `verified: graph:<hash12>` (and banner stamp) against current `meta.content_hash[7:19]`;
  mismatch ⇒ STALE, REPORT-only (regeneration is always human/agent-ordered — print
  `env/bin/python scripts/generate_docs.py --out docs/features`, never run it). Hand-edit
  detection = regenerate to scratch + `diff -r` (proven E3). Fence domain v1 = trivially
  clean (zero live fences; scanner semantics per E8). Manifest domain = existing CI guard
  ONLY (A1 — no regenerate-compare in v1). R-10 temp-path validator extension obligation
  stands unchanged.
- **Phase 18 (future feature docs):** new feature/route ⇒ update SOURCE (FEATURE_INDEX,
  urls.py, registers) → rebuild graph (Phase-8 builder) → FULL regenerate → new cards appear;
  one-card-per-URL invariant; `_unassigned/` = the countable membership backlog. New target
  classes only via GEN-D9 (template + selection spec + dated GEN-D2 amendment). Prose ceiling
  permanent (owner ruling §GEN-0.2).
- **Phase 19 (deployment docs):** runbook stays `handwritten`; may adopt fenced structural
  tables later ONLY via GEN-D9 + an OI-2-class activation amendment; never whole-file
  generation.

### 6. Regeneration runbook (the permanent instructions — here + every output banner)

```
env/bin/python scripts/generate_docs.py --out docs/features
```
- Pipeline self-verifies the graph read-only (hash recompute + schema major-1 pin) and
  REFUSES a mismatched/newer-major graph — a stale or hand-edited graph cannot generate.
- Full-run is the ONLY default mode (GEN-D4); total overwrite is safe — every file under
  `docs/features/` is disposable (GEN-D3). Rollback = regenerate (or delete + regenerate).
- Run after: any graph rebuild, or any template change (bump `TEMPLATE_VERSION` in
  `scripts/generate_docs.py` in the same change).
- Verify after: file count matches the selection arithmetic printed by the run · double-run
  `diff -r` empty · stamps carry the new graph hash.
- NEVER hand-edit an output: fix the source → rebuild the graph → regenerate.

### 7. Success criteria (§3) — final walk

1 ✅ (every ratified target at its GEN-D8 location, valid; A1 re-scopes the trio's third
member) · 2 ✅ (arithmetic §1, counted) · 3 ✅ (determinism §2) · 4 ✅ (fence integrity E8 +
hand-edit proof E3) · 5 ✅-BY-CONDITION (its own "if GEN-D2 confirms it" clause — NOT
confirmed for v1, A1) · 6 ✅ (routing rows live; 0 orphans; URL_ATLAS handoff executed per
its ruling = OI-3 DEFER/coexist) · 7 ✅ (stamps on 558/558; stale contract §5 written) ·
8 ✅ (census §3, zero unexplained) · 9 ✅ (status+memory every close; battery untouched
phase-wide per A1 — baseline 1530/1530 stands).

### 8. 🏁 PHASE 9 VERDICT

**GENERATION-COMPLETE-WITH-DOCUMENTED-DEFERRALS.** The generated documentation layer exists,
is deterministic, evidence-validated, index-reachable, and regenerable from the certified
graph alone; the handwritten corpus is untouched outside allowlisted rows; the manifest
remains handwritten+CI-guarded by permanent v1 owner decision (A1); the hybrid-fence lane is
empty by owner ruling (OI-2); URL_ATLAS coexists pending OI-3. **PHASE 9 CLOSED.
Phase 10 (UI Component Library) gate = this closure + UI-D1..D9 at UIL-0 — CLEARED to begin
on owner order.** Post-Phase-9 snapshot refresh is DUE (Phase-0 D4 cadence — owner action).

_Log closed for Phase 9, 2026-07-16. Future entries = dated amendments only._
