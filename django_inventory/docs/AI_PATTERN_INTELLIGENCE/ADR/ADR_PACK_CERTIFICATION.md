---
id: docs-ai-pattern-intelligence-adr-adr-pack-certification
type: adr
status: active
owner: frozen
scope: architecture
anchors: —
verified: 2026-07-18
---

# ADR PACK CERTIFICATION — Phase 1 (2026-07-06)

> **Scope:** consistency certification of draft ADRs A–H against the three
> governing documents: [MANUFACTURING_V1_FREEZE.md](../MANUFACTURING_V1_FREEZE.md)
> (§7 frozen contracts), [06_BLUEPRINT_V3_FINAL.md](06_BLUEPRINT_V3_FINAL.md)
> (constitution + locks; APPROVED), and
> [AI_PATTERN_INTELLIGENCE_KICKOFF.md](../AI_PATTERN_INTELLIGENCE_KICKOFF.md)
> (§5 frozen contracts, §10 Owner Vision, global rules).
> **ADR status: DRAFT — this certification asserts consistency; owner approval
> of the pack ratifies the ADRs and the D1–D11 finals mapped below.**

## 1. The pack

| ADR | Title | One-line decision |
|---|---|---|
| [A](ADR-A-nesting-engine.md) | Nesting engine & bake-off | engine-agnostic adapters; P0 hostile bake-off (SVGnest-headless / pynest2d / BLF floor); criteria fixed before running |
| [B](ADR-B-background-jobs.md) | Background jobs | Postgres SKIP-LOCKED queue + ONE systemd worker; no Redis/Celery; append-only job history; adoption elsewhere = mini-ADR |
| [C](ADR-C-geometry-format.md) | Canonical geometry format | versioned JSON · integer µm/centi-degrees · polyline-at-tolerance · first-class garment features · grade-rule slot · SVG/DXF-AAMA guarantees · additive-only evolution |
| [D](ADR-D-marker-lifecycle.md) | Marker lifecycle | immutable markers + lineage; 4 origins incl. manual-forever; full status machine w/ reasoned negatives; D11 promotion = confirm pins + status flip |
| [E](ADR-E-calibration-metrology.md) | Calibration & metrology | ChArUco mat + CalibrationMat registry + commissioning; hard per-photo gates; validated (not promised) error tiers; numeric tape acceptance |
| [F](ADR-F-vendoring-isolation.md) | Vendoring & isolation | everything vendored+checksummed; two-runtime isolation (Django never imports torch); no-network test; annual rebuild drill |
| [G](ADR-G-media-lifecycle.md) | Media lifecycle | KNOWLEDGE/REGENERABLE/DEV classes; originals immutable+cold-archived; integrity sweep; declared S3 switch point |
| [H](ADR-H-app-boundary-governance.md) | Boundary & governance | patterns_ai app; FKs into production only; ZERO reverse imports (stricter than machines); proposals-only; RBAC map; D8 execution on approval |

## 2. Consistency matrix

### 2.1 vs MANUFACTURING_V1_FREEZE §7 (ten frozen contracts)

| Frozen contract | Verdict | Where honored |
|---|---|---|
| 1 Money only at settlement / single-writer money services | ✅ | H-6 (no money; ₹ read-only post-GSM; STOP rule cited) |
| 2 Append-only work-that-happened | ✅ | B-4, D-3, E (recheck logs), G-1 |
| 3 Verification confirms/reduces | ✅ | untouched — no ADR nears production verification |
| 4 Frozen snapshots (rates/costs) | ✅ | untouched; same freeze PHILOSOPHY reused (C, D) |
| 5 Manager-assignment rosters / visibility predicate | ✅ | H-5 uses existing skill+role machinery only |
| 6 FK direction (satellites → production) | ✅ | H-1; D (MarkerUsage→Adda) |
| 7 Sidebar+URL co-gating | ✅ | H-5 (SidebarItemRule per URL) |
| 8 Grain monotonicity / pool windows | ✅ | untouched — module never reads/writes pools |
| 9 Enforcement flags OFF until R11 | ✅ | untouched |
| 10 Design system frozen / mobile-first | ✅ | inherited via kickoff §5.4; UI ADRs defer to design-system audit gates (V2 §6 carve) |

### 2.2 vs Blueprint V3 (constitution + locks)

