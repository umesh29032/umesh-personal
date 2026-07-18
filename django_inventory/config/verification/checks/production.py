"""verification.checks.production — the production-safe subset (VER-C, VER-D3).

STRICTLY SELECT/aggregate + settings/migration introspection: no request
cycle, no sessions, no logins, no writes of any kind. Every check is bounded
(COUNT/SUM aggregates — noted per check) and cites its certified invariant
(VER-D4). Integrity checks encode SELF-CONSISTENCY predicates, never
point-in-time constants (the MGT-C lesson). A red check returns a FINDING —
it never fixes (the campaign routing owns findings).

The `_plan`/`_violators` injection parameters exist ONLY for constructed-fail
tests (a live migration mismatch / DB-constraint breach cannot be fabricated
in a battery DB — the DB itself refuses); production callers never pass them.
"""

from django.db.models import F, Q, Sum

from verification.report import CheckResult


def _r(check_id, citation, category, ok, measured):
    return CheckResult(id=check_id, citation=citation, category=category,
                       status="pass" if ok else "fail", measured=measured)


# ── dev-contamination (spec §4 / DATA-D8) ────────────────────────────────────

# Identifier-bearing columns × the reserved DEV namespace (spec §4 schemes).
# Cost: one COUNT per row — bounded aggregates.
DEV_NAMESPACE_SCAN = (
    ("accounts.User", "email", ("dev.",), ("@test.local",)),
    ("production.Product", "code", ("DEV-",), ()),
    ("production.Adda", "code", ("DEV-",), ()),
    ("production.Stage", "code", ("dev-",), ()),
    ("raw_materials.ClothType", "name", ("DEV-",), ()),
    ("raw_materials.ClothColor", "name", ("DEV-",), ()),
    ("raw_materials.StorageLocation", "name", ("DEV-",), ()),
    ("machines.Machine", "code", ("DEV-",), ()),
    ("storefront.Category", "name", ("DEV-",), ()),
    ("storefront.FeaturedProduct", "name", ("DEV-",), ()),
)


def check_dev_contamination(environment):
    """Reserved DEV namespace must be ABSENT from production data. In a dev
    rehearsal the scan still runs and reports hit counts, informationally
    (the dev cast is expected there) — red only in a production-mode run."""
    from django.apps import apps
    hits = {}
    for label, field, prefixes, suffixes in DEV_NAMESPACE_SCAN:
        q = Q()
        for p in prefixes:
            q |= Q(**{f"{field}__startswith": p})
        for s in suffixes:
            q |= Q(**{f"{field}__endswith": s})
        n = apps.get_model(label).objects.filter(q).count()
        if n:
            hits[label] = n
    ok = (not hits) if environment == "prod" else True
    measured = {"hits": hits, "columns_scanned": len(DEV_NAMESPACE_SCAN)}
    if environment != "prod" and hits:
        measured["note"] = "informational in dev rehearsal — DEV identifiers are expected here"
    return _r("prod.contamination.dev-namespace",
              "DEV_DATASET_ARCHITECTURE §4 / DATA-D8 (production data never carries DEV identifiers)",
              "dev-contamination", ok, measured)


# ── production-safety ────────────────────────────────────────────────────────

# U10 owner DECLARATION (changed only by the owner; post-R11 flips update THIS
# declaration, never the check): both enforcement flags ship OFF.
OWNER_DECLARED_FLAGS = {
    "ENFORCE_ALLOCATION_BOUND": False,
    "ENFORCE_SETTLEMENT_RECONCILIATION": False,
}


def check_flags_vs_declaration():
    from django.conf import settings
    got = {flag: bool(getattr(settings, flag, False)) for flag in OWNER_DECLARED_FLAGS}
    return _r("prod.safety.flags-vs-declaration",
              "U10 (enforcement flags == owner-declared state; declaration is the input)",
              "production-safety", got == OWNER_DECLARED_FLAGS,
              {"declared": OWNER_DECLARED_FLAGS, "actual": got})


def check_migrations_consistency(_plan=None):
    """No unapplied migrations, no applied-but-unknown migrations. Read-only
    introspection (the executor builds a plan; nothing runs)."""
    if _plan is not None:
        unapplied, unknown = _plan()
    else:
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        targets = executor.loader.graph.leaf_nodes()
        unapplied = [f"{m.app_label}.{m.name}"
                     for m, _ in executor.migration_plan(targets)]
        unknown = sorted(f"{a}.{n}" for (a, n) in
                         set(executor.loader.applied_migrations)
                         - set(executor.loader.disk_migrations))
    ok = not unapplied and not unknown
    return _r("prod.safety.migrations-consistent",
              "PHASE_13 §6.4 (migrations applied == migration files; none unapplied/unknown)",
              "production-safety", ok,
              {"unapplied": unapplied[:10], "unknown": unknown[:10]})


