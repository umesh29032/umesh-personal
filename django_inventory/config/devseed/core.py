"""devseed.core — the orchestration engine (PHASE_12 §6.1: ALL logic lives
here, testable without the CLI; commands are thin shells).

SEED-B state: layer executors 2–6 live; layers 7+ are wave-gated (SEED-C/D).
One outer `transaction.atomic` per world (spec §8 / SEED-D3) — a mid-seed
failure rolls the whole world back; the post-seed assertions run AFTER commit
(a failed assertion leaves the world for forensics, contract §6.5)."""

import json
import os
from datetime import datetime, timezone
from decimal import Decimal

from django.apps import apps
from django.db import connection, transaction

# SEED-D6 reconciliation (VER-D1, 2026-07-17): the shared assertion library
# lives in the production-present `verification` app; devseed IMPORTS it.
from verification.assertions import run_post_seed
from devseed.guard import SPEC_VERSION
from devseed.layers.cast import seed_cast
from devseed.layers.machines import seed_machines
from devseed.layers.masters import seed_masters
from devseed.layers.journeys import replay_journey
from devseed.layers.money import settle_adda
from devseed.layers.production_truth import seed_adda_journey
from devseed.layers.products import seed_product_and_flow
from devseed.layers.rolls import seed_rolls
from devseed.layers.storefront import seed_storefront
from devseed.scenarios.extras import EXTRA_CONTENT, EXTRA_STEPS
from devseed.scenarios.minimal_money import MINIMAL_MONEY, MINIMAL_WITH_JOURNEY
from devseed.scenarios.recipes import RECIPES

# Scenario content lookup (grows per wave; slugs must exist in the registry).
CONTENT = {"minimal": MINIMAL_WITH_JOURNEY, "feature-settlement": MINIMAL_MONEY,
           **RECIPES, **EXTRA_CONTENT}

# Highest layer with a live executor — the wave gate (SEED-D: 11 = full stack;
# 9 storefront · 10 patterns_ai · 11 tracking rows = journey service outcomes).
IMPLEMENTED_THROUGH_LAYER = 11

# Repo-root var/ (gitignored) — the SEED-D8 manifest archive, cwd-independent.
DEFAULT_MANIFEST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "var", "seed_manifests")


