> **ARCHIVED 2026-07-13** — 2026-06 production-readiness audit phase; findings closed, superseded by the current frozen architecture ([../../MANUFACTURING_V1_FREEZE.md](../../MANUFACTURING_V1_FREEZE.md)). Kept for history (Phase-7 DOCCLEAN-D). Its own outbound links reflect the 2026-06 tree.

# Phase E — Documentation Alignment

**Method:** cross-checked the money/architecture claims in ARCHITECTURE_V2, the ADRs (0005/0007/0009), CLAUDE.md, START_HERE, PKALS, and the new Production-Truth Foundation docs against **verified code/behavior** from Phases A–D. Evidence-backed mismatches only; no new architecture proposed.

**Scope honesty:** concentrated on the **settlement/costing/production-truth** claims (where drift = financial risk). Navigational docs (START_HERE, PKALS_RELEASE) checked at the claim level, not line-by-line.

---

## Verdict
Documentation is **unusually well-aligned** with the code — ADR-0009 matches the implementation almost line-for-line, and ARCHITECTURE_V2 honestly flags verification as optional. **One real doc-vs-code drift** (variance policy), **one latent default inconsistency**, and **one forward-gap** (foundation not yet referenced). No fabricated/contradictory architecture claims found.

---

## Findings

### MEDIUM

**E-1 — ARCHITECTURE_V2 §5/§6 says variance reduces final payable; the code always absorbs it.** *doc-vs-code drift* · confidence HIGH
- Doc claims:
  - §5 L142: "Compute final payable per worker from **expected vs packed/missing/rejected (variance policy)** minus advance recovery."
  - §6 L155-157: flow `… → packed / missing / rejected / variance → … → FINAL PAYABLE`.
  - §6 L160 example: "expected 100, **final payable 90**, deduct 30 → paid 60" — assumes a 10 variance reduction.
- Code reality: `finalize_adda_settlement` hardcodes `variance_amount = _ZERO`, `variance_total = _ZERO` (factory_absorbs), `final_payable = worker_expected − recovered`; `variance_policy` is **never read** ([adda_settlement_service.py:353-382](config/expense/services/adda_settlement_service.py#L353)). Packed/missing/rejected are recorded as counts but **never reduce pay**.
- So the doc describes a variance-policy-driven payable that isn't implemented (the code side is Phase-B B-3). The L160 example's 100→90 reduction cannot occur today.
- Fix (no new architecture — just truth): update §5/§6 to state "factory_absorbs is the only implemented policy; variance counts are recorded but do not reduce payable; `variance_policy` is reserved for a future deduct policy (see B-3)." Or implement the policy per the B-3 decision. Effort: **S** (doc) / **M** (code, if chosen).

**E-2 — `LEDGER_CREDIT_AT_ALLOCATION` defensive default contradicts the documented settlement-first default.** *latent code/doc drift* · confidence HIGH
- Documented (CLAUDE.md, ADR-0007): settlement-first is the **default**; `LEDGER_CREDIT_AT_ALLOCATION=False`. Settings agree: `base.py:182 default=False`.
- But `allocation_service.py:66` reads `getattr(dj_settings, 'LEDGER_CREDIT_AT_ALLOCATION', True)` — fallback **True** (legacy allocation-era) — while `stage_views.py:979` falls back to **False**. Inconsistent.
- Today harmless (the setting is defined =False, so the fallback never fires), but **latent**: if the setting were ever removed, `allocation_service` would silently revert to allocation-era crediting while the rest of the app assumes settlement-first — a split-brain money path contradicting the documented default.
- Fix: make both getattr fallbacks `False` to match the documented + settings default. Effort: **S**.

### INFO / FORWARD-GAP

**E-3 — TM-1 + ARCHITECTURE_V2 don't yet reference the locked Production-Truth Foundation.** *doc completeness* · confidence HIGH
- REQUIREMENT_REVIEW_STAGE_TRACKING (TM-1) defines C-TM convergence (every capture path → `WorkerStageContribution` via the single-writer chokepoint) — verified accurate against code. But it predates the locked foundation, so it does **not** mention allocation-bounded reporting, good/alter/missing, or Adda-rate snapshots — yet the locked decision makes the **foundation a prerequisite of TM-1**.
- Not a contradiction (the chokepoint claim is still true) — a **completeness gap**. Per DOCS-SYNC: when the foundation is built, cross-link ARCHITECTURE_V2 §11 + REQUIREMENT_REVIEW_STAGE_TRACKING → the foundation docs, and note TM-1's dependency on the allocation layer. Flag now; update at build (not in this review-only phase).

### Adjacent (state, not doc-claim)
- **Unapplied migration `tracking 0014`** (Phase-A E1) is a local-DB *state* drift, not a documentation mismatch — but it means the running instance differs from the migrated schema head. Resolve before staging.

---

## Verified ALIGNED (no drift — positive)

- **ADR-0009 cost-truth ↔ code: exact match.** Standard cost (`processing_cost`, `ws.cost_rate`, handler qty, frozen at advance) vs actual pay (settled earnings, role-aware `expected_rate`, reported/verified qty, SWA+ledger at settlement); "NEVER additive." The costing UI even cites ADR-0009 inline. **And ADR-0009 explicitly names "standard-vs-actual labor = a future VARIANCE report"** — i.e. it *anticipates* the B-1/B-2 divergence (actual 360 > standard 315) as its declared home. Strong alignment.
- **ARCHITECTURE_V2 is honest about verification:** "Manager review/verification — OPTIONAL today… does NOT gate advancement" (L113). So Phase-B B-1 is a *business-risk* finding, **not** a doc lie — the doc tells the truth about the gap.
- **ADR-0005 Option B ↔ code:** reported locked after submit; verified manager-only; expected_earning frozen at complete = visibility; no ledger until settlement. Matches.
- **CLAUDE.md migration claim accurate:** "V2-1d… migration 0035" = `0035_drop_worker_m2m.py`. ✓
- **SWA transitional-retained** as the settlement earning line (§11.4) — matches (`StageWorkAssignment` created at finalize). ✓
- **Settlement-first default** (`LEDGER_CREDIT_AT_ALLOCATION=False`) present in settings — matches (modulo E-2 fallback).
- **New foundation docs are consistent with ARCHITECTURE_V2** — they *extend* Option B / settlement-first (allocation + good/alter/missing + Adda-rate snapshots), they do not contradict it.

---

## Net Phase E
Docs are a strength here — the costing/cost-truth and Option-B claims match the code, and the architecture honestly flags its own optional-verification gap. Only **E-1 (variance-policy doc overstates the implementation)** needs a doc correction before staging (pairs with the B-3 decision); **E-2** is a one-line code-default alignment; **E-3** is a build-time cross-link obligation. No misleading architecture claims that would trap a new developer.
