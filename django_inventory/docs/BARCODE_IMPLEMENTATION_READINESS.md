---
id: docs-barcode-implementation-readiness
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# BARCODE IMPLEMENTATION READINESS — append generation for late lanes
(2026-07-11 · one page · the ONLY implementation item justified by
BARCODE_ARCHITECTURE_REVIEW.md · gated on owner approval)

**Real factory problem.** A post-join Cutting Stream (recut after
checking failures · fabric-shortfall second lay · added production —
all owner-named) produces pieces that the frozen lifecycle promises
will "append to the ops pool" — but barcode generation is one-shot per
Adda: `generate_for_adda` / `generate_for_cutting` refuse when any
batch exists. Recut pieces would flow with NO identity; tracking,
damage marking and dispatch checks go blind exactly on the pieces most
likely to need them.

**Why it matters.** Breaks the lifecycle promise the owner froze;
recuts are routine floor reality, not an edge case.

**Ownership.** ERP generation moment (production barcode stage /
join-inline) + Tracking identity rows. Pattern Intelligence: untouched.

**Smallest implementation.**
1. `generate_for_adda` gains APPEND mode: cover only breakdown rows
   not yet covered by existing batches (coverage = per cutting-record
   comparison), new `BarcodeBatch` rows starting at
   `Max(end_seq)+1` for the Adda — sequence continuous, append-only,
   never renumbered; existing batches and printed stickers untouched.
2. The one-shot guard becomes "nothing new to cover" (refusal message
   says so honestly) instead of "batches exist".
3. Barcode STAGE console: when uncovered lane output exists post-join,
   the Generate button reads "Generate N barcodes for the new lane" —
   same one-shot-per-lane semantics.
4. Export manifest regeneration already includes new batches (no
   change — idempotent by construction).

**Explicitly NOT done (YAGNI, rejected in review):** value format
changes · encoding dimensions · mandatory stage scanning · per-bundle
identity · global sequences.

**Browser journey.** On a copy-shaped world: two-lane Adda joined with
sequence 1–60 → open a sequence-2 recut lane (or simulate its cut) →
barcode stage shows "12 new pieces uncovered" → generate → new batch
61–72 with the recut lane's size/color → scan `…-0065` resolves the
correct dimensions → export manifest shows both ranges.

**Tests.** Append coverage math (uncovered rows only) · sequence
continuation Max+1 · double-append refusal ("nothing new to cover") ·
legacy one-shot behavior identical when nothing new exists · scan
resolve across old+new ranges · export regeneration includes both.

**Out of scope.** Everything in the review's rejected list · the
"Add lane" button itself (separate lifecycle §10 item — this readiness
only guarantees barcodes WHEN such a lane exists).

**STOP — awaiting owner approval before implementation.**
