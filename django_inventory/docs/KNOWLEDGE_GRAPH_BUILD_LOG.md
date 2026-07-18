---
id: knowledge-graph-build-log
type: evidence-cert
status: active
owner: append-only
scope: all — Phase-8 Knowledge Graph build evidence
anchors: docs/campaign_contracts/PHASE_08_KNOWLEDGE_GRAPH.md, docs/DOCUMENT_CLEANUP_CERTIFICATION.md
verified: 2026-07-13
---

# KNOWLEDGE GRAPH BUILD LOG — Phase 8 evidence document

> **The single evidence doc for Phase 8.** Created at KG-0 per
> [campaign_contracts/PHASE_08_KNOWLEDGE_GRAPH.md](campaign_contracts/PHASE_08_KNOWLEDGE_GRAPH.md).
> Authoritative inputs (owner-designated): [DOCUMENT_CLEANUP_CERTIFICATION.md](DOCUMENT_CLEANUP_CERTIFICATION.md)
> **§5 = the official KG readiness package** · [DOCUMENT_DISCOVERY_REPORT.md](DOCUMENT_DISCOVERY_REPORT.md)
> (§7/§8) · [DOC_STANDARDS.md](DOC_STANDARDS.md) (frozen-v1) ·
> [KOS_TARGET_VISION.md](KOS_TARGET_VISION.md) (**vision input only, NOT a contract**).
> Precision rule restated: **knowledge_graph.json = single source FOR GENERATED DOCUMENTATION;
> never project truth** — code + T1 locks stay the territory; fix-at-source, hand-edits
> forbidden. Sections append-only once closed.

---

## KG-0 — Charter + gate + ratification (2026-07-13) ✅

### Gate check — PASS (§7 row 0 / §16.2)

| Check | Result |
|---|---|
| Phase 7 closed, DOCCLEAN-G handoff present | ✓ verdict "CLEANUP-COMPLETE-WITH-DOCUMENTED-RESIDUALS" in cert §8 + log §G; status master row 7 = ✅ |
| Standard `frozen-v1` (transitive) | ✓ frontmatter read from disk |
| Clean substrate | ✓ cert §4: residuals documented, none blocks P8; independent re-review (2026-07-13, post-G) re-verified 25/25 claims + zero old-path links corpus-wide |
| Build log + graph absent pre-session | ✓ (this file = the KG-0 creation; no knowledge_graph.json exists) |

### Fact re-verification (readiness package vs disk, 2026-07-13)

| Fact | Cert §5 / discovery | Re-measured | Verdict |
|---|---|---|---|
| Manifest | 25 topics, 51/51, v2026-07-13 | 25 · 51/51 · v2026-07-13 | ✓ |
| FEATURE_INDEX (R3 seed) | "29 rows" | **28 content rows** (+1 header — the 29 counted the header line; corrected here, content identical) | ✓ (counting nuance, not drift) |
| Service modules | 57 | 57 | ✓ |
| ADRs | 11 (+ index) | 11 numbered files | ✓ |
| Apps | 10 (9 + core) | 10 with apps.py | ✓ |
| Active-tree docs md | 333 (+cert = 334) | 334 | ✓ (cert self-inclusion, expected) |
| docs json | 2 (manifest + stray partial) | 2 | ✓ |
| URL/view/model censuses | 528 / ~238 / ~87 (discovery §8.1) | re-counted authoritatively at KG-A (URLConf walk + apps registry — the census instruments, not grep) | deferred to KG-A by design |

No material drift → §16.3 clear.

### Design Record — KG-D1..KG-D9 rationale (owner-required format: alternatives · why-correct · why-rejected · compatibility · roadmap impact)

Compatibility legend per decision: **STD** = DOC_STANDARDS · **VIS** = KOS_TARGET_VISION ·
**SCH** = Single Canonical Home · **P9/P14/P18** = downstream phases. Every decision:
**roadmap UNCHANGED**.

**KG-D1 — JSON Schema artifact, semver from 1.0.0 → DEFAULT ACCEPTED.**
Alternatives: (a) standalone JSON Schema file [default]; (b) schema-in-validator-code only;
(c) YAML/other schema format; (d) no schema, validator-only. Why (a): consumers (P9
generators, P14 sync) validate WITHOUT importing builder code — the contract's own rule
("Phase 9 consumes the graph ONLY through the schema"); JSON Schema = stdlib-checkable, no new
dependency; tool-death-safe (plain readable file). Rejected: (b) couples consumers to tooling
(violates STD §16 tool-death); (c) new parser dependency for zero gain; (d) makes the §6.7
handoff contract unstatable. Compat: STD ✓ (machine-index typology, generated-class rules) ·
VIS ✓ · SCH ✓ (ONE schema = the one contract) · P9 pins schema major ✓ · P14 extends validator
over the same schema ✓ · P18 regenerates through it ✓.

**KG-D2 — 8-kind closed node set + natural-key IDs → DEFAULT ACCEPTED (OWNER-DIRECTED).**
Alternatives: (a) the ratified 8 kinds [default]; (b) expand v1 with the vision kinds
(templates, forms, handlers-as-distinct, APIs, transactions, permissions, workflows,
DB-relationships, calculations, AI-context, learning-notes); (c) open/extensible kind set;
(d) file-grain-only nodes (no semantic kinds). Why (a): every v1 kind has a **certified census
instrument today** (URLConf walk · apps registry · service-module census · doc registers ·
ADR census · R3 seed) — invariant 8 (completeness floors) demands COUNTED denominators, and
only these 8 have them; v1's sole consumer need is Phase-9 cards/features, which require
exactly these kinds; the additive-minor lane (KG-D6) makes later kinds cheap and safe.
Rejected: (b) the vision kinds lack certified extraction instruments (no template/form/
transaction registry exists; permissions truth lives in code — the `gated_by` edge covers the
navigation need) → adding them now = asserted-not-counted completeness, violating the evidence
standard, and silently expands schema against the owner's explicit prohibition; (c) an open
set breaks invariant 3 (kind-closed) and validator determinism; (d) file-grain loses the
knowledge-level navigation the owner mandated (clarification #6 verdict: v1 SUFFICIENT via
feature/doc nodes). **Vision preservation: NOTHING forgotten — the complete additive-minor
register below carries every vision concept with its future prerequisite.** Compat: STD §19
P8 row verbatim ✓ · VIS §6 anticipated exactly this split ✓ · SCH ✓ (each kind = one
natural-key home; IDs are stable natural keys, never positional) · P9 ✓ (cards consume
url/view/service/model/doc/feature/adr) · P14 ✓ (drift domains map 1:1 onto these kinds) ·
P18 ✓ (feature-close regenerates the same kinds).

