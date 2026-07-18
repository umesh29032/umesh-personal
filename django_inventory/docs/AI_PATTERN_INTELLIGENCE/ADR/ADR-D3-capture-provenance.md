---
id: docs-ai-pattern-intelligence-adr-adr-d3-capture-provenance
type: adr
status: active
owner: frozen
scope: architecture
anchors: —
verified: 2026-07-18
---

# ADR-D3 — Capture Provenance Depth (P2 entry decision)

**Status: DECIDED 2026-07-07 (Phase 2 entry; slot reserved by the master
plan as "D3 mini-ADR"). Owner reviews with the P2 package.**

## Problem
How much device/context provenance is recorded per capture, and where?
Too little ⇒ ADR-E's "recall every capture made on the stretched mat /
that phone" query is impossible. Too much ⇒ a device-profiling subsystem
nobody consumes.

## Decision
1. **No new provenance tables in P2.** Provenance = versioned JSON payloads
   in structures that already exist (F3 additive evolution):
   - `CaptureAsset.metadata` payload v2 (additive keys, schema_version
     bump): `exif` subset — camera make/model/software, capture datetime,
     orientation, focal length, pixel dimensions — read at upload via PIL
     (metadata extraction, explicitly NOT CV; the rendition-only PIL rule
     gains this one documented sibling use) + free-text
     `device_profile` (e.g. "poco-x3 · stock camera · photo mode").
   - `GeometryExtraction.result/gate` payloads: raw marker detections,
     homography matrix, per-corner residuals, tilt estimate, mat
     self-check deltas, `pipeline_version`, backend + params — the FULL
     reprocessing record ADR-E §6 requires. Originals are immutable, so a
     better future pipeline re-derives NEW drafts from the same asset.
2. **Custody chain stays relational where it must be queryable:**
   `CaptureAsset.mat` (exists since 3A) + `GeometryExtraction.capture` +
   `PieceSizeGeometry.source_extraction` — "every dimension traces to
   mat + photo + residuals + confirmer" is pure FK walking.
3. **Mat lifecycle evidence = `CalibrationMatCheck`** (append-only child
   the mats model reserved since 2A): commissioning + recheck rows with
   measured deltas, pass/fail, actor. This is a decision-event table
   (F2), not device profiling.
4. **EXIF is evidence, never authority:** gates (ADR-E §3) run on detected
   board geometry only; EXIF absence never blocks a capture; EXIF values
   are never used in measurement math.

## Alternatives considered
- **DeviceProfile registry table** — rejected for P2: no consumer exists;
  free-text + EXIF answers the recall query; a registry can be derived
  from stored payloads later WITHOUT data loss (additive promotion).
- **Full EXIF dump** — rejected: privacy/noise (GPS etc.); the subset is
  fixed, documented, and sufficient.
- **No EXIF at all** — rejected: "which phone produced the drifted
  captures" is a real ADR-E recall scenario.

## Consequences
Zero schema weight for profiling; complete reprocessing provenance;
promotion path to a registry stays open (F3). The one-page payload spec
lives in the geometry pipeline doc.
