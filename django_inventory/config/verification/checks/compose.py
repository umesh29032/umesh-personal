"""verification.checks.compose — verify_all composition (VER-D7).

Environment-aware, run-all-then-aggregate (NO fail-fast): dev = every
MANIFEST-PRESENT world (dev-world suite each, ids prefixed `world.<slug>.`)
+ the production-safe subset as a rehearsal; prod = the production-safe
subset only. Worlds without a manifest are not silently dropped — the
composition summary result lists verified vs manifest-absent worlds.
"""

from dataclasses import replace

from verification.report import CheckResult


def _prefixed(slug, result):
    return replace(result, id=f"world.{slug}.{result.id}")


def compose_all(environment, *, manifest_dir=None, skip_categories=()):
    """Returns (results, skipped_categories). Dev-world composition is
    manifest-driven (contract §6.3); devseed imports are function-level and
    only reachable in dev (prod composition never touches devseed)."""
    from verification.checks.production import run_production_checks

    results = []
    verified_worlds, absent_worlds = [], []

    if environment == "dev":
        from devseed.scenarios import SCENARIOS  # dev-only, lazy
        from verification.checks.dev_world import run_checks
        from verification.manifests import ManifestMissing, latest_manifest

        for slug in [k for k, s in SCENARIOS.items() if s["implemented"]]:
            try:
                manifest = latest_manifest(slug, manifest_dir)
            except ManifestMissing:
                absent_worlds.append(slug)
                continue
            world_results, _ = run_checks(slug, manifest,
                                          skip_categories=skip_categories)
            results += [_prefixed(slug, r) for r in world_results]
            verified_worlds.append(slug)

    results += run_production_checks(environment, skip_categories=skip_categories)

    # The composition summary — absent worlds are REPORTED, never silent.
    results.append(CheckResult(
        id="all.composition",
        citation="PHASE_13 §6.3/VER-D7 (environment-aware run-all-then-aggregate)",
        category="production-safety", status="pass",
        measured={"environment": environment,
                  "worlds_verified": verified_worlds,
                  "worlds_without_manifest": absent_worlds}))
    return results, sorted(set(skip_categories))