def seed_scenario(slug, *, max_layer=IMPLEMENTED_THROUGH_LAYER, manifest_dir=None):
    """Seed one scenario's layers ≤ max_layer. Returns the manifest dict."""
    spec = CONTENT[slug]

    # Composite scenarios (seed_factory class): each child = its own WORLD
    # with its own outer atomic (spec §8: one atomic per world).
    if "composite" in spec:
        children = {child: seed_scenario(child, max_layer=max_layer,
                                         manifest_dir=manifest_dir)
                    for child in spec["composite"]}
        manifest = {
            "scenario": slug, "spec_version": SPEC_VERSION,
            "database": connection.settings_dict.get("NAME", ""),
            "composite": {c: {"counts": m["counts"], "money": m.get("money"),
                               "assertions": m["assertions"]}
                          for c, m in children.items()},
            "counts": {c: {"created": sum(x["created"] for x in m["counts"].values()),
                            "skipped": sum(x["skipped"] for x in m["counts"].values())}
                       for c, m in children.items()},
            "assertions": {"result": "PASS"},
            "money": None,
            "handles": [h for m in children.values() for h in m["handles"]],
            "ran_at": datetime.now(timezone.utc).isoformat(),
        }
        if manifest_dir:
            write_manifest(manifest, manifest_dir)
        return manifest

    counts = {}
    with transaction.atomic():  # spec §8: scenario = all-or-nothing
        cast = seed_cast(spec["cast"])
        counts["2-cast"] = {k: cast[k] for k in ("created", "skipped")}
        mgr = cast["actors"][spec["manager_handle"]]
        sa = cast["actors"][spec["sa_handle"]]

        masters = seed_masters(spec["masters"], actor=mgr)
        counts["3-masters"] = {k: masters[k] for k in ("created", "skipped")}

        # Product create = super_admin-only (product_service gate); flow edits = manager.
        prod = None
        if spec.get("product"):
            prod = seed_product_and_flow(
                spec["product"], spec["flow"], actor=sa, flow_actor=mgr,
                stage_costs=spec.get("stage_costs", ()))
            counts["4-products-flows"] = {k: prod[k] for k in ("created", "skipped")}
            # Optional grain config (S4 D1) via the certified flow_service writer.
            for g in spec.get("grain", ()):
                from production.services import flow_service
                WS = apps.get_model("production", "WorkflowStage")
                ws = WS.objects.get(product=prod["product"],
                                    stage__code=g["stage"])
                if ws.allocation_dimensions != g["dimensions"]:
                    flow_service.set_stage_grain(
                        user=mgr, workflow_stage=ws,
                        allocation_dimensions=g["dimensions"])

        if "machines" in spec and max_layer >= 5:
            mach = seed_machines(spec["machines"], actor=mgr)
            counts["5-machines"] = {k: mach[k] for k in ("created", "skipped")}

        # Recipe extras: product sizes + pattern assignments (certified writers:
        # product_size_service + patterns_ai register_pattern_definition).
        if spec.get("sizes"):
            from production.services import product_size_service
            ProductSize = apps.get_model("production", "ProductSize")
            for code in spec["sizes"]:
                if not ProductSize.objects.filter(product=prod["product"], code=code).exists():
                    # SA-only gate (same class as create_product).
                    product_size_service.add_product_size(
                        sa, product=prod["product"], code=code, label=code.upper())
                    counts.setdefault("4b-sizes", {"created": 0, "skipped": 0})["created"] += 1
                else:
                    counts.setdefault("4b-sizes", {"created": 0, "skipped": 0})["skipped"] += 1
        if spec.get("patterns"):
            from patterns_ai.services.pattern_geometry_service import register_pattern_definition
            PPA = apps.get_model("production", "ProductPatternAssignment")
            for name in spec["patterns"]:
                if PPA.objects.filter(product=prod["product"], pattern__name=name).exists():
                    counts.setdefault("4c-patterns", {"created": 0, "skipped": 0})["skipped"] += 1
                    continue
                register_pattern_definition(user=sa, product=prod["product"], name=name)
                counts.setdefault("4c-patterns", {"created": 0, "skipped": 0})["created"] += 1

        rolls = seed_rolls(spec["rolls"], masters["objects"], actor=mgr)
        counts["6-rolls"] = {k: rolls[k] for k in ("created", "skipped")}

        if spec.get("storefront") and max_layer >= 9:
            sf = seed_storefront(spec["storefront"])
            counts["9-storefront"] = {k: sf[k] for k in ("created", "skipped")}

        money_recon = None
        world_adda = None
        if "journey" in spec and max_layer >= 7:
            ClothRoll = apps.get_model("raw_materials", "ClothRoll")
            roll_objs = list(ClothRoll.objects.filter(roll_id__in=rolls["roll_ids"])
                             .select_related("cloth_color"))
            journey = replay_journey(spec, actors=cast["actors"], product=prod["product"], rolls=roll_objs)
            counts["7-production-truth"] = {k: journey[k] for k in ("created", "skipped")}
            world_adda = journey["adda"]
            if max_layer >= 8:
                money_recon = settle_adda(
                    journey["adda"], manager=mgr,
                    expected_total=spec["journey"]["golden"])
                counts["8-money"] = {k: money_recon[k] for k in ("created", "skipped")}
        elif "adda_journey" in spec and max_layer >= 7:
            ClothRoll = apps.get_model("raw_materials", "ClothRoll")
            roll = ClothRoll.objects.get(roll_id=rolls["roll_ids"][0])
            journey = seed_adda_journey(
                spec["adda_journey"], actors=cast["actors"], roll=roll,
                product=prod["product"])
            counts["7-production-truth"] = {k: journey[k] for k in ("created", "skipped")}
            world_adda = journey["adda"]

            if "settlement" in spec and max_layer >= 8:
                money_recon = settle_adda(
                    journey["adda"],
                    manager=cast["actors"][spec["settlement"]["manager"]],
                    expected_total=spec["settlement"]["expected_total"])
                counts["8-money"] = {k: money_recon[k] for k in ("created", "skipped")}

        # SEED-D post-steps: certified-service compositions per scenario
        # (allocation · fnf · machine windows · edge worlds) — idempotent.
        if spec.get("post"):
            step = EXTRA_STEPS[spec["post"]]
            ctx = {"actors": cast["actors"], "mgr": mgr, "sa": sa, "adda": world_adda}
            post = step(ctx)
            counts["post-" + spec["post"]] = {
                "created": post.get("created", 0), "skipped": post.get("skipped", 0)}
            post_facts = {k: v for k, v in post.items() if k not in ("created", "skipped")}
        else:
            post_facts = None

    minted = scenario_handles(spec)
    outputs = [("raw_materials.ClothRoll", "roll_id", rid) for rid in rolls["roll_ids"]]
    if "journey" in spec:
        # Recipe class: the product is a BASELINE handle (migration-seeded,
        # converged-with, never DEV-minted) — existence-checked only.
        prod_handle = ("production.Product", "code", spec["product"]["code"])
        minted.remove(prod_handle)
        outputs.append(prod_handle)
    handles = minted + outputs
    assertion_result = run_post_seed(
        expected_counts=expected_counts(spec),
        handles=minted,
        output_handles=outputs,
        dev_prefixes=spec["dev_prefixes"],
    )

    # Ledger recount discipline (owner Wave-1 mandate): every money delta is
    # explained or the seed FAILS (post-commit — the world stays for forensics).
    money_manifest = None
    if money_recon is not None:
        before = Decimal(money_recon["ledger_before"]["sum"])
        after = Decimal(money_recon["ledger_after"]["sum"])
        expected_delta = Decimal(money_recon["ledger_delta_expected"])
        from verification.assertions import SeedAssertionError
        if after - before != expected_delta:
            raise SeedAssertionError(
                f"LEDGER RECONCILIATION FAILED: Σ before {before} → after {after} "
                f"(delta {after - before}) != expected {expected_delta}")
        s = money_recon.get("settlement")
        money_manifest = {
            "settlement": getattr(s, "reference", None),
            "expected_total": str(getattr(s, "expected_total", "")),
            "ledger_before": money_recon["ledger_before"],
            "ledger_after": money_recon["ledger_after"],
            "delta_explained": str(expected_delta),
        }
    manifest = {
        "scenario": slug,
        "spec_version": SPEC_VERSION,
        "database": connection.settings_dict.get("NAME", ""),
        "max_layer": max_layer,
        "counts": counts,
        "handles": [h[2] for h in handles],
        "assertions": assertion_result,
        "money": money_manifest,
        "post": post_facts,
        # Manifest timestamp = an OPERATIONAL log field (SEED-D8), never part
        # of seeded DB content (determinism lives in the data, spec §1).
        "ran_at": datetime.now(timezone.utc).isoformat(),
    }
    if manifest_dir:
        write_manifest(manifest, manifest_dir)
    return manifest