def check_settings_sanity(environment):
    """DEBUG off in production-mode; SECRET_KEY presence (never its value)."""
    from django.conf import settings
    debug = bool(settings.DEBUG)
    secret_present = bool(getattr(settings, "SECRET_KEY", ""))
    ok = secret_present and (not debug if environment == "prod" else True)
    return _r("prod.safety.settings-sanity",
              "PHASE_13 §6.4 (DEBUG False in prod-mode report; secret presence, not value)",
              "production-safety", ok,
              {"DEBUG": debug, "secret_present": secret_present,
               "environment": environment})


# ── integrity (self-consistency — SELECT/aggregate only) ─────────────────────

def check_settlement_items_sum():
    """Σ(item.expected_earning) == settlement.expected_total for EVERY
    finalized settlement (self-consistent, never a frozen ₹ constant).
    Cost: one aggregate per finalized settlement (small, bounded set)."""
    from django.apps import apps
    AS_ = apps.get_model("expense", "AddaSettlement")
    bad = []
    qs = AS_.objects.filter(status="finalized")
    for s in qs:
        total = s.items.aggregate(x=Sum("expected_earning"))["x"] or 0
        if total != s.expected_total:
            bad.append({"settlement": s.reference,
                        "expected_total": str(s.expected_total), "items_sum": str(total)})
    return _r("prod.integrity.settlement-items-sum",
              "ARCHITECTURE_V2 §11 settlement math (items Σ = expected_total; settlement = the only money boundary)",
              "integrity", not bad, {"finalized": qs.count(), "violations": bad[:5]})


def check_ledger_reversals_net(_violators=None):
    """Every reversal entry mirrors the amount of the entry it reverses —
    reversal pairs net to zero (§11.5 correction truth: never edit, reverse).
    Cost: one filtered COUNT."""
    from django.apps import apps
    L = apps.get_model("expense", "WorkerLedgerEntry")
    pairs = L.objects.filter(reverses__isnull=False)
    mismatched = (_violators() if _violators is not None
                  else pairs.exclude(amount=F("reverses__amount")).count())
    return _r("prod.integrity.ledger-reversals-net",
              "ARCHITECTURE_V2 §11.5 / ledger_service reversal law (compensating entries, append-only)",
              "integrity", mismatched == 0,
              {"reversal_pairs": pairs.count(), "mismatched": mismatched})


def check_constraint_ledger_amount_positive(_violators=None):
    """The ledger amount CheckConstraint, re-checked in SQL (belt over the DB's
    own braces — a bypassed constraint would surface here). Cost: one COUNT."""
    from django.apps import apps
    L = apps.get_model("expense", "WorkerLedgerEntry")
    n = _violators() if _violators is not None else L.objects.filter(amount__lte=0).count()
    return _r("prod.integrity.constraint-ledger-amount-positive",
              "DB-Integrity PR1+PR2 CheckConstraints (2026-06-06; ledger amount > 0)",
              "integrity", n == 0, {"violators": n})


def check_constraint_wsc_gam(_violators=None):
    """The S3 good/alter/missing constraint shape (prod migration 0039:
    gam_nonneg_sum_positive), re-checked as a SELECT. Cost: one COUNT."""
    from django.apps import apps
    WSC = apps.get_model("production", "WorkerStageContribution")
    if _violators is not None:
        n = _violators()
    else:
        n = WSC.objects.filter(
            Q(good_quantity__lt=0) | Q(alter_quantity__lt=0)
            | Q(missing_quantity__lt=0)).count()
    return _r("prod.integrity.constraint-wsc-gam-nonneg",
              "S3 migration prod 0039 gam_nonneg_sum_positive (good/alter/missing ≥ 0)",
              "integrity", n == 0, {"violators": n})


def check_supersession_chain():
    """Every superseded settlement has a successor (reverse-then-supersede is
    a CHAIN, never a dead end). Cost: one filtered COUNT."""
    from django.apps import apps
    AS_ = apps.get_model("expense", "AddaSettlement")
    orphans = AS_.objects.filter(status="superseded",
                                 superseded_by__isnull=True).count()
    return _r("prod.integrity.supersession-chain",
              "ARCHITECTURE_V2 §11.5 (supersedes chain: superseded ⇒ finalized successor exists)",
              "integrity", orphans == 0, {"orphans": orphans})


# ── the production-safe runner ───────────────────────────────────────────────

def run_production_checks(environment, *, skip_categories=()):
    """The full production-safe subset. Returns a results list (categories
    skipped by the caller are simply not run — the caller records the skips
    in the envelope; never silent)."""
    skip = set(skip_categories)
    results = []
    if "dev-contamination" not in skip:
        results.append(check_dev_contamination(environment))
    if "production-safety" not in skip:
        results.append(check_flags_vs_declaration())
        results.append(check_migrations_consistency())
        results.append(check_settings_sanity(environment))
    if "integrity" not in skip:
        results.append(check_settlement_items_sum())
        results.append(check_ledger_reversals_net())
        results.append(check_constraint_ledger_amount_positive())
        results.append(check_constraint_wsc_gam())
        results.append(check_supersession_chain())
    return results