| V3 clause | Verdict | Where |
|---|---|---|
| F1 product-root knowledge graph, no parallel stores | ✅ | C (one canonical format), G (classes, no second store), H (one app) |
| F2 decisions are reasoned immutable events | ✅ | D-3 (reasons on negatives), E-2 (recheck log), B-4 (job history) |
| F3 additive evolution / versioned payloads | ✅ | C-1/C-8, B-1 (payload versions), F (manifest) |
| F4 engine independence | ✅ | A-1, C-6, F (adapters + isolation) |
| F5 deletion policy / full status sets | ✅ | D-3, G-1, B-4 |
| F6 facts stored, metrics derived | ✅ | C companion note; feedback service reads facts (V2 §5/§9 unchanged) |
| Honest-AI vocabulary | ✅ | A (search, not intelligence), E (validated tiers), no ADR adds an AI claim |
| Open-source / offline / no paid APIs / repo-reproducible | ✅ | F (whole ADR), A-alternatives (cloud rejected), B (no new infra) |
| Human confirmation = source of truth | ✅ | E-5, D-4 (promotion = human gate) |
| Manual markers first-class / baselines / confidence | ✅ | D-2 (origins, benchmarked_against); confidence spec untouched (V2 §5) |

### 2.3 vs KICKOFF (frozen contracts §5 · Owner Vision §10 · global rules)

| Item | Verdict | Notes |
|---|---|---|
| §5.1 proposals-only | ✅ | H-3 |
| §5.2 no money | ✅ | H-6 |
| §5.3 human confirmation + immutable confirmed artifacts | ✅ | D, E |
| §5.4 FK/single-writer/RBAC/mobile/docs-sync | ✅ | H-1/4/5 |
| §5.5 frozen modules change only via ADR | ✅ | D2/D3 (GSM, fabric_construction) explicitly routed as owner mini-ADRs on the manufacturing side — no ADR in this pack touches production schema |
| §10 vision items (product-home list · manual markers · promotion · capture doors · confidence · offline) | ✅ | D (origins/promotion), E (capture doors), C (permanent formats), F/G (offline+forever) |
| Global rule 12 (8 qualities) | ✅ | each ADR closes with the V1/V3 respect sections |
| Global rule 11 (contradiction ⇒ STOP) | ✅ | H-7 encodes it as module governance |

## 3. Known, scheduled items (NOT inconsistencies)

1. **ops-master §11 AI-row wording** still carries the pre-blueprint
   "proposing … back into the SAME masters" phrasing. This is the documented
   D8 decision: the amendment **executes upon owner approval of this pack**
   (ADR-H §3). Deliberately not edited during Phase 1 — scope discipline.
2. **Error-tier numbers (ADR-E) and engine choice (ADR-A)** are empirical:
   they become addenda after P0/P2 validation, by design.
3. **D2/D3 manufacturing-side additive fields** (fabric_construction, GSM) are
   routed as separate owner mini-ADRs at P1 — this pack cannot and does not
   authorize production schema changes.

## 4. D1–D11 ratification mapping (owner approval of the pack = these finals)

D1 revisions-as-optional-labels (C9) → ADR-D/C · D2 fabric_construction mini-ADR at P1 → ADR-H §6 note · D3 GSM mini-ADR at P1 → ADR-H §6 · D4 capture/approve = cutting_master, activate/promote = management, ≥2 trained → ADR-H §5 · D5 instruction-diagram v1, plotter after P4 → (V2 §8, unchanged) · D6 office printer + 100 mm ritual → (V2 §8) · D7 mat + mount purchase at P2 → ADR-E · D8 §11 amendment on approval → ADR-H §3 · D9 scaled = draft-only until tape-confirmed → ADR-E/D · D10 local-LLM skipped, slot documented → ADR-F future · D11 temporary-marker promotion mechanics → ADR-D §4.

## 5. CERTIFICATION

Cross-checked ADR-by-ADR against all three governing documents above:
**no contradiction found; no frozen contract touched; no production schema
change authorized; every owner lock and vision item traced to its
implementing ADR.** The three open items in §3 are scheduled decisions, not
conflicts.

**The ADR pack is CERTIFIED INTERNALLY CONSISTENT and consistent with
Manufacturing V1, Blueprint V3, and the Kickoff Contract — ready for owner
approval.**

*Phase 1 ends here. Phase 2 (IMPLEMENTATION_MASTER_PLAN) does not start
without explicit owner approval.*
