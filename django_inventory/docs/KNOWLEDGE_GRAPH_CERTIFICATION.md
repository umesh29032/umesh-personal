---
id: knowledge-graph-certification
type: evidence-cert
status: active
owner: append-only
scope: all — the Phase-8 Knowledge Graph certification package
anchors: docs/KNOWLEDGE_GRAPH_BUILD_LOG.md, docs/knowledge_graph.json, docs/knowledge_graph.schema.json
verified: 2026-07-13
---

# KNOWLEDGE GRAPH CERTIFICATION — Phase 8 (permanent, citable)

> **The one artifact later phases cite instead of reopening the build log.** Created at the
> Phase-8 close (2026-07-13) per owner directive. Every figure traces to
> [KNOWLEDGE_GRAPH_BUILD_LOG.md](KNOWLEDGE_GRAPH_BUILD_LOG.md) §KG-0..§KG-F or to the
> validator/proof scripts named inline. Phase 9 consumes the graph ONLY through the schema +
> §6/§7 of this certification; Phase 14 extends the validator, never forks it; neither
> re-derives what this document already proves.

---

## 1. What is certified

`docs/knowledge_graph.json` is certified as **the authoritative Phase-8 output: the single
machine-readable source FOR GENERATED DOCUMENTATION** — never project truth. Code and the
T0/T1 truth-lock documents remain the territory; the graph is the map. Fix-at-source law
stands: a wrong graph is never edited by hand (the content-hash guard makes hand-edits
detectable and refusable); the source is fixed and the graph rebuilt.

| Item | Certified value |
|---|---|
| Graph artifact | `docs/knowledge_graph.json` (`generated` ownership class) |
| Schema | `docs/knowledge_graph.schema.json` — **v1.0.1** (draft-07; 1.0.0 → 1.0.1 = KG-D validator-proven widening-only amendment, dated in the Phase-8 contract) |
| Content hash | `sha256:85b7fd6d52041e4a529e68d231df01ae6ee09497e1d60eb2a7a89bdf34578fad` |
| Builder | `scripts/build_knowledge_graph.py` (stdlib + Django introspection; reads schema version from the schema file; id-collision = hard failure; loud-absence report on stderr) |
| Validator | `scripts/validate_knowledge_graph.py` (schema-DRIVEN independent verifier; INV-1..8; floors by independent recount; hash recompute; builder re-run byte-compare) |
| Battery | NEVER ran in Phase 8 (KG-D9: scripts/ outside the test surface); baseline 1530/1530 stands untouched |

## 2. Node census (1,345 nodes — floors exact)

