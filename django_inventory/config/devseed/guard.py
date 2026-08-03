"""devseed.guard — the 4-factor production guard (spec DATA-D8 / PHASE_12 §6.6).

Pure functions first (unit-testable with injected values), one thin gather step
reading real settings/connection. Guard bypass flags DO NOT EXIST by design.
The fifth factor is STRUCTURAL: this app is registered only in
config/config/settings/local.py, so these commands do not exist under
production settings at all.

Factors (ALL must pass for any seed command; reset adds the confirmation):
  1. settings module   == the dev settings module
  2. dev marker        DEBUG is True
  3. DB-name allowlist target database ∈ SCRATCH_DB_ALLOWLIST (owner-ratified
                       SEED-D5 2026-07-17 — the PRIMARY dev DB is deliberately
                       NOT allowlisted: it is never a Phase-12 seeding target)
  4. destructive gate  reset only: exact per-database confirmation flag
"""

# The spec this engine implements (DEV_DATASET_ARCHITECTURE.md §10) — printed
# in every command banner per SEED-D7.
SPEC_VERSION = "1.0.0"

DEV_SETTINGS_MODULE = "config.settings.local"

# Owner-ratified verbatim (SEED-D5, 2026-07-17). frozenset: immutable by intent.
SCRATCH_DB_ALLOWLIST = frozenset(
    {"inventory_seed_scratch_1", "inventory_seed_scratch_2"}
)


def check_settings_module(settings_module):
    """Factor 1 — refuse unless running under the dev settings module."""
    if settings_module != DEV_SETTINGS_MODULE:
        return (
            f"settings module is '{settings_module}' — seeder commands run ONLY "
            f"under '{DEV_SETTINGS_MODULE}'"
        )
    return None


def check_dev_marker(debug):
    """Factor 2 — refuse unless DEBUG (the dev marker) is on."""
    if not debug:
        return "DEBUG is False — not a development environment"
    return None


def check_db_allowlist(db_name):
    """Factor 3 — refuse unless the TARGET database is an allowlisted scratch DB."""
    if db_name not in SCRATCH_DB_ALLOWLIST:
        allowed = ", ".join(sorted(SCRATCH_DB_ALLOWLIST))
        return (
            f"database '{db_name}' is not an allowlisted scratch DB "
            f"(allowed: {allowed}) — the primary dev DB is never a seeder target"
        )
    return None


def check_reset_confirmation(db_name, confirmed_db):
    """Factor 4 (reset only) — the exact-string destructive confirmation.

    confirmed_db = the db name extracted from the literal flag the operator
    typed (--i-understand-this-destroys-<dbname>); must equal the target.
    """
    if confirmed_db != db_name:
        return (
            f"destructive confirmation missing or mismatched: reset of '{db_name}' "
            f"requires the literal flag --i-understand-this-destroys-{db_name}"
        )
    return None


def guard_failures(kind, settings_module, debug, db_name, confirmed_db=None):
    """Collect EVERY failing factor (never short-circuit — refusals are verbatim
    and complete so the operator sees the whole wall, not one brick)."""
    failures = [
        check_settings_module(settings_module),
        check_dev_marker(debug),
        check_db_allowlist(db_name),
    ]
    if kind == "reset":
        failures.append(check_reset_confirmation(db_name, confirmed_db))
    return [f for f in failures if f]


def gather_and_check(kind, target_db_name=None, confirmed_db=None):
    """Thin impure layer: read the real settings + default connection and run
    the pure checks. target_db_name overrides for reset (--db flag)."""
    from django.conf import settings
    from django.db import connection

    db_name = target_db_name or connection.settings_dict.get("NAME", "")
    return guard_failures(
        kind,
        settings_module=getattr(settings, "SETTINGS_MODULE", ""),
        debug=settings.DEBUG,
        db_name=db_name,
        confirmed_db=confirmed_db,
    )
