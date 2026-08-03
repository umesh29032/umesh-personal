"""verification.checks — the cited check registry (VER-D4; Phase-13 CERTIFIED).

`dev_world` = the dev-only categories (golden incl. manifest conformance +
shared-assertion re-run; smoke). `production` = the production-safe subset
(production-safety · dev-contamination · integrity). `compose` = verify_all's
environment-aware aggregation. Every check is a pure function over
ORM/settings state returning `report.CheckResult` rows, and EVERY check
carries its certified-invariant citation — an uncited check does not merge.
New invariants are owner/ADR territory, never this package's. 19 check ids
total — the completeness census of record: VERIFICATION_ENGINE_LOG §VER-E.
"""

# Category names (the §6.4 taxonomy; report.CheckResult.category values).
CATEGORIES = (
    "smoke",               # dev modes only — the sole request-cycle territory
    "golden",              # regression byte-match (owner business truth)
    "production-safety",   # flags-vs-declaration · migrations · settings sanity
    "dev-contamination",   # reserved DEV namespace absent from production data
    "integrity",           # self-consistency (Σ-checks, reversal nets, constraint-shaped)
)