**KG-D3 — 8-edge closed set, register-sourced calls/writes → DEFAULT ACCEPTED.**
Alternatives: (a) register-sourced declared-coverage [default]; (b) runtime call-tracing;
(c) static AST import/call analysis; (d) a slimmer edge set (drop gated_by/cites). Why (a):
edges derive from CERTIFIED truth — `writes` from the never_modify single-writer registry
(ADR-0002 law) + chokepoint pages; `calls` from GUIDE tables; `documented_by`/`supersedes`
from the Phase-6/7-verified registers; every edge kind carries a declared extraction source =
honest provenance, deterministic, zero code execution. Rejected: (b) runtime tracing executes
app code (forbidden: read-only introspection, no DB writes) and is nondeterministic; (c) AST
inference invents relationships beyond certified registers (uncited claims — evidence-standard
violation; legitimate FUTURE minor once it gets its own instrument); (d) dropping `gated_by`
loses the permissions navigation dimension (vision item 10 — covered informationally, RBAC
truth stays in code); dropping `cites` loses the hub→truth-lock subordination edges that the
F-B-07 disposition and STD §2 conflict rules depend on. Compat: STD ✓ (cites = machine form of
subordination; supersedes = §12 lifecycle law) · VIS ✓ · SCH ✓ · P9 ✓ (cards' "single writer"
row = writes edge) · P14 ✓ (per-edge drift semantics pre-declared in §6.7 handoff) · P18 ✓.

**KG-D4 — determinism rules → DEFAULT ACCEPTED.**
Alternatives: (a) canonical serialization + zero timestamps + content_hash/built_from meta
[default]; (b) timestamped builds; (c) natural (as-encountered) ordering. Why (a): the
double-build byte-identical proof is THE phase regression instrument (§14); hash-stability is
what lets P14 define "graph-stale" mechanically; mirrors the already-registered R6
determinism concern in PHASE_09 (no wall-clock in generated artifacts). Rejected: (b)
timestamps make every rebuild a spurious diff (breaks proof + pollutes post-22 git);
(c) FS/locale-dependent ordering = non-reproducible. Compat: all ✓ (P9 byte-stable
regeneration inherits the same discipline).

**KG-D5 — invariants 1–8 all-fatal → DEFAULT ACCEPTED.**
Alternatives: (a) all-fatal [default]; (b) warn-tier for cardinality/islands; (c) optional
validation. Why (a): the graph is generated — any violated invariant is a builder bug or a
source defect; the fix-at-source law demands stopping, never warning past (a warned-through
graph would feed Phase-9 generation with known-bad structure). Island detection continues the
Standard §15 no-orphans law at graph level. Rejected: (b)/(c) allow certifying a graph that
P9 would then generate falsehoods from. Compat: P14 extends this validator (never forks) ✓.

**KG-D6 — additive=minor / breaking=major+owner+same-change-consumer-update → DEFAULT ACCEPTED.**
Alternatives: (a) semver discipline [default]; (b) latest-only (no versioning); (c) date
versioning. Why (a): P9/P14 pin the major → the graph can grow (the vision kinds!) without
breaking consumers; **this policy is the ratified vehicle for every additive-minor register
row below**. Rejected: (b) consumer breakage undetectable; (c) dates convey no compatibility
semantics (and violate KG-D4's no-wall-clock spirit). Compat: all ✓.

**KG-D7 — graph = `generated` class; owns nothing, derives → DEFAULT ACCEPTED.**
Alternatives: (a) default; (b) graph as canonical truth; (c) hybrid hand-annotations inside
the graph. Why (a): STD §1.4 (docs are the map; code + locks are the territory) + §11
generated class + §16 tool-death; SCH is PRESERVED precisely because truth stays at the single
canonical sources — the graph is an index of them. Vision §5 ("KOS = first-class production
artifact") is satisfied: first-class as an ARTIFACT (validated, versioned, battery-adjacent
correctness), while truth-ownership stays at sources — no conflict. Rejected: (b) contradicts
the contract's own precision note + STD §1.4 (would create a SECOND home for every truth =
anti-SCH); (c) hand-edits are hash-refused by design; annotations belong in source docs.
Compat: all ✓.

**KG-D8 — semver + content_hash, no in-repo graph history → DEFAULT ACCEPTED.**
Alternatives: (a) default; (b) dated graph copies in-repo; (c) external artifact storage.
Why (a): the graph is regenerable by construction; git supplies history from Phase 22.
Rejected: (b) violates the R8 naming closed-set, duplicates knowledge (anti-SCH), bloats the
uncommitted U2 tree; (c) breaks self-containment/tool-death. Compat: all ✓.

**KG-D9 — builder/validator in `scripts/`, NOT manage.py, battery-never; CI-guard = Phase-14 → DEFAULT ACCEPTED; deviation NOT invoked.**
Alternatives: (a) scripts/ [default]; (b) manage.py command now; (c) invoke the owner-gated
CI-guard deviation now. Why (a): pkals_canonical.py precedent (read-only-over-truth wrapper);
`manage.py test` does not collect scripts/ → the docs-only battery posture holds (baseline
1530/1530 untouched); management commands are explicitly chartered to Phases 12–14. Rejected:
(b) violates the P12–14 charter boundary (that WOULD be a roadmap change — refused); (c)
battery-bearing now for zero benefit: nothing consumes the graph until Phase 9; the guard
belongs with Phase-14's sync (one home for graph guarding — SCH applied to tooling). Compat:
all ✓ · **roadmap UNCHANGED — the P14 CI-guard hook is preserved exactly as chartered.**

### Deliverable 8 — Additive-minor future register (KOS_TARGET_VISION → KG-D6 lane; NOTHING forgotten, NOTHING implemented now)

| Vision concept | v1 representation (today) | Future first-class form | Prerequisite before promotion (its own Design-Record input) |
|---|---|---|---|
| Handlers/views | `view` nodes (handler = view) — IN v1 | — | covered |
| Templates | view/url `anchors` only | `template` kind + `renders` edge | template census instrument (template-dir walk + {% include %} map) |
| Forms | not represented | `form` kind + `validates` edge | forms census (app forms/ packages) |
| APIs | `url` nodes (no separate API surface exists today) | `api` kind | emerges only if a distinct API layer ships (G-phase fences) |
| Transactions + why | prose in chokepoint/LEARNING docs (`doc` nodes) | `transaction` attribute on service nodes / `wraps` edge | transaction registry (atomic-block census); prose-why stays handwritten (R7) |
| Permissions/roles | `gated_by` edges (informational; truth in code) | `permission` kind | permission-constant export from permission_service as a certified register |
| Workflows / user journeys | `doc` nodes (request-journey type) | `workflow` kind | journey completion + a workflow registry |
| DB relationships (FK grain) | `model` nodes + `writes` edges | `relates_to` (FK) edges | model-introspection extractor (apps registry has the data — cheapest future minor) |
| Calculations | `doc`/`adr` nodes (ADR-0009, cost chokepoint) | `calculation` kind | calculation registry (none exists) |
| Business rules | `adr` nodes + FOM (`doc`) | first-class `rule` kind | FOM §5 rulings as an extractable register |
| Certification evidence | `doc` nodes, `type: evidence-cert` — queryable IN v1 | optional first-class kind | none needed now (type attribute suffices) |
| AI context / learning notes | **prose-class — R7: NEVER machine-written**; become `doc` nodes when humans author them | n/a as graph kinds | GEN-0 hybrid-card sections + FFD authoring lane (Phase 9/18) |

### Deliverable 9 — Risks, assumptions, constraints

