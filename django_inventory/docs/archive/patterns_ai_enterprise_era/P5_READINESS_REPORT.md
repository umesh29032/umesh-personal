# P5 READINESS REPORT — Factory Integration & Production Readiness entry
check (2026-07-07)

**Verification only. P5 is NOT started.**

## Verdict: **READY — no architectural blockers.** The platform is
feature-complete for its four eras (memory · geometry · generation ·
assistant); P5 is integration, hardening and rollout — not invention.

## 1. What P5 stands on (all frozen, tested, browser-proven)
- Complete knowledge chain: capture → geometry → marker (manual +
  generated) → usage → outcome → yield → advice → recorded human
  decision. Every link append-only, every metric derived at read.
- The Advisor gives factory-facing value from day one of rollout and
  improves automatically as outcomes accumulate (re-derivation learning).
- Isolated compute runtime with pinned lockfile + vendored engines +
  artifact manifest — deployable by the ADR-F rebuild recipe.
- 166 app tests + full-suite integration inside the manufacturing ERP's
  own gates; walls make constitution violations mechanical failures.

## 2. P5's natural scope (the master plan's integration era)
1. **Workflow integration:** advisor/marker surfaces at the REAL
   decision points (Adda cut-planning page links, marker pick recorded
   against the Adda) — touching production UI = the first time
   patterns_ai renders inside manufacturing pages; needs its own
   boundary care (read-only embeds, no reverse imports — ADR-H).
2. **Operational readiness:** deploy runbook entries (compute venv build,
   node runtime, media/integrity crons, ADR-F annual rebuild drill),
   backup story for `media/patterns_ai/`, monitoring of the sweep.
3. **Physical validation (D7):** the REAL printed mat → ADR-E addendum
   tiers on the factory table → trust-grade policy goes live.
4. **Rollout policy:** who gets the sidebar entries, worker-facing
   visibility rules, the enforcement-flag posture (unchanged: OFF until
   R11 — manufacturing stream, orthogonal).
5. **Suggestion-outcome reporting:** acceptance vs later reality — the
   spine data exists from P4.

## 3. Known risks going into P5
| Risk | Standing answer |
|---|---|
| Production-page embedding erodes the app boundary | ADR-H: production never imports patterns_ai — embeds must be links/includes rendered BY patterns_ai URLs; wall test already enforces the import direction |
| Real-mat tiers miss the synthetic promise | ADR-E ritual: publish measured tiers as the addendum; gates already parameterized |
| Rollout data quality (garbage outcomes) | void-with-reason + honest-n already absorb noise; training the humans = runbook item |
| Ops drift (venv/node missing after a reprovision) | runtime_available() honest failures + lockfile rebuild recipe + the annual drill |

## 4. Entry criteria for P5 kickoff
1. **Owner approval** of the P4 package + freeze.
2. **Owner checkpoint commit** (standing discipline; four eras now sit
   uncommitted in the working tree).
3. **D7 purchase** (printed mat + phone mount) scheduled — P5's physical
   validation depends on the artifact existing.
4. **Owner's integration priorities:** which production surface links to
   the Advisor first (Adda cut-planning is the natural candidate).

**STOPPED. No P5 work begins without the owner's explicit go.**
