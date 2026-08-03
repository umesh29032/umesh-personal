> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# M8 — Real Pattern Capture · report
(2026-07-10 · opened with the approved M8 readiness · owner-frozen
capture workflow implemented as approved)

**The headline: the platform now holds its FIRST REAL FACTORY
GEOMETRY.** Your actual cardboard Body photo (plain table, no mat,
tape beside the piece) went Evidence → Build → Review → Publish and is
now the confirmed design: **Nickar Body · M = v2, trust "Measured
(tape-accepted)", 36-vertex real outline**, live in the Digital
Cutting Table payload with its capabilities intact. v1 (synthetic)
superseded; S carried forward untouched.

**What shipped (exactly the approved scope):**
- `photo_plain` evidence kind (migration 0017, choices-only). Plain
  photos JOIN the set silently — no per-item adapter. Each item carries
  its own `view` label (top_full/folded/closeup/edge/corner/reference/
  other) and its own tape `measurements` (any name → mm; your rule:
  measurements belong to individual evidence items).
- **Build Geometry From Evidence** (the Evidence-SET adapter): you pick
  the PRIMARY photo; the set's merged measurements supply scale —
  width + height tape numbers are the per-axis truth, the outline lands
  on them exactly. Every other stated number becomes a recorded
  cross-check: derived where the outline can answer (diagonal), listed
  stated-only where it can't (waist etc.). Advisory always — shown in
  the inspector, never a silent gate.
- New compute tool `extract_plain.py` (isolated runtime): Otsu
  dark-object segmentation for the real factory photo. The mat
  pipeline's segmenter FALSE-PASSED on your photos (grabbed the whole
  frame — caught by drawing the mask over the image, not by the numbers).
  The new ladder was validated on all 20 of your Body photos first.
- Honest gates in the UI: your top_view photo was REFUSED with
  "piece touches the photo edge — retake with background margin all
  around (keep the tape BESIDE the piece, never across it)". Recorded
  on the evidence row, exactly like every other adapter refusal.
- Trust law needed zero new code: no mat ⇒ proposal accepts as
  UNCALIBRATED; your matching tape at publish upgraded M to MEASURED —
  the one path that already existed.

**Proof:** tests 15/15 (`test_m8_capture.py`: intake/params/refusals ·
set merge primary-wins · cross-check deltas · trust law · UI actions ·
real-runtime exact-scale) · patterns_ai suite **514/514** · full serial
battery **1399/1399** · browser on DEV-NICKAR with the REAL photos
(screenshots m8_b1..b6: stack chips → proposal + cross-checks
(diagonal Δ 3.5 mm) → publish → refusal → real outline in DCT).

**Photo guidance for the next capture session** (from what the gates
taught us): plain contrasting table · margin on all four sides · tape
BESIDE the piece, never across it · one full top view per piece×size =
the primary; close-ups/folded views join the same stack as context +
measurement carriers. The numbers I used (350×510×615) are DEV
placeholders — re-state your real tape numbers and rebuild whenever
you're ready; rebuilding is one click on the same stack.

**One observation (pre-existing, NOT changed — your call):** accepting
a proposal on an already-published piece opens a BARE draft holding
only that size; the copy-forward path is pressing "Reopen in Studio"
FIRST. If someone publishes a bare draft, the other sizes drop out of
the current confirmed version (they stay in history). Worth a small
guard or auto-copy-forward later — flagging, not fixing.

**Out of scope (as declared):** Gemini/AI adapter (the set is now
shaped for it — a future adapter reads the SAME stack) · multi-photo
fusion · video evidence · mat retirement (the mat path stays, it's the
higher-trust ladder rung).

**STOPPED — M8 complete, awaiting review.**