- **Assumption:** the certified registers (chokepoints · never_modify · GUIDE tables) are the
  complete declared-coverage source for `calls`/`writes` — the known history_service page gap
  (DC-D1 residual) will appear HONESTLY as a missing `documented_by` edge, never faked.
- **Risk — census grain:** discovery's ~238 views / ~87 models are grep-level; KG-A's
  authoritative instruments (URLConf-resolved callables · apps registry) may differ; the §16.3
  drift stop applies only to MATERIAL divergence beyond method explanation.
- **Risk — substrate motion:** any corpus change between KG-0 and KG-A shifts doc-node counts;
  KG-A re-counts first (contract §17.4).
- **Constraints:** read-only introspection (`manage.py shell`-level, zero DB writes, no
  network) · builder/validator write ONLY graph artifacts + scratchpad · no corpus md edits
  (findings → dated Phase-6/7 amendments) · manifest read-only (conversion = Phase 9) ·
  battery never (KG-D9 default held) · transitional-active residuals are ordinary doc nodes
  (correct — they exist and are documented).

### KG-0 scope discipline

Writes this sub-phase: this log (NEW) + PHASE_08 Appendix A (designated fill) +
DOCUMENTATION_INDEX row + status + memory = §9 exactly. Zero code · zero corpus edits ·
manifest untouched · battery not run · graph/schema NOT created (KG-B/C work). Stop §16.1
normal close.

---

## KG-A — Source-extraction census (2026-07-13) ✅

Owner guidance honored: pure evidence-gathering · deterministic read-only extraction only ·
no inferred/guessed relationships · no runtime execution (Django `setup()` + registry/URLConf
introspection only — zero DB queries, zero writes, zero network) · no synthetic nodes · every
discrepancy classified, no denominator silently adjusted. Design Record untouched (frozen; no
amendment needed — nothing proved unimplementable).

### 1. Final authoritative census (per node kind)

