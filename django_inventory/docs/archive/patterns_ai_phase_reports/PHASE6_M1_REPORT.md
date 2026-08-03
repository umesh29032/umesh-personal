> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# Phase 6 · M1 REPORT — BLF internal timebox (2026-07-07)

**Status: ✅ M1 COMPLETE — STOPPED. M2 will not start without approval.**

## Implementation summary
The grid-BLF placement pass now carries an **internal deadline** (checked
every 64 scan rows — negligible overhead) in BOTH paths:
- **Generation BLF** (`run_blf`): deadline = the job's timebox; expiry
  returns the honest error *"the Quick method ran out of time on this
  layout — use the Thorough method for large mixes, or reduce the piece
  count."* — recorded per-engine in `run.errors`, exactly like a
  width-refusal.
- **Optimize op** (`_place_free`): the pass returns a `timeout` sentinel;
  the orderings loop stops, the give-up is counted in
  `dropped['timeout']`, and a zero-option run returns the same honest
  message. Small sets behave identically (timeout counter 0).

No API change, no vendored code touched, no Django change. Determinism
on sets that finish in time is unaffected (byte-equality re-pinned).

## Changed files
- `compute/patterns_ai/nest.py` (only file, per plan).
- `config/patterns_ai/tests/test_phase6_m1.py` — NEW (5 tests).

## Test results
- **M1 suite 5/5**: 60-piece generation gives up honestly well inside
  the bridge window (elapsed < 30 s, message asserted) · same set
  succeeds with a small count + generous box · **small-set full-placement
  byte-determinism unchanged** · optimize op inherits the give-up
  (timeout counter ≥ 1, honest error) · small optimize sets unaffected
  (timeout counter 0, options verified).
- Prior Phase-5 engine suite (13) re-ran green alongside — 18/18.
- Full app + serial battery: fresh run (counts below).

## CLI smoke (the original F1 case)
The 66-piece DEV-TEE-shaped mix with a 2 s box: **`ok False · errors:
{'blf': 'the Quick method ran out of time…'}` in ~2 s** — previously this
hung until the bridge killed it at 115 s.

## Browser behavior
None (engine-level milestone, as planned) — the honest message will
surface through the existing generation/optimize error paths untouched.

## Regression
patterns_ai **230/230 OK** (225 + 5 M1) · full manufacturing suite **1115/1115 OK** (serial, fresh) ·
`makemigrations --check` clean (no schema this milestone) · import
contracts unchanged.

**STOPPED — awaiting approval for M2 (the one migration).**
