"""verification.assertions — THE shared assertion library (spec §6.1.7).

SINGLE-SOURCE module — exactly ONE implementation exists (owner ruling,
VER-D1 2026-07-17). RELOCATED here from `devseed.assertions` at VER-A as the
SEED-D6 coordinated reconciliation: this app is BASE-settings (production-
present) so `verify_production` can reach the library; `devseed` (dev-only)
IMPORTS it for post-seed self-assertions — one implementation, two consumers,
never forked (dated amendments in the PHASE_12 + PHASE_13 Design Records).

Content is behavior-identical to the Phase-12 certified module: counts ·
handle existence · DEV-marking · flags-untouched. Golden-value/referential
money checks arrive as CITED checks in `verification.checks` (VER-B/C), not
here.
"""

from django.apps import apps
from django.conf import settings


class SeedAssertionError(AssertionError):
    """Post-seed assertion failure — the seeded world STAYS for forensics
    (PHASE_12 contract §6.5); the command exits nonzero."""


def assert_counts(expected):
    """expected: {model_label: exact_count_of_scenario_rows_by_filter} where each
    value = (filter_kwargs, expected_n). Counted, never asserted from memory."""
    failures = []
    for label, (flt, want) in expected.items():
        got = apps.get_model(label).objects.filter(**flt).count()
        if got != want:
            failures.append(f"count {label}{flt}: expected {want}, got {got}")
    return failures


def assert_handles_exist(handles):
    """handles: iterable of (model_label, field, value) — every seeded natural
    handle must resolve to exactly one row."""
    failures = []
    for label, field, value in handles:
        n = apps.get_model(label).objects.filter(**{field: value}).count()
        if n != 1:
            failures.append(f"handle {label}.{field}={value!r}: expected 1 row, got {n}")
    return failures


def assert_dev_marking(handles, prefixes):
    """DEV-marking invariant (spec §4): every dataset-born handle is
    identifiable as dataset-born by its identifier ALONE."""
    failures = []
    for _, _, value in handles:
        v = str(value)
        if not any(v.startswith(p) or v.lower().startswith(p.lower()) for p in prefixes):
            failures.append(f"handle {v!r} carries no DEV marking (allowed prefixes: {prefixes})")
    return failures


def assert_flags_untouched():
    """U10: seeding must never perturb the enforcement flags. AE-1 (2026-07-20):
    ENFORCE_ALLOCATION_BOUND retired (bound now always-on, no flag); only the
    settlement-reconciliation flag remains."""
    failures = []
    for flag in ("ENFORCE_SETTLEMENT_RECONCILIATION",):
        if getattr(settings, flag, False):
            failures.append(f"enforcement flag {flag} is ON — seeding must never touch flags")
    return failures


def run_post_seed(*, expected_counts, handles, dev_prefixes, output_handles=()):
    """The automatic post-seed pass. Raises SeedAssertionError with the FULL
    failure list (never first-failure-only).

    handles         = MINTED natural handles (scenario-authored) — existence +
                      DEV-marking both asserted.
    output_handles  = SERVICE-ISSUED handles (spec §4: e.g. roll_id CR-NNNNNN —
                      the production intake format the spec itself declares).
                      Existence-asserted only; their dataset-born identity
                      derives from their DEV-marked masters (FKs), which the
                      count filters pin."""
    failures = (
        assert_counts(expected_counts)
        + assert_handles_exist(list(handles) + list(output_handles))
        + assert_dev_marking(handles, dev_prefixes)
        + assert_flags_untouched()
    )
    if failures:
        raise SeedAssertionError("POST-SEED ASSERTIONS FAILED:\n- " + "\n- ".join(failures))
    return {"checks": 4, "handles": len(handles), "result": "PASS"}