| Kind | Count | Instrument (reproducible command = scratchpad `kg_a_census.py`, output quoted) |
|---|---|---|
| **app** | **10** | `config/<label>/apps.py` presence ∩ Django app registry (all 10 registered): accounts · core · expense · inventory · machines · patterns_ai · production · raw_materials · storefront · tracking. Vendor apps (django.contrib, allauth) excluded by definition — project apps only |
| **url** | **528** | recursive root-URLConf walk (`get_resolver()`, URLResolver/URLPattern descent — the MGT-H instrument): 482 named + 46 unnamed; per-route (namespace, url_name, pattern, view-callable) table = `kg_a_urls.tsv` |
| **view** | **229 project** (+38 vendor, listed separately) | unique view callables actually serving the 528 routes (CBV → `view_class`, FBV → unwrapped function); vendor callables (django.contrib/allauth, serving 298 admin/auth plumbing routes) censused but flagged vendor |
| **service** | **57** | file census `config/<app>/services/*.py` excluding `__init__.py` + `_`-prefixed helpers (excluded + documented: `expense._shared`, `production._shared` — shared money-primitive helpers, not single-writer services) |
| **model** | **88** | Django apps registry `get_models()` (concrete, non-abstract, project apps; **0 proxies**): accounts 5 · expense 11 · machines 2 · patterns_ai 21 · production 32 · raw_materials 4 · storefront 7 · tracking 6 · core 0 · inventory 0 (both by design: core = abstract bases only, inventory = umbrella app, no tables) |
| **doc** | **355** = 353 md + 2 json | DD-1 active boundary: docs/** minus archive (335 md incl. this log) + 8 root companions + 10 config READMEs + deploy/README + 2 machine-index json; frontmatter carriers 223 |
| **adr** | **11** | `docs/adr/NNNN-*.md`, numbering 1..11 **contiguous** (guard-test invariant confirmed at extraction) |
| **feature** | **28** | FEATURE_INDEX content rows (R3 seed); derived kebab slugs **28/28 unique** (no dedup needed) |

Extraction tables (the KG-C builder's input contract) preserved in scratchpad:
`kg_a_urls.tsv` (528 rows) · `kg_a_models.tsv` (88) · `kg_a_services.tsv` (57) ·
`kg_a_docs.tsv` (355) · `kg_a_features.tsv` (28).

### 2. Extraction methodology (all deterministic + reproducible)

Single read-only script (`kg_a_census.py`): Django `setup()` under `config.settings.local` →
apps registry + `get_resolver()` walk (sorted, no wall-clock, no environment-dependent
ordering beyond URLConf declaration order, which is source-stable) → sorted file censuses for
services/docs/ADRs → FEATURE_INDEX row parse with deterministic slugging. No ORM query
executed; no test client; no login. Edge-source contract (for KG-C, unchanged from KG-D3):
routes_to/gated_by from the URL table · calls/writes from the certified registers
(never_modify + chokepoints + GUIDE) · documented_by/supersedes/cites from frontmatter +
Phase-6/7 registers · belongs_to_feature from the R3 seed.

### 3. Reconciliation vs Phase-6 discovery census

| Kind | Discovery (method) | KG-A authoritative | Classification |
|---|---|---|---|
| url | **528** (MGT-H certified walk) | **528** | **EXACT MATCH** — zero drift since certification |
| view | ~238 (grep `^class \w+.*View`) | **229 project callables** | **expected methodological improvement**: grep counted class *definitions* in files; the walk counts callables *serving routes* — the graph's correct denominator (routes_to targets). Both figures retained; neither adjusted silently |
| model | ~87 (grep `models.Model|TimeStampedModel` bases) | **88** | **expected methodological improvement, delta fully closed**: registry-only +4 = `accounts.User` (AbstractUser base) + `tracking.{Adda,ClothRoll,Product}History` (core.AbstractHistoryEntry base) — base-class patterns the grep missed; grep-only −3 = `core.{TimeStampedModel,AbstractHistoryEntry,FieldChangeMixin}` = ABSTRACT bases, correctly absent from the registry. 87 − 3 + 4 = 88 ✓ |
| service | 57 (file census) | **57** | EXACT (same instrument, `_shared` exclusion now explicitly documented) |
| app | 10 | **10** | EXACT |
| adr | 11 | **11** | EXACT + contiguity proven |
| doc | 334 active md (F-time) | **353 md + 2 json = 355** | **explained composition**: 334 + this build log (KG-0 creation) = 335 docs/-md; + 18 boundary companions (8 root + 10 config READMEs) + deploy README... = 353 md; + 2 machine-index json. Boundary = DD-1 (discovery's own definition); no drift |
| feature | 28 content rows (KG-0 corrected count) | **28**, slugs unique | EXACT |

**Classified discrepancies: 2, both "expected methodological improvement" (view, model) — no
documentation drift, no repository drift, no contract-level issue. No denominator silently
adjusted; every prior figure retained beside its authoritative successor.**

### 4. KG-0 Design-Record satisfaction — CONFIRMED

Every KG-D2 node kind has a counted, reproducible denominator ✓ · natural keys available per
kind (namespace:url_name unique for named routes; 46 unnamed routes get pattern-derived keys —
an extraction-table detail for KG-C, flagged) · KG-D3 edge sources all exist as certified
registers ✓ · completeness floors (invariant 8) now have authoritative values ✓ ·
determinism-compatible extraction proven (sorted walks, no timestamps) ✓.

**Flagged for KG-B/C (extraction-contract details, NOT Design-Record changes):** (a) 46
unnamed routes → id scheme `url:<mount-pattern>` fallback (deterministic; noted for the
schema's id rules); (b) vendor views (38) → censused but EXCLUDED from project view nodes
(vendor routes keep routes_to to a vendor-view stub? decision: vendor callables appear as
view nodes flagged `vendor: true` OR routes to them carry a note — **KG-B schema decision,
flagged not guessed**); (c) core/inventory legitimately have 0 models (island-invariant 7
must permit model-less apps — consistent with §6.3 "apps never islands" via their url/doc
edges).

### 5. Scope discipline

Read-only throughout (script writes only scratchpad TSVs). Zero corpus/code/manifest changes.
Battery not run. Writes = this log section + status + memory. git HEAD 49404001 · 2 stashes ·
0 staged.

_Section closed 2026-07-13. KG-B (schema authoring) may safely begin — all inputs counted,
classified, and Design-Record-conformant._

## KG-B — Schema authoring (2026-07-13) ✅

Schema-authoring ONLY (owner): no graph, no nodes, no edges generated. Design Record frozen —
no field invented beyond the ratified v1; everything else stays in the §KG-0 additive-minor
register. Deliverable: **`docs/knowledge_graph.schema.json`** (JSON Schema draft-07,
version **1.0.0**).

### Node definitions (8 kinds — required/optional/keys/constraints/ownership/derivation/consumers)

Common required: `id · kind · label · anchors[≥1]` (anchors = repo-relative existence proofs).
Ownership semantics (KG-D7): every attribute DERIVED from its declared source — the graph owns
nothing. Downstream consumers: P9 generators (cards/features/indexes), P14 sync (drift
domains), P18 lifecycle (regeneration at feature-close).

| Kind | id natural-key | Kind-required | Optional | Derivation source | Consumer expectation |
|---|---|---|---|---|---|
| app | `app:<label>` | app_label | — | apps registry ∩ config/<label>/apps.py | P9 app sections; P14 app-scope drift |
| url | `url:<ns>:<name>` · unnamed → `url:_unnamed:<pattern-slug>` | pattern, mount, named | namespace, url_name(nullable), gate(informational — RBAC truth stays in code) | root-URLConf walk | P9 url-cards (R4 grain); P14 route drift |
| view | `view:<module.Name>` | module, name, **vendor(bool)** | — | URLConf callback resolution | P9 card "view" row |
| service | `service:<app>.<module>` | app_label, module | single_writer_of[] (register-sourced) | file census + never_modify registry | P9 card "services"; P14 writer drift |
| model | `model:<app>.<Model>` | app_label, model_name, table | single_writer(nullable — honest absence) | apps registry + never_modify | P9 card "models written" |
| doc | `doc:<path>` | path, tier, doc_type(20-enum), owner_class(5-enum), lifecycle | — | frontmatter (223 carriers) else census rows; lifecycle "unknown" allowed for pre-retrofit (honest, never guessed) | P9 documented_by targets; P14 staleness |
| feature | `feature:<r3-slug>` | slug, seed_source(const = FEATURE_INDEX) | — | R3 seed | P9 features/ tree scaffold |
| adr | `adr:<NNNN>` | number, status | — | docs/adr census | P9 cites targets; P18 decision routing |

### Edge definitions (8 kinds, closed)

Required on EVERY edge: `from · to · kind · source` (+optional note). **`source` is a closed
9-value enum** (urlconf · register:never_modify · register:chokepoints · register:guide ·
frontmatter · banner · feature_index · manifest · documentation_index) — machine-enforcing
the owner rule: **no inferred, guessed, or runtime-traced relationship can exist** (an edge
without a declared certified source fails shape validation). Endpoint-kind semantics per edge
kind documented in the schema `$comment` (validator-enforced: routes_to url→view · gated_by
url→service|doc · calls view→service · writes service→model · documented_by
url|model|service|view|app→doc · belongs_to_feature url|doc|service|model→feature ·
supersedes doc→doc · cites doc→doc|adr).

### The three KG-A flags — resolved as documented schema decisions

1. **Unnamed-route id fallback:** `url:_unnamed:<slug-of-full-mount-pattern>` — deterministic
   from URLConf source; slug collision = build FAILURE routed to a source finding (never
   auto-suffixed). Named routes keep `url:<namespace>:<url_name>`.
2. **Vendor-view representation:** vendor callables ARE view nodes with **`vendor: true`**
   (referential integrity: all 528 routes_to targets exist); completeness floor binds
   vendor:false nodes (≥ census.view_project = 229); vendor floor informational; vendor
   anchors = the served route mounts (site-packages ≠ repo anchors).
3. **Model-less-app rule:** apps with zero models (core, inventory) are VALID; invariant 7
   (apps never islands) is satisfied THROUGH `documented_by` edges to their README/GUIDE doc
   nodes — connectivity via documentation, not tables.

### Validation rules (KG-D5 — shape in schema, semantics in validator)

Shape (schema-expressible): closed kind/edge/source enums · per-kind required fields · id
regexes · meta block (semver 1.x pattern · `sha256:` hash format · built_from.census with all
9 denominators). Semantic invariants 1–8 (validator, all fatal): id-unique · referential
integrity · closed kinds · cardinality (url→exactly-1-view; ≤1 url-card per url; superseded
doc→exactly-1 successor) · supersedes-acyclic · doc-paths-exist · island rules ·
**completeness floors ≥ meta.built_from.census** (the KG-A denominators are IN the graph's
meta — self-describing floors).

### Serialization rules (KG-D4, stated in the schema description)

Canonical JSON: sorted object keys · nodes sorted by id · edges sorted by (from, kind, to,
source) · indent 2 · UTF-8 · single trailing newline · **zero wall-clock timestamps anywhere**
· `content_hash` = sha256 of the canonical body with the hash value blanked · `built_from` =
git HEAD + census totals (change only when inputs change).

### Evidence — example validation (stdlib, scratchpad `kg_b_examples.py`)

**Tooling disclosure:** the frozen venv has NO third-party `jsonschema` library (installing =
environment change, forbidden). The `.schema.json` is standard draft-07 for external
consumers; the shape checks ran via a stdlib checker implementing the schema's rules — the
same engine KG-D's validator extends. **Result: 1 VALID example PASS ✓ · 6 deliberately-invalid
examples each REJECTED for the specified reason ✓** (unknown node kind `handler` · doc missing
`tier` · url id pattern violation · unknown edge kind `depends_on` · **undeclared edge source
`runtime_trace`** · malformed content_hash). Full output quoted in session evidence; schema
file parses as valid JSON.

### Compatibility analysis

- **Phase 9:** consumes ONLY through this schema (contract rule); card fields map 1:1 (url
  node + routes_to/gated_by/writes/documented_by edges = the R4 card rows); features tree from
  feature nodes + belongs_to_feature; manifest-view from documented_by/cites (KG-E mapping
  table upcoming); byte-stable serialization matches GEN determinism law. ✓
- **Phase 14:** pins schema major 1; extends the same validator; per-edge `source` enum gives
  sync its drift taxonomy (code-side vs doc-side vs graph-stale per source class); content_hash
  = the staleness primitive. ✓
- **Phase 18:** feature-close regeneration reproduces the same kinds; additive-minor lane
  (KG-D6) absorbs future vision kinds without breaking consumers. ✓
- **DOC_STANDARDS/SCH:** doc_type/owner_class/tier enums copied verbatim from the Standard's
  closed sets; graph = index-never-truth preserved. ✓ Roadmap unchanged.

### Scope discipline

Writes: `docs/knowledge_graph.schema.json` (NEW — §9-listed artifact) + this log section +
status + memory. No graph/nodes/edges generated. Zero corpus/code/manifest changes. Battery
not run. git HEAD 49404001 · 0 staged.

_Section closed 2026-07-13. KG-C (builder + first build) may safely begin._

## KG-C — Builder + first build (2026-07-13) ✅

Builder: **`scripts/build_knowledge_graph.py`** (KG-D9 location; stdlib + Django read-only
introspection; writes ONLY `docs/knowledge_graph.json`). Owner rules enforced in code: every
edge carries its declared source; a relationship without a certified register stays ABSENT
and is printed in the builder's **loud absence report** (never silent, never inferred); id
collision = hard BUILD FAILURE (never auto-suffixed); no runtime business logic executed
(URLConf walk + apps registry only — the same KG-A instruments).

### 1. Generation summary

First build produced a schema-1.0.0 graph: **1,345 nodes · 635 edges**, meta carrying
git_head + the census floors + `content_hash`. One determinism bug was caught and fixed IN
THE BUILDER before the proof (per KG-D4's own rule, logged): the boundary walk initially
included the graph's own output file → build #2 would have gained a `doc:docs/knowledge_graph.json`
node (self-inclusion instability). Fix = the builder excludes its own artifact from the doc
boundary. Rebuilt clean.

### 2. Node counts by kind (vs KG-A floors)

| Kind | Built | Floor (KG-A) | Verdict |
|---|---|---|---|
| app | 10 | 10 | exact |
| url | 528 | 528 | exact |
| view (project) | 229 | 229 | exact |
| view (vendor, flagged) | 38 | 38 informational | exact |
| service | 57 | 57 | exact |
| model | 88 | 88 | exact |
| doc | **356** | 355 | ✓ floor met; +1 = `knowledge_graph.schema.json` (born at KG-B, a legitimate boundary machine-index; the GRAPH itself is excluded by the determinism guard) |
| adr | 11 | 11 | exact |
| feature | 28 | 28 | exact |
| **total** | **1,345** | | |

### 3. Edge counts by kind (all source-tagged)

| Kind | Count | Source(s) |
|---|---|---|
| routes_to | 528 | urlconf (1 per route — cardinality exact by construction) |
| belongs_to_feature | 39 | feature_index (exact-token url/model matches only) |
| documented_by | 34 | register:guide (10 app→README + 10 app→GUIDE + 9 model→DATABASE_GUIDE) + register:chokepoints (5 service→page) |
| cites | 25 | manifest (topic canonical → also[] routing, doc→doc + doc→adr) |
| writes | 9 | register:never_modify (ADR-0002 single-writer registry; `single_writer`/`single_writer_of` attrs set symmetrically) |
| calls / gated_by / supersedes | **0 — ABSENT BY EVIDENCE** (see findings) |
| **total** | **635** | |

### 4. Coverage report

Completeness floors (invariant 8): **9/9 kinds ≥ census** — 8 exact + doc explained (+1
schema). Every 528 routes_to target resolves (vendor views are nodes, `vendor:true`).
Documented_by coverage mirrors the certified registers honestly: 9/88 models have
DATABASE_GUIDE pages, 5/57 services have chokepoint pages — the graph REPORTS the real
documentation coverage; it does not pad it (that gap analysis is precisely Phase-9/14 input).

### 5. Determinism proof

Build run twice post-fix: **`diff` = EMPTY (byte-identical)**; both files hash to a single
sha256; the graph's `content_hash` identical across runs:
`sha256:858a2a6f9643ad2a1d6548c0982e493bab39b3a54c6c69bb109834d72b94a922`.

### 6. Content-hash proof

Independent recomputation (hash-blanked canonical body → sha256) **MATCHES the stored value**
— the KG-D7 hand-edit guard works: any manual byte change breaks the match and the validator
will refuse it.

### 7. Serialization proof

Verified on the artifact: nodes sorted by id ✓ · edges sorted by (from, kind, to, source) ✓ ·
sorted object keys (json sort_keys) ✓ · indent 2, UTF-8, single trailing newline ✓ · **zero
wall-clock timestamps in the body** ✓.

### 8. Classified findings / residuals (the loud-absence report, 9 items)

| # | Class | Finding | Disposition |
|---|---|---|---|
| C-1 | absent-by-evidence (edge kind) | `calls` = 0: no certified machine-extractable view→service register exists (GUIDE tables are file-grain) | remains absent; candidate future register/instrument (additive lane); Phase-9 cards simply omit the row |
| C-2 | absent-by-evidence (edge kind) | `gated_by` = 0: no gate-census artifact; RBAC truth stays in code regardless | remains absent; candidate future instrument |
| C-3 | absent-by-evidence (edge kind) | `supersedes` = 0: no ACTIVE-tree doc carries a strict single-successor banner; RAW_MATERIALS (`lifecycle: superseded`) names TWO live-truth pointers → not a provable single successor | classified; KG-D interpretation question: invariant 4 constrains supersedes EDGES, not lifecycle strings — to be confirmed at validation |
| C-4 | non-model target | never_modify "processing_cost freeze" = a FIELD freeze, not a model → no writes edge | correct absence; noted |
| C-5 | filename-rule miss | chokepoint page `ledger_and_payment.md` matches no service module name → its 2 documented_by edges (ledger_service, settlement_service) not machine-provable by the filename rule | absent-not-guessed; the manifest topic routing still reaches the page (cites lane); candidate explicit mapping at Phase-9 manifest-view table |
| C-6..C-9 | unparsable feature rows | 4 features (settlement-reverse-supersede · leftover-consume · public-homepage · pattern-layout-tool) have no exact-token url/model in their FEATURE_INDEX cells (prose like "(same, action=reverse)", "(no UI yet)", "/") → no belongs_to_feature edges | absent-not-guessed; the feature NODES exist; linkage = Phase-9 feature-doc authoring input |

### 9. Scope discipline

New files: `scripts/build_knowledge_graph.py` + `docs/knowledge_graph.json` (both §9-listed).
Zero corpus md edits · manifest read-only · zero DB writes (introspection only) · battery not
run (builder outside test surface, KG-D9). git HEAD 49404001 · 0 staged · 2 stashes.

_Section closed 2026-07-13. KG-D (validator + full invariant suite) may safely begin._

## KG-D — Validator + validation run — DONE 2026-07-13

**Owner directives honored:** validation-and-proof only · schema/builder/graph NOT modified
except through the owner's explicit exception clause ("unless the validator proves a genuine
contract-level defect") — which fired ONCE, was STOPPED on, classified, evidenced, and recorded
as a dated amendment in the Phase 8 contract BEFORE any repair · every proof recomputed
independently · builder output never trusted unverified.

### 1. The validator instrument

`scripts/validate_knowledge_graph.py` (new, §KG-D9 home: `scripts/`, NOT manage.py, battery
never touches it). Independent by construction:

- **Schema-driven, not builder-driven** — kind enums, id regexes, required fields, edge
  `source` enums are parsed from `docs/knowledge_graph.schema.json` at runtime, so the
  validator cannot inherit a builder assumption.
- **Sections:** [1] schema shape (top-level keys · semver · hash format · census denominators ·
  all 1,345 node shapes · all 635 edge shapes) · [2] semantic invariants INV-1..7 + endpoint-kind
  table for all 8 edge kinds · [3] INV-8 completeness floors via **independent recount**
  (fresh URLConf walk, `get_app_configs()`/`get_models()`, service-file glob, docs/adr/feature
  recount — same instruments as KG-A, re-executed, never read from `meta`) · [4] content-hash
  independent recompute (hand-edit guard) · [5] serialization law (sorted nodes/edges/keys,
  no timestamps) + **reproducibility**: re-runs the builder to a temp path and byte-compares.
- `jsonschema` lib absent from the frozen venv (installing = forbidden env change) — disclosed;
  all checks are hand-rolled stdlib equivalents driven by the schema file itself.
- One instrument bug during authoring (mine, not the graph's): `len(generator)` TypeError in
  the model recount — fixed to an explicit counter before any verdict was read. Disclosed;
  validator bugs are not graph defects.

### 2. The contract-level defect (stop → classify → amend → repair)

First full run: **3 real nodes failed schema shape validation** —

- `url:media-protected`, `url:media-public` — legitimate NAMESPACE-LESS url names containing
  hyphens; the KG-B url regex's first segment `[a-z0-9_]+` assumed namespace-style tokens.
- `view:allauth.socialaccount.providers.oauth2.views.OAuth2View.adapter_view.<locals>.view` —
  vendor closure qualname; `<locals>` sits outside the KG-B view charset `[A-Za-z0-9_.]+`.

Classification: the KG-B regexes were **narrower than the KG-D2-ratified natural-key law**
(url = Django url name as-is; view = qualname as-is). The ids are CORRECT; the schema was
wrong. Genuine contract-level defect → owner's exception clause applies.

Disposition (dated amendment recorded in `docs/campaign_contracts/PHASE_08_KNOWLEDGE_GRAPH.md`
→ "Dated amendments", 2026-07-13): schema **1.0.0 → 1.0.1**, constraint-WIDENING only (url
first segment → `[a-z0-9_-]+`; view charset → `[A-Za-z0-9_.<>]*`) — every previously-valid id
stays valid = backward-compatible patch per KG-D6. Builder change in the same defect chain:
`schema_version` now **read from the schema file** instead of hardcoded (removes the
version-drift risk this exact incident exposed). Graph rebuilt; full suite re-run.

### 3. Hash-delta proof (node/edge content byte-unchanged)

Rebuild at 1.0.1 → `content_hash` `sha256:85b7fd6d52041e4a529e68d231df01ae6ee09497e1d60eb2a7a89bdf34578fad`
(KG-C was `sha256:858a2a6f…`). Proven attributable SOLELY to the `meta.schema_version` string:
taking the 1.0.1 artifact, substituting `"schema_version": "1.0.0"`, and recomputing the
canonical hash reproduces the KG-C certified digest **exactly** (`858a2a6f9643…` MATCH: True).
Zero node or edge bytes changed across the patch.

### 4. Full validator verdict (re-run after patch)

```
[1] SCHEMA SHAPE — 6/6 PASS (1,345 node shapes, 0 offenders; 635 edge shapes; semver 1.0.1)
[2] SEMANTIC INVARIANTS — INV-1 (1345/1345 unique) · INV-2 (0 dangling) · INV-3 · endpoint-kind
    (0 bad) · INV-4a (528 urls → exactly 1 view each) · INV-4b (0 url→card edges; cards = Phase 9)
    · INV-4c (0 superseding docs) · INV-5 (acyclic, 0 edges) · INV-6 (356/356 doc paths on disk)
    · INV-7 (0 app islands) — ALL PASS
[3] COMPLETENESS FLOORS — independent recounts app 10 · url 528 · view_project 229 · service 57
    · model 88 · doc 356 · adr 11 · feature 28 — all EQUAL node counts EQUAL meta census — PASS
[4] CONTENT HASH — independent recompute matches stored (hand-edit guard armed) — PASS
[5] SERIALIZATION + DETERMINISM — canonical bytes ✓ · sort laws ✓ · zero timestamps ✓ ·
    REPRODUCIBILITY: independent builder re-run → byte-identical artifact ✓ — ALL PASS

VERDICT: ALL INVARIANTS PASS — GRAPH CERTIFIED AS BUILT (exit 0)
```

### 5. INV-4c / C-3 interpretation — CONFIRMED

KG-C's open question (loud-absence C-3) is settled as documented: **invariant 4c constrains
`supersedes` EDGES (each superseding doc → exactly one successor), not `lifecycle` strings.**
`docs/production/RAW_MATERIALS.md` (`lifecycle: superseded`, names TWO live-truth pointers)
therefore correctly has ZERO supersedes edges — surfaced by the validator as an INFO
honest-absence finding, not a violation.

### 6. Findings register (non-fatal, routed out)

| # | Class | Finding | Route |
|---|---|---|---|
| V-1 | orphan-signal | **298 doc islands** (docs with zero edges) — expected: only 34 documented_by + 25 cites edges exist at v1 | Phase-9 card/`documented_by` authoring is the designed resolution (§6.3-7: doc islands non-fatal) |
| V-2 | permitted islands | adr 7 · feature 4 · model 62 · service 50 with zero edges | same Phase-9 lane; model/service linkage = future `calls`/`writes` registers (additive-minor) |
| V-3 | INFO honest-absence | RAW_MATERIALS `lifecycle: superseded`, 0 supersedes edges | correct per §5 above |
| V-4 | INFO provenance | `meta.built_from.git_head: "unknown"` — repo root is `/home/tech/umesh-personal` (parent dir), so the builder's `django_inventory/.git/HEAD` probe never resolves; deterministic fallback, **identical in the certified KG-C artifact** (byte-proof §3 covers it) | not a contract defect (no invariant governs git_head); candidate 1-line builder improvement at KG-E/F if owner wants HEAD provenance |

### 7. Scope discipline

Files touched this sub-phase: `scripts/validate_knowledge_graph.py` (NEW, §9-listed) ·
`docs/knowledge_graph.schema.json` (1.0.1 patch, amendment-covered) ·
`scripts/build_knowledge_graph.py` (version-read change, amendment-covered) ·
`docs/knowledge_graph.json` (rebuilt artifact) · Phase 8 contract (dated amendment) · this log.
Zero corpus md edits · zero DB writes · battery NOT run (KG-D9: builder/validator outside the
test surface; baseline 1530/1530 stands) · git HEAD `49404001` · 0 staged · 2 stashes.

_Section closed 2026-07-13. **GRAPH CERTIFIED AS BUILT (schema 1.0.1).** KG-E (consistency
proofs vs manifest/FEATURE_INDEX/DOCUMENTATION_INDEX + manifest-view mapping) may safely begin
on owner approval._

## KG-E — Consistency proofs — DONE 2026-07-13

**Owner order (verbatim intent, dated amendment in the Phase-8 contract):** "KG-E is the
certification and handoff phase only" — the owner's 2026-07-13 approval merged KG-E (§6.5
consistency proofs) and KG-F (§6.7 certification + handoff) into one terminal session. **No
contract content skipped**: §6.5 proofs below; §6.7 handoff in §KG-F. Schema, builder,
validator, graph ALL UNTOUCHED this session (no contract-level inconsistency found — the
owner's precondition for modification never fired).

### 1. Instrument

Read-only proof script (scratchpad, never in-repo): loads the CERTIFIED graph (hash
`85b7fd6d…`, exactly as KG-D validated — not regenerated), the live `canonical_manifest.json`
(v2026-07-13), `FEATURE_INDEX.md`, `DOCUMENTATION_INDEX.md`. Zero writes, zero DB, battery
never.

### 2. Proof 1 — graph ⊇ canonical_manifest (25 topics)

- **25/25 canonical paths → nodes** (doc: or adr: — ADR canonicals resolve to adr nodes).
- **All also[] FILE paths → nodes.** One also[] entry is a DIRECTORY pointer
  (`docs/LEARNING_2_0/APPS/`, topic 13) — **no node BY DESIGN** (schema law: doc kind = file
  paths); the builder emitted no edge for it and the independent recompute expected none →
  both sides agree. Classified finding E-1, routed to GEN-0 (manifest-view generator carries
  directory pointers as prose/dir-listing).
- **cites edges recomputed from the manifest == the graph's 25/25 EXACTLY** (set-equal on
  (from,to); zero missing, zero extra).
- Entry paths → nodes ✓ · **7/7 chokepoint_services register entries → service nodes** ✓.

### 3. Proof 2 — graph ⊇ FEATURE_INDEX

- Index content rows (EXACT builder row-law re-applied): **28 == 28 feature nodes**, slug
  set-equal.
- **39/39 `belongs_to_feature` edges endpoint-valid.**
- Features with zero edges = **exactly the 4 KG-C classified unparsable rows**
  (leftover-consume · pattern-layout-tool · public-homepage · settlement-reverse-supersede)
  — loud absence stable, nothing appeared or vanished.

### 4. Proof 3 — graph attributes vs DOCUMENTATION_INDEX

- Index-linked doc paths: 115 on disk. **114/114 ACTIVE-tree paths → doc nodes.** 1 path is
  `docs/archive/audits/DOC_AUDIT_2026_06_12.md` — the graph's certified boundary EXCLUDES
  `docs/archive/**` (KG-A census = ACTIVE tree), and the index row itself labels the file
  "**archived** … history only" → **agreement, not divergence** (finding E-2, boundary-exempt,
  recorded).
- Lifecycle contradictions (active-tree node claiming superseded/archived while indexed as
  live): **0**.
- doc node count 356 == meta census ✓ (composition verified from the graph: 353 md + 3 json;
  7 root docs + 10 app READMEs included per `doc_boundary()`).

**Per-router verdict: ALL PASS. Divergences: 0. Classified findings: E-1, E-2 (both
representation-boundary, neither a graph/schema/builder defect).**

### 5. The manifest-view mapping table (Phase-9 GEN-D input spec)

Law: **manifest-view = for each topic: match[] terms → canonical node → cites edges
(source=manifest) → also nodes.** The generator reads the GRAPH ONLY; the manifest file
becomes a generated view at GEN-D. Directory pointers (E-1) carried as prose. Node ids below
abbreviated (`doc:docs/` stripped; `ADR-` = adr node).

| # | match[0] | canonical node | match terms | also nodes (cites targets) |
|---|---|---|---|---|
| 0 | worker assignment | `ARCHITECTURE_V2.md` | 5 | LEARNING_2_0/CHOKEPOINTS/worker_task_service.md, LEARNING_2_0/ARCHITECTURE_EXPLAINED/06_why_two_truths.md |
| 1 | settlement | `LEARNING_2_0/CHOKEPOINTS/adda_settlement_service.md` | 5 | ARCHITECTURE_V2.md, ADR-0005, ADR-0007 |
| 2 | two truths | `ADR-0005` | 4 | LEARNING_2_0/ARCHITECTURE_EXPLAINED/06_why_two_truths.md |
| 3 | ledger credit timing | `ADR-0007` | 7 | LEARNING_2_0/ARCHITECTURE_EXPLAINED/10_why_eras.md, LEARNING_2_0/CHOKEPOINTS/allocation_service.md |
| 4 | ledger | `LEARNING_2_0/CHOKEPOINTS/ledger_and_payment.md` | 6 | ADR-0002, LEARNING/02_DATABASE_RELATIONSHIPS.md |
| 5 | costing | `ADR-0009` | 5 | LEARNING_2_0/CHOKEPOINTS/cost_service.md |
| 6 | commerce | `ADR-0008` | 5 | ADR-0010 |
| 7 | tracking mode | `REQUIREMENT_REVIEW_STAGE_TRACKING.md` | 5 | LEARNING_2_0/CHOKEPOINTS/worker_task_service.md |
| 8 | request flow | `PROJECT_KNOWLEDGE_MAP.md` | 4 | LEARNING_2_0/REQUEST_JOURNEYS/README.md |
| 9 | a URL | `LEARNING_2_0/URL_ATLAS.md` | 3 | — |
| 10 | request call chain | `LEARNING_2_0/REQUEST_JOURNEYS/README.md` | 3 | — |
| 11 | data model | `LEARNING_2_0/DATABASE_GUIDE/README.md` | 5 | LEARNING/02_DATABASE_RELATIONSHIPS.md, PROJECT_KNOWLEDGE_MAP.md |
| 12 | chokepoint services | `PROJECT_KNOWLEDGE_MAP.md` | 3 | LEARNING_2_0/CHOKEPOINTS/README.md |
| 13 | an app's files | `apps/README.md` | 3 | — (also[] = directory pointer, E-1) |
| 14 | future-phase doc work | `LEARNING_2_0/LIVING_DOCUMENTATION_SYSTEM/CHANGE_IMPACT_MATRIX.md` | 5 | LEARNING_2_0/LIVING_DOCUMENTATION_SYSTEM/OWNERSHIP_MATRIX.md |
| 15 | what is still to build | `PENDING_BACKLOG.md` | 4 | DEPLOYMENT_BACKLOG.md |
| 16 | working rules | `CLAUDE.md` (root) | 4 | — |
| 17 | current state | `MANUFACTURING_V1_FREEZE.md` | 5 | DEPLOYMENT_CAMPAIGN_STATUS.md |
| 18 | product truth | `PRODUCT_DESIGN_DOCUMENT.md` | 5 | — |
| 19 | operations | `FACTORY_OPERATIONS_MASTER.md` | 6 | MANUFACTURING_V1_FREEZE.md |
| 20 | machines | `config/machines/README.md` | 4 | apps/machines/GUIDE.md |
| 21 | patterns | `AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md` | 5 | AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md, apps/patterns_ai/GUIDE.md |
| 22 | deployment | `deploy/README.md` (root tree) | 5 | — |
| 23 | documentation rules | `DOC_STANDARDS.md` | 6 | — |
| 24 | campaign | `DEPLOYMENT_CAMPAIGN_STATUS.md` | 5 | campaign_contracts/README.md |

_Section closed 2026-07-13. Zero divergences; E-1/E-2 classified. §KG-F (same session, owner-merged) follows._

## KG-F — Certification + Phase-9/14 handoff — DONE 2026-07-13

**The permanent certification artifact = [KNOWLEDGE_GRAPH_CERTIFICATION.md](KNOWLEDGE_GRAPH_CERTIFICATION.md)**
(evidence-cert, append-only) — final graph version + schema 1.0.1 + node/edge censuses +
determinism/validation/content-hash/completeness proof summary + **residual register R-1..R-10**
(KG-C loud-absences + KG-D INFOs + KG-E E-1/E-2 + the R-10 instrument hazard, every one routed) + additive-minor future
register pointer (§KG-0, 12 rows — nothing from KOS_TARGET_VISION forgotten) + Phase-9/14/18
compatibility + architectural assessment + PHASE 8 VERDICT.

§6.7 handoff content (recorded in the certification §7):
(a) **generator input spec** — url-cards ← url nodes + routes_to; feature docs ← feature
nodes + belongs_to_feature; index tables ← kind censuses; manifest-view ← the §KG-E.5
mapping table; (b) **sync contract sketch** — Phase 14 re-checks INV-1..8 + floors
continuously; drift per `source` enum: urlconf-sourced = code-side, register-sourced =
doc-side, hash-mismatch-vs-rebuild = graph-stale; (c) **version-pinning** — consumers pin
major v1; additive = minor, breaking = major + owner + same-change consumer update;
(d) **open items** → GEN-0 (R-4, R-5, R-8) · Phase-14 (R-1..R-3 instruments) · owner-gated
minor (R-7).

Ownership + tool-death declaration (per §11): the graph + schema are `generated`/frozen-shape
artifacts — **an index, not truth**; loss of scripts = fallback to handwritten docs + code;
nothing irreplaceable lives in the graph. DOCUMENTATION_INDEX rows for graph + schema +
certification added this session (§11c).

Every census row accounted (KG-A denominators == meta census == node counts == independent
recounts). No unaccounted rows; no open divergences.

**Bootstrap boundary (disclosed, by necessity):** the consistency proofs ran against the
corpus AS OF the certified build; this session then created `KNOWLEDGE_GRAPH_CERTIFICATION.md`
and the §11c index rows — post-build docs that are NOT nodes in the certified graph. Correct
by design: (a) rebuilding to include the certification would change the hash the certification
cites (unterminating chase); (b) `knowledge_graph.json` self-exclusion is the KG-C determinism
law; (c) new-docs-after-build = exactly the graph-staleness class Phase 14 exists to detect
(`content_hash` vs rebuild). First Phase-14 sync (or any owner-ordered rebuild) picks them up
as ordinary doc nodes.

**PHASE 8 VERDICT: COMPLETE — KNOWLEDGE GRAPH CERTIFIED. Phase 9 CLEARED (gated at GEN-0).**

### Dated correction (2026-07-13, same session — incident disclosed, artifact restored byte-identical)

During post-certification adversarial re-verification, a verification agent — following a
main-thread instruction that was WRONG — re-ran the builder **in place** to re-prove
determinism. The corpus had grown since the certified build (this session's certification
doc), so the rebuild differed and overwrote the certified artifact (hash `1138f57b…`,
+1 doc node). Detected immediately by the closing hash check; run stopped; the agent's
pre-run byte copy verified (`sha256:85b7fd6d…` recomputed MATCH) and **restored; the restored
artifact re-proved non-destructively** (canonical serialization · 1,345/635 sorted+unique ·
hash law · 0 dangling · schema 1.0.1 — ALL PASS). Delta census of the discarded rebuild:
**exactly one added node, `doc:docs/KNOWLEDGE_GRAPH_CERTIFICATION.md`** — a live confirmation
of the bootstrap-boundary note above (nothing else drifted).

Two lessons recorded, neither a graph/schema defect:
1. **Instrument hazard (routed to Phase 14 as residual R-10):** builder writes ONLY in place
   (`docs/knowledge_graph.json`); the validator's reproducibility check therefore mutates the
   artifact whenever the corpus has drifted since build. Behavior is as documented
   ("READ-ONLY except the reproducibility check") and safe at build time — the hazard is
   post-certification use. Phase 14's first validator extension: temp-path rebuild for the
   repro check. NOT fixed now (owner precondition: modify only on proven contract-level
   inconsistency — this is an operational caveat, and the certified artifact is intact).
2. **Process:** post-certification verification must never invoke the in-place builder;
   read-only recomputation (hash law + serialization + byte-compare against a copy) proves
   the same thing without the hazard.

### Supplemental adversarial verification (U7: supplemental only — main-thread instruments = the certification basis)

Read-only hostile-verifier fan-out re-run after the restore (each verifier independently
reimplements its check from primary sources; repo scripts execution FORBIDDEN): **5/8
returned, 0 refuted** — censuses (node/edge counts per kind + source-enum distribution
{urlconf 528 · feature_index 39 · register:guide 29 · register:chokepoints 5 · manifest 25 ·
register:never_modify 9} + doc split 353md/3json all recompute-exact) · hash (law
reimplemented from builder source; 85b7fd6d recompute MATCH; 1.0.0-substitution reproduces
858a2a6f) · invariants (uniqueness/dangling/routes_to-bijection-with-view-targets/
supersedes-vocabulary/doc-paths-realpath-inside-repo/app-islands all PASS) · determinism-
readonly (canonical form byte-exact; artifact md5 identical before/after audit) ·
residuals (R-5 four ids set-identical · R-6 island counts 298/7/4/62/50 exact · R-7 · R-9
zero archive nodes · version 1.0.1 three-way agreement). **3/8 FAILED on session limit
(schema-conformance · manifest-proof · feature-proof) — disclosed per U7, NOT marked clean
on absence: manifest-proof + feature-proof were already main-thread-proven (§KG-E.2/.3, the
certification basis), and schema-conformance was re-proven MAIN-THREAD post-failure
(schema-file-driven recompute: 0 id-regex offenders over all 8 kinds · 9-value source enum,
0 offenders · the 3 amended ids present + conformant).** One verifier observation adopted as
a wording note: §4 "floors == meta census" refers to `meta.built_from.census` (the input
denominators) — the artifact carries no separate output-census block; counts proven by
recount. Artifact integrity re-confirmed after the fan-out: 618,480 bytes, certified hash
intact.

_Log complete. Sections §KG-0..§KG-F closed append-only 2026-07-13._
