> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# M8.1 — Bare-Draft Safety · report
(2026-07-10 · workflow safety improvement per owner order; opened with
M8_1_DRAFT_SAFETY_READINESS.md — the 5 questions answered there with
code evidence)

**The verdict first:** the bare draft was a leftover, not a design.
`get_or_create_draft` predates versioning-on-published-pieces (built
for the empty-v1 creation flow); copy-forward lived only behind the
explicit "Reopen in Studio" button, so accept-first (and the legacy
DXF import) bypassed ADR-D2 §3. No legitimate workflow wants a
published piece's other sizes silently dropped — size retirement goes
through the ProductSize archive, never omission.

**What changed (`pattern_geometry_service.py` only — zero models/
migrations/UI/ERP):**
1. **Prevention** — `get_or_create_draft` now copy-forwards the latest
   confirmed version's rows into every NEW draft (shared
   `_copy_forward_rows`, same provenance: `copied_from`, original
   contract, trust carried). New pieces still start bare v1; open
   drafts still reused. Every current and future draft-creating path
   inherits this. "Reopen in Studio" stays as the explicit act, now on
   the same one copy routine.
2. **Replace-not-duplicate** — `import_dxf` gained the same replace
   branch `accept_extraction` already had (a carried copy of the target
   size is re-captured in place; its pre-check still refuses real
   double-imports on open drafts).
3. **Backstop** — `confirm_version` refuses to publish a draft missing
   an ACTIVE size the current confirmed version covers, with the fix
   named: "confirming would drop size(s) S currently published on v1 —
   carry them forward (Reopen in Studio copies every size) or archive
   the size first." Unreachable in normal flows now; guards exotic and
   future paths forever. Archived sizes exempt — deliberate retirement
   stays possible.

**Proof:** `test_draft_safety.py` 9/9 (accept-on-published carries all
sizes then replaces the target · contract/trust carried · fresh piece
bare v1 · draft reuse no-dup · DXF path carries · Reopen semantics
preserved · backstop refuses naming the size · archived-size exempt ·
full loop v1→accept→v2 both sizes) · patterns_ai suite **523/523** ·
full serial battery **1408/1408** · browser on a throwaway OPTIONAL
"DEV Guard" piece (real pieces untouched): published v1 (S+M) →
accepted a new proposal on M → draft v2 showed BOTH sizes (S carried
300×200 · M replaced 340×190) → published v2 → DB: v2 confirmed S+M,
v1 superseded (screenshot m81_b1_carried.png).

**Out of scope (as declared):** draft-row deletion UI · version
diff/restore · publish semantics beyond the guard.

**STOPPED — M8.1 complete. Foundation considered finished; next work
arrives only from real factory requirements.**
