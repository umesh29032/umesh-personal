# P1 — BLOCK 2A REPORT: Foundation Data Model (2026-07-06)

**Status: ✅ BLOCK 2A COMPLETE — STOPPED. Block 2B will NOT start without
explicit owner approval.**

## Scope compliance
Exactly the seven approved entities — **no services, no views, no UI, no
uploads, no geometry processing, no generation, no import/export, no advanced
relationships beyond the spec'd lineage FKs.** The Block-1 "no models" pin was
**consciously replaced** by a Block-2A pin asserting EXACTLY these seven
models (drift-proof); the no-FileField pin still stands (uploads = later block).

## Schema summary (`patterns_ai/models/` — migration `patterns_ai.0001_initial`)

| Model | Grain | Load-bearing schema |
|---|---|---|
| `CalibrationMat` | physical mat registry (ADR-E) | status uncommissioned→active→retired; **CHECK: retired ⇒ reason** (F2); commissioning fields; JSON control_distances (F3 schema_version-in-payload) |
| `PatternPiece` | product-scoped piece identity | FKs INTO production (Product · ProductPattern name-link · optional 1:1 assignment); fabric_group enum; is_pair/on_fold; **UNIQUE(product, pattern)** — the blocker-fix grain; index (product, fabric_group) |
| `PatternPieceVersion` | append-only version chain (ADR-D) | draft→confirmed\|rejected\|superseded; superseded_by self-FK PROTECT; **CHECKs: UNIQUE(piece, version_no) · rejected ⇒ reason · confirmed ⇒ confirmed_by+at** (audit spine) |
| `Marker` | immutable knowledge asset (ADR-D) | `reference` unique MRK- (service-assigned) · **origin enum incl. manual_photo + adda_temporary** (C2/D11) · full status machine · lineage `supersedes` + `benchmarked_against` self-FKs PROTECT (C4/C20) · usable_width_mm + **stamped width_band** (C10) · construction open/tubular · INTEGER ratio JSON (F3) · **CHECKs: adda ⇔ origin=adda_temporary (both directions) · retired/rejected ⇒ reason · width>0**; **resolution index (product, fabric_group, width_band)** |
| `MarkerUsage` | THE feedback join (human act) | FK Marker + FK production.Adda (+optional stage record); plies + **repeats (C7)**; measured width honest-NULL; confirmed_by; **CHECKs: plies≥1 · repeats≥1 · void ⇒ reason**; append-only (void, never delete) |
| `MarkerOutcome` | **RAW FACTS ONLY** (V3 F6) | OneToOne usage; fabric_in_mm/garments_cut/packed/leftover_mm all honest-NULL; quality_flags JSON; facts_schema_version; recorded_by (N-6: explicit human act) — **no derived-metric columns exist, test-asserted** |
| `SuggestionEvent` | product-homed suggestion asset (C8) | source mechanism-id string; payload JSON (F3); offered→accepted\|modified\|rejected; **CHECK: rejected ⇒ reason**; decided_by/at |

Every model: help_text on every meaningful field · verbose_name · Meta ·
enums as TextChoices · append-only rules stated in module/class docstrings ·
FKs INTO production only (string refs), PROTECT throughout.

## Migration summary
`patterns_ai/migrations/0001_initial.py` — 7 CreateModel · 6 indexes ·
**12 CheckConstraints/UniqueConstraints** · applied cleanly to the dev DB;
fully reversible (single additive initial).

## Validation
| Gate | Result |
|---|---|
| patterns_ai suite (purity + pins + smoke + **new Block-2A model tests**: all 12 constraints exercised both directions, lineage PROTECT proven, facts-only asserted) | ✅ OK |
| Full manufacturing suite, serial | ✅ OK |
| `makemigrations --check` | ✅ No changes detected |
| import-linter | ✅ contract 1 KEPT; contract 2 unchanged (zero patterns_ai entries) |

## Findings
1. `usable_width_band` is service-stamped (Block 2B single-writer), not
   DB-computed — Postgres CHECK can't express floor-division portably;
   commented in schema, will be enforced in `marker_service` + tested there.
2. `SuggestionEvent.source` is a mechanism-id string until the
   `GarmentTemplate` model lands in its own block (FK upgrade = additive).
3. `CalibrationMat` recheck LOG (append-only child) belongs to the capture
   block with `CaptureAsset` — registry row ships now so the custody chain has
   its anchor.
4. Tests build rows directly BY DESIGN (no services yet) — the I-1 no-raw-ORM
   rule starts binding production code at Block 2B, stated in the test module
   docstring.

**Awaiting owner approval for Block 2B** (single-writer services: marker_service
[MRK- references, width_band stamping, status transitions with reasons,
usage/void] + marker_feedback_service [outcome facts + derived-at-read math] —
per master plan P1).