| Kind | Count | Natural key | Source instrument |
|---|---|---|---|
| app | 10 | `app:<label>` | Django apps registry |
| url | 528 | `url:<ns:name \| name \| _unnamed:slug>` | root-URLConf recursive walk (482 named + 46 unnamed) |
| view | 267 | `view:<qualname>` | 229 project + 38 `vendor:true` (floors bind project ≥229) |
| service | 57 | `service:<app>.<module>` | `config/*/services/` file census (`_shared` helpers excluded, documented) |
| model | 88 | `model:<app>.<Model>` | apps registry `get_models()` (0 proxies; core/inventory 0 by design) |
| doc | 356 | `doc:<path>` | ACTIVE-tree walk (docs/** minus `docs/archive/**`, minus the graph ITSELF) + root docs + app READMEs; 353 md + 3 json incl. the schema |
| adr | 11 | `adr:<NNNN>` | `docs/adr/` census (0001–0011 contiguous) |
| feature | 28 | `feature:<slug>` | FEATURE_INDEX.md row parse (28/28 slugs unique) |

## 3. Edge census (635 edges — every edge carries a certified `source` enum value)

| Kind | Count | Source | Absent kinds (loud, classified — never inferred) |
|---|---|---|---|
| routes_to | 528 | urlconf | `calls` = 0 (no certified view→service register at that grain) |
| belongs_to_feature | 39 | feature_index (exact-token only) | `gated_by` = 0 (no gate-census artifact; RBAC truth stays in code) |
| documented_by | 34 | filename-rule registers | `supersedes` = 0 (no ACTIVE-tree doc carries a strict single-successor banner) |
| cites | 25 | canonical_manifest topics | |
| writes | 9 | never_modify register / ADR-0002 | |

The mandatory per-edge `source` enum (9 certified values) makes inferred, guessed, or
runtime-traced edges **shape-invalid by construction**.

## 4. Proof summary (all recorded in full in the build log)

| Proof | Result | Where |
|---|---|---|
| Determinism | Double-build byte-identical (KG-C); independent builder re-run byte-identical (KG-D); zero wall-clock timestamps in body; canonical serialization (sorted keys/nodes/edges, UTF-8, trailing newline) | §KG-C.5, §KG-D.4 |
| Validation | Independent schema-driven validator: shape over 1,345 nodes + 635 edges (0 offenders), INV-1..8 ALL PASS, exit 0 | §KG-D.4 |
| Content hash | Independent recompute matches stored (hand-edit guard armed). **Hash-delta byte-proof:** substituting `"1.0.0"` into the 1.0.1 artifact reproduces the KG-C digest `sha256:858a2a6f…` exactly → the 1.0.1 amendment changed ZERO node/edge bytes | §KG-D.3 |
| Completeness | INV-8 floors by independent recount (fresh URLConf walk, apps registry, file globs): all 8 kinds — recount == node count == meta census | §KG-D.4 |
| Consistency (KG-E) | Graph ⊇ manifest: 25/25 canonical + all also[] file paths resolve; **cites edges recomputed from the manifest == graph 25/25 exactly**; entry paths + 7/7 chokepoint services resolve. Graph ⊇ FEATURE_INDEX: 28 rows ↔ 28 nodes (set-equal); 39 belongs_to_feature edges valid; the 4 zero-edge features == exactly the KG-C classified unparsable rows. Graph vs DOCUMENTATION_INDEX: 114/114 active-tree linked paths → nodes; 0 lifecycle contradictions | §KG-E |
| KG-D defect handling | 1 genuine contract-level defect (KG-B regexes narrower than the natural-key law; 3 real ids) — stopped, classified, dated amendment, widening-only patch, full re-validation | §KG-D.2 |

## 5. Residual register (routed, none blocks Phase 9)

| # | Residual | Class | Routed to |
|---|---|---|---|
| R-1 | `calls` edges = 0 — no certified view→service register | absent-by-evidence | future instrument (additive-minor lane); Phase-9 cards omit the row |
| R-2 | `gated_by` edges = 0 — no gate-census artifact | absent-by-evidence | future instrument; Phase-14 candidate |
| R-3 | `supersedes` edges = 0 — no strict single-successor banner in ACTIVE tree (RAW_MATERIALS 2-pointer = valid INFO per INV-4c edges-not-lifecycle, KG-D confirmed) | absent-by-evidence | Phase-9/14 as supersession banners appear |
| R-4 | `ledger_and_payment.md` chokepoint page — filename-rule miss (matches no service module); manifest cites lane still routes to it | absent-not-guessed | explicit mapping candidate at GEN-0 |
| R-5 | 4 FEATURE_INDEX rows unparsable (no exact-token url/model cells): settlement-reverse-supersede · leftover-consume · public-homepage · pattern-layout-tool — nodes exist, 0 edges | absent-not-guessed | Phase-9 feature-doc authoring input |
| R-6 | 298 doc islands (docs with zero edges) + permitted islands adr 7 · feature 4 · model 62 · service 50 | orphan-signal, non-fatal | Phase-9 card/`documented_by` authoring = the designed resolution |
| R-7 | `meta.built_from.git_head: "unknown"` — repo root is the parent dir, builder's `.git/HEAD` probe never resolves; deterministic; identical in the KG-C artifact | INFO provenance | optional 1-line builder improvement, owner-gated minor |
| R-8 | manifest topic-13 also[] entry `docs/LEARNING_2_0/APPS/` is a DIRECTORY pointer — no node by design (doc kind = files); no cites edge on either side (proof + builder agree) | representation boundary | GEN-0 Design Record: manifest-view generator carries it as prose/dir-listing |
| R-9 | DOCUMENTATION_INDEX links 1 archive path (`docs/archive/audits/DOC_AUDIT_2026_06_12.md`) — graph boundary excludes `docs/archive/**` BY DESIGN; the index row itself labels it archived = agreement | boundary-exempt | none (recorded) |
| R-10 | Validator's reproducibility check rebuilds IN PLACE (builder writes only `docs/knowledge_graph.json`) — safe at build time, mutates the artifact if the corpus drifted since build (incident + byte-identical restore disclosed in build log §KG-F dated correction) | instrument hazard | Phase-14 first validator extension: temp-path repro; post-cert verification = read-only recompute only |

## 6. Additive-minor future register (nothing from KOS_TARGET_VISION forgotten)

The 12-row register lives in the build log §KG-0: every vision concept (templates, forms,
transactions, permissions, workflows, FK-grain relations, calculations, business rules,
domain kind, journeys, cert-evidence, component nodes) is mapped to its v1 representation →
future node/edge kind → promotion prerequisite. Additive = **minor** version; breaking =
major + owner + same-change consumer update. AI-context and learning-notes remain R7 prose —
never graph kinds. Consumers pin the **major** version.

## 7. Downstream compatibility

**Phase 9 (Documentation Generation) — READY.** Consumes the graph ONLY through schema
v1 (pin major). Generator input spec: url-cards ← `url` nodes + `routes_to` (+ absent-kind
rows omitted, R-1); feature docs ← `feature` nodes + `belongs_to_feature` (R-5 rows =
authoring input); index tables ← kind censuses; **manifest-view ← the 25-row mapping table
in build log §KG-E** (topic → match[] terms → canonical node → cites edges → also nodes;
R-8 directory pointer carried as prose). GEN-D battery-bearing conversion unchanged.

**Phase 14 (Knowledge Sync) — READY.** Extends `scripts/validate_knowledge_graph.py`,
never forks it. Continuous re-checks = INV-1..8 + floors. Drift taxonomy per edge kind via
the `source` enum: urlconf-sourced drift = code-side change; register-sourced
(feature_index/manifest/never_modify) = doc-side change; `content_hash` mismatch vs rebuild
= graph-stale. The graph CI-guard is Phase 14's hook (KG-D9 held — pulling it forward was
never invoked).

**Phase 18 (Future Feature Docs) — READY.** New features enter as FEATURE_INDEX rows →
feature nodes on rebuild (additive-minor). The permanent PHASE_18 protocol needs no schema
change; new knowledge kinds route through §6's register.

## 8. Architectural assessment (owner questions, answered)

**Is the Knowledge Graph now a stable production foundation?** Yes. It is deterministic
(byte-identical rebuilds proven twice, no timestamps), schema-bound (every node/edge
shape-validated, provenance-enumerated), invariant-certified (8 fatal invariants, floors =
independent recounts), and tamper-evident (content-hash guard). Because it owns nothing —
truth stays at the sources — any future defect is a rebuild, never a data repair.

**Can Phases 9, 14 and 18 safely build on it without revisiting Phase 8?** Yes. Each
consumes through a documented interface (§7): Phase 9 through the schema + mapping table,
Phase 14 through the validator + source-enum drift taxonomy, Phase 18 through the
FEATURE_INDEX seed lane. The DOCDISC-F verdict (v1 kinds SUFFICIENT for the 5 knowledge
strata) plus the additive-minor register (§6) mean growth is versioned extension, not
rework.

**Are there any remaining technical risks that would justify reopening Phase 8?** No
contract-level ones. Honest non-reopening risks, all mitigated: (1) graph staleness between
rebuilds — Phase 14's purpose, `content_hash` is the staleness primitive; (2) edge coverage
is only as good as the certified registers (R-1..R-5) — the loud-absence discipline keeps
this visible instead of silently wrong; (3) 298 doc islands are a coverage statement, not a
defect — Phase 9 is the designed fill; (4) git_head provenance gap (R-7) — cosmetic.

## 9. PHASE 8 VERDICT

**PHASE 8 COMPLETE — KNOWLEDGE GRAPH CERTIFIED as the authoritative Phase-8 output.**
Every census row accounted; zero open divergences (2 KG-E findings classified as
representation-boundary, routed to GEN-0); zero hand-edits; zero corpus mutations; battery
never ran (1530/1530 stands); git HEAD `49404001`, 0 staged, working tree = the product (U2).

Tool-death declaration: if builder/validator/scripts are ever lost, consumers fall back to
the handwritten docs + code — the graph is disposable and regenerable; nothing irreplaceable
lives in it.

Bootstrap boundary (disclosed): this certification and its index rows post-date the certified
build and are not nodes in it — by design (rebuilding to include them would change the hash
this document cites). First Phase-14 sync or owner-ordered rebuild absorbs them as ordinary
doc nodes.

**Phase 9 (Documentation Generation) is CLEARED to begin, owner-gated at GEN-0.**

## Dated amendment — 2026-07-17 (owner disposition of incident KS-C-I1, Phase 14)

**The certified baseline hash changes** (owner ruling, verbatim: "I choose OPTION (a).
Record a dated Phase-8 certification amendment accepting the deterministic rebuilt
knowledge graph as the new certified baseline."):

- **Old certified hash:** `sha256:85b7fd6d…` (the 2026-07-16 build this document originally
  cited). Its bytes were OVERWRITTEN in place on 2026-07-17 by the validator's
  reproducibility subprocess — the R-10 hazard, fired under the first Phase-14 KS-C sweep
  (full incident record: KNOWLEDGE_SYNC_LOG §KS-C-I1). No copy of the old bytes exists
  (the artifact was untracked; backups predate Phase 8).
- **New certified baseline:**
  `sha256:203547859d6561316de21b2e3e1fb05e1de70fef440e36e89ac461922f7dd372` —
  a DETERMINISTIC in-place rebuild of the 2026-07-17 tree (census: 12 apps incl.
  devseed+verification · 925 docs · 528 urls · 88 models · 57 services · 28 features ·
  11 adrs; internally valid: self-hash ✓ schema ✓; the Phase-14 write-free dry-run
  reproduces it byte-identically).
- **Scope (owner ruling):** this amendment changes ONLY the graph certification baseline —
  no contracts, no detector behavior, no reporting semantics. **The 558 generated outputs
  remain stamped `graph:85b7fd6d5204` and their `d4.stale` findings remain the HONEST
  EXPECTED STATE until the future regeneration phase (regeneration explicitly NOT performed
  at KS-D).**
- The bootstrap-boundary note above now also covers this amendment (post-dates the build).