def scenario_handles(spec):
    """Every MINTED natural handle this scenario authors, as assertion tuples
    (service-issued output handles — roll_ids — are appended separately)."""
    handles = [("accounts.User", "email", c["handle"]) for c in spec["cast"]]
    m = spec["masters"]
    handles += [
        ("raw_materials.ClothType", "name", m["cloth_type"]),
        ("raw_materials.ClothColor", "name", m["cloth_color"]),
        ("raw_materials.StorageLocation", "name", m["storage"]),
        ("production.StageCategory", "code", m["stage_category"]["code"]),
    ]
    handles += [("production.Stage", "code", s["code"]) for s in m["stages"]]
    if spec.get("product"):
        handles += [("production.Product", "code", spec["product"]["code"])]
    return handles


def expected_counts(spec):
    """Exact per-scenario row expectations (counted post-seed, spec §7)."""
    m = spec["masters"]
    out = {
        "production.Stage": (
            {"category__code": m["stage_category"]["code"]}, len(m["stages"])),
        "raw_materials.ClothRoll": (
            {"cloth_type__name": m["cloth_type"]},
            sum(int(r["qty"]) for r in spec["rolls"]["rolls"])),
    }
    if spec.get("product"):
        # +1: create_product auto-attaches the mandatory LAYERING first stage
        # (production law — a Product without a flow would break create_adda).
        out["production.WorkflowStage"] = (
            {"product__code": spec["product"]["code"]}, len(spec["flow"]) + 1)
    return out


