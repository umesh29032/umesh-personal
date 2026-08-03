"""verification.checks.dev_world — the dev-world check registry (VER-B).

Categories here: `golden` (manifest conformance · LIVE shared-assertion re-run
· golden settlement totals + certified worker-item truth) and `smoke` (app
registry · URLConf · critical renders — the ONLY request-cycle territory,
contract §6.4; renders write session rows on the TARGET dev world, sanctioned
and disclosed).

Single-source law (VER-D4 + owner VER-B order): every golden value and every
assertion comes from a CERTIFIED source — `verification.assertions` (the
SEED-D6 library), the devseed scenario registry/content, and the extracted
per-worker item truth. ZERO golden literals exist in this package (test-pinned).
devseed imports are FUNCTION-LEVEL by design: these checks are dev-only (the
command polarity refuses anywhere devseed is absent).
"""

from verification.report import SPEC_VERSION, CheckResult


def _r(check_id, citation, category, ok, measured):
    return CheckResult(id=check_id, citation=citation, category=category,
                       status="pass" if ok else "fail", measured=measured)


# ── golden-category: manifest conformance ────────────────────────────────────

def check_manifest_spec_version(manifest, prefix=""):
    got = manifest.get("spec_version")
    return _r(f"dev.{prefix}manifest.spec-version",
              "DEV_DATASET_ARCHITECTURE §10 (spec semver pin)",
              "golden", got == SPEC_VERSION,
              {"manifest": got, "engine": SPEC_VERSION})


def check_manifest_database_match(manifest, prefix=""):
    from django.db import connection
    want, got = manifest.get("database"), connection.settings_dict.get("NAME", "")
    return _r(f"dev.{prefix}manifest.database-match",
              "SEED-D5 scratch law (verify THE world the manifest describes; "
              "the primary dev DB is never a target)",
              "golden", want == got, {"manifest": want, "connection": got})


def check_manifest_assertions_recorded(assertions_section, prefix=""):
    got = (assertions_section or {}).get("result")
    return _r(f"dev.{prefix}manifest.assertions-recorded",
              "PHASE_12 §6.5 (post-seed assertions, non-optional)",
              "golden", got == "PASS", {"recorded": got})


# ── golden-category: LIVE world state ────────────────────────────────────────

def check_assertions_rerun(slug, spec, manifest_handles, prefix=""):
    """Re-run the SEED-D6 shared library against the LIVE world — the same
    counts/handles/DEV-marking/flags pass the seeder ran, now as verification
    (drift since seeding = red)."""
    from verification.assertions import SeedAssertionError, run_post_seed
    from devseed.core import expected_counts, scenario_handles  # dev-only, lazy

    minted = scenario_handles(spec)
    outputs = [("raw_materials.ClothRoll", "roll_id", h)
               for h in manifest_handles if str(h).startswith("CR-")]
    if "journey" in spec:
        # Recipe class: the product is a BASELINE handle (mirrors the seeder).
        prod_handle = ("production.Product", "code", spec["product"]["code"])
        if prod_handle in minted:
            minted.remove(prod_handle)
            outputs.append(prod_handle)
    try:
        out = run_post_seed(expected_counts=expected_counts(spec), handles=minted,
                            output_handles=outputs, dev_prefixes=spec["dev_prefixes"])
        return _r(f"dev.{prefix}assertions.rerun",
                  "DEV_DATASET_ARCHITECTURE §6.1.7/§7 (shared assertion definitions)",
                  "golden", True, out)
    except SeedAssertionError as e:
        return _r(f"dev.{prefix}assertions.rerun",
                  "DEV_DATASET_ARCHITECTURE §6.1.7/§7 (shared assertion definitions)",
                  "golden", False, {"failures": str(e)[:400]})


def _certified_golden(slug, spec):
    """The certified expected settlement total — registry first (regression
    class, owner change-control), then the scenario's own derived config.
    Returns None for money-less worlds. NEVER a literal in this package."""
    from devseed.scenarios import SCENARIOS
    return (SCENARIOS.get(slug, {}).get("expected")
            or spec.get("settlement", {}).get("expected_total")
            or spec.get("journey", {}).get("golden"))


def check_golden_settlement_total(slug, spec, prefix=""):
    golden = _certified_golden(slug, spec)
    if golden is None:
        return None  # money-less world — no golden check to emit
    from django.apps import apps
    AS_ = apps.get_model("expense", "AddaSettlement")
    s = (AS_.objects.filter(adda__product__code=spec["product"]["code"],
                            status="finalized").order_by("-id").first())
    got = str(s.expected_total) if s else None
    return _r(f"dev.{prefix}golden.settlement-total",
              "DEV_DATASET_ARCHITECTURE §7 golden values (owner change-control)",
              "golden", got == golden,
              {"expected": golden, "got": got,
               "settlement": getattr(s, "reference", None)})


def check_golden_worker_items(slug, spec, prefix=""):
    """Per-worker item truth for the three replayed golden journeys — the
    extracted certified maps (SEED-C W2), consumed from their single source."""
    from devseed.tests.test_golden_journeys import EXPECTED_ITEMS  # single source
    expected = EXPECTED_ITEMS.get(slug)
    if expected is None:
        return None
    from django.apps import apps
    AS_ = apps.get_model("expense", "AddaSettlement")
    s = (AS_.objects.filter(adda__product__code=spec["product"]["code"],
                            status="finalized").order_by("-id").first())
    got = ({i.worker.email: str(i.expected_earning) for i in s.items.all()}
           if s else {})
    return _r(f"dev.{prefix}golden.worker-items",
              "extracted ADST-0004/0005/0006 per-worker truth (SEED-C W2, byte-matched)",
              "golden", got == expected,
              {"workers_expected": len(expected), "workers_got": len(got),
               "mismatches": sorted(set(expected.items()) ^ set(got.items()))[:6]})


# ── smoke-category (dev modes only) ──────────────────────────────────────────

CRITICAL_ROUTES = ("public_home", "accounts:login", "inventory:my_dashboard")


def check_smoke_app_registry():
    from django.apps import apps as django_apps
    from django.conf import settings
    loaded = {c.name for c in django_apps.get_app_configs()}
    missing = [a for a in settings.INSTALLED_APPS
               if a.split(".")[-1] not in {n.split(".")[-1] for n in loaded}
               and a not in loaded]
    return _r("dev.smoke.app-registry", "PHASE_13 §6.4 smoke (app registry loads)",
              "smoke", django_apps.ready and not missing,
              {"apps_loaded": len(loaded), "missing": missing})


def check_smoke_urlconf(routes=CRITICAL_ROUTES):
    from django.urls import NoReverseMatch, reverse
    failures = []
    for name in routes:
        try:
            reverse(name)
        except NoReverseMatch:
            failures.append(name)
    return _r("dev.smoke.urlconf", "PHASE_13 §6.4 smoke (URLConf resolves)",
              "smoke", not failures, {"routes": len(routes), "unresolved": failures})


def check_smoke_render_critical(sa_email):
    """Critical pages render 200 — anon public/login pages + the dashboard AS
    the world's SA cast identity (request cycle sanctioned ONLY here; writes
    session rows on the TARGET dev world — disclosed)."""
    from django.apps import apps
    from django.test import Client
    from django.urls import reverse
    measured, ok = {}, True
    client = Client()
    for name in ("public_home", "accounts:login"):
        code = client.get(reverse(name)).status_code
        measured[name] = code
        ok = ok and code == 200
    User = apps.get_model("accounts", "User")
    sa = User.objects.filter(email=sa_email).first()
    if sa is None:
        ok, measured["sa"] = False, f"cast identity {sa_email} missing"
    else:
        client.force_login(sa)
        code = client.get(reverse("inventory:my_dashboard")).status_code
        measured["inventory:my_dashboard(sa)"] = code
        ok = ok and code == 200
    return _r("dev.smoke.render-critical",
              "PHASE_13 §6.4 smoke (critical renders as cast identities, dev-only)",
              "smoke", ok, measured)


# ── feature-slug validation (shared by verify_feature; unit-testable) ────────

def feature_slug_failure(slug):
    from devseed.scenarios import SCENARIOS, valid_slugs
    if slug not in SCENARIOS:
        return (f"Unknown scenario '{slug}'. Valid slugs:\n  "
                + "\n  ".join(valid_slugs()))
    if not SCENARIOS[slug]["implemented"]:
        return (f"Scenario '{slug}' is not executable/verifiable: "
                f"{SCENARIOS[slug].get('note', 'not implemented')}")
    return None


# ── the dev-world runner ─────────────────────────────────────────────────────

def run_checks(slug, manifest, *, skip_categories=()):
    """All dev-world checks for one world (composite-aware). Returns
    (results, skipped_categories_applied). Skips are category-level and
    surface in the report envelope — never silent."""
    from devseed.core import CONTENT  # dev-only, lazy by design

    skip = {c for c in skip_categories}
    results = []
    spec = CONTENT[slug]

    if "golden" not in skip:
        results.append(check_manifest_spec_version(manifest))
        results.append(check_manifest_database_match(manifest))
        if "composite" in spec:
            for child in spec["composite"]:
                child_spec = CONTENT[child]
                pfx = f"child.{child}."
                section = (manifest.get("composite") or {}).get(child, {})
                results.append(
                    check_manifest_assertions_recorded(section.get("assertions"), pfx))
                results.append(
                    check_assertions_rerun(child, child_spec, (), prefix=pfx))
                for maybe in (check_golden_settlement_total(child, child_spec, pfx),
                              check_golden_worker_items(child, child_spec, pfx)):
                    if maybe is not None:
                        results.append(maybe)
        else:
            results.append(
                check_manifest_assertions_recorded(manifest.get("assertions")))
            results.append(
                check_assertions_rerun(slug, spec, manifest.get("handles", ())))
            for maybe in (check_golden_settlement_total(slug, spec),
                          check_golden_worker_items(slug, spec)):
                if maybe is not None:
                    results.append(maybe)

    if "smoke" not in skip:
        results.append(check_smoke_app_registry())
        results.append(check_smoke_urlconf())
        # Composite worlds carry no cast of their own — render as the first
        # child's SA identity (same DEV cast family).
        sa_handle = (spec.get("sa_handle")
                     or CONTENT[spec["composite"][0]]["sa_handle"])
        results.append(check_smoke_render_critical(sa_handle))

    return results, sorted(skip)