def write_manifest(manifest, manifest_dir):
    os.makedirs(manifest_dir, exist_ok=True)
    stamp = manifest["ran_at"].replace(":", "").replace("+", "Z")
    path = os.path.join(manifest_dir, f"{manifest['scenario']}-{stamp}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
    return path


# ── SEED-E: the destructive reset path (NON-transactional by nature, SEED-D3;
#    DDL cannot roll back — hence the strictest confirmation upstream) ─────────

# Runtime identifiers permitted to differ between otherwise-identical runs
# (contract: "identical manifest except permitted runtime identifiers").
VOLATILE_MANIFEST_KEYS = ("ran_at",)


def strip_volatile(manifest, extra=()):
    """Manifest minus the permitted runtime identifiers — the determinism
    comparison surface (same-DB: strip ran_at; cross-DB: also strip the DB
    identity keys the caller names in `extra`)."""
    drop = set(VOLATILE_MANIFEST_KEYS) | set(extra)
    return {k: v for k, v in manifest.items() if k not in drop}


def _drop_and_recreate(target_db):
    """DROP + CREATE the allowlisted scratch DB via a psycopg2 maintenance
    connection ('postgres') using the project's own credentials. Closes every
    Django connection first (an open handle to the target blocks DROP)."""
    import psycopg2
    from django.conf import settings
    from django.db import connections
    from psycopg2 import sql

    connections.close_all()
    d = settings.DATABASES["default"]
    conn = psycopg2.connect(dbname="postgres", user=d["USER"],
                            password=d["PASSWORD"], host=d["HOST"], port=d["PORT"])
    conn.autocommit = True  # CREATE/DROP DATABASE refuse to run in a transaction
    try:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(target_db)))
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target_db)))
    finally:
        conn.close()


def _migrate_target(target_db):
    """Point the process's default connection at the scratch target, then run
    the full migration chain (layer 1 = baseline). The switch is deliberate and
    process-lifetime: everything after a reset (seed, assertions) must hit the
    scratch DB, never the connection the CLI started on."""
    from django.core.management import call_command
    from django.db import connections

    connections.close_all()
    connections.databases["default"]["NAME"] = target_db
    call_command("migrate", verbosity=0, interactive=False)


def run_reset(target_db, *, seed_slug=None, manifest_dir=None,
              _dropper=None, _migrator=None, _seeder=None):
    """SEED-E orchestration: drop → recreate → migrate → optional seed (with
    its own post-seed assertions) → reset manifest. Belt over braces: refuses
    any non-allowlisted target even though the command guard already did — this
    function must be safe to call directly. The _dropper/_migrator/_seeder
    injection points exist ONLY for failure-propagation tests (guard factor 2
    keeps the real path off battery/test databases by design); production
    callers never pass them."""
    from devseed.guard import SCRATCH_DB_ALLOWLIST

    if target_db not in SCRATCH_DB_ALLOWLIST:
        raise ValueError(
            f"run_reset refused: '{target_db}' is not an allowlisted scratch DB "
            f"(allowed: {', '.join(sorted(SCRATCH_DB_ALLOWLIST))})")

    (_dropper or _drop_and_recreate)(target_db)
    (_migrator or _migrate_target)(target_db)

    seeded = None
    if seed_slug:
        s = (_seeder or seed_scenario)(seed_slug, manifest_dir=manifest_dir)
        # Nested summary carries NO DB identity — cross-DB comparable as-is.
        seeded = {"scenario": seed_slug, "counts": s["counts"],
                  "assertions": s["assertions"], "money": s.get("money"),
                  "handles": s["handles"]}

    manifest = {
        "scenario": f"reset-{target_db}",  # manifest filename key
        "reset": target_db,
        "spec_version": SPEC_VERSION,
        "migrated": True,
        "seeded": seeded,
        "ran_at": datetime.now(timezone.utc).isoformat(),
    }
    if manifest_dir:
        write_manifest(manifest, manifest_dir)
    return manifest
