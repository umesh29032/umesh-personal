"""reset_demo — the DESTRUCTIVE path (drop→migrate→optional seed; SEED-D3
non-transactional by nature ⇒ the strictest confirmation).

Confirmation design (SEED-D7 exact-string gate): the allowlist is CLOSED
(two owner-ratified names), so each scratch DB gets its own literal flag —
a typo cannot confirm the wrong database:
    reset_demo --db inventory_seed_scratch_1 --i-understand-this-destroys-inventory_seed_scratch_1

SEED-E state (2026-07-17): the real reset — guard + confirmation → drop →
recreate → migrate → optional `--seed <slug>` (with post-seed assertions) →
reset manifest. NON-transactional (DDL); no bypass flags exist.
"""

from django.core.management.base import BaseCommand, CommandError

from devseed.guard import SPEC_VERSION, gather_and_check
from devseed.scenarios import SCENARIOS, valid_slugs


class Command(BaseCommand):
    help = "DESTRUCTIVE: rebuild an allowlisted scratch DB (drop → migrate → optional seed)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--db", default="inventory_seed_scratch_1",
            help="Target scratch database (must be allowlisted).",
        )
        parser.add_argument(
            "--seed", default=None, metavar="SLUG",
            help="Optionally seed this registry scenario after the rebuild.",
        )
        # One literal flag per allowlisted name — the exact-string destructive
        # gate is typo-proof by construction (argparse store_true flags).
        parser.add_argument("--i-understand-this-destroys-inventory_seed_scratch_1",
                            action="store_true", dest="confirm_scratch_1",
                            help="Exact confirmation for inventory_seed_scratch_1.")
        parser.add_argument("--i-understand-this-destroys-inventory_seed_scratch_2",
                            action="store_true", dest="confirm_scratch_2",
                            help="Exact confirmation for inventory_seed_scratch_2.")

    def handle(self, *args, **options):
        target = options["db"]
        self.stdout.write(f"devseed — spec v{SPEC_VERSION} — reset target: {target}")
        confirmed_db = None
        if options["confirm_scratch_1"]:
            confirmed_db = "inventory_seed_scratch_1"
        if options["confirm_scratch_2"]:
            # Two confirmations at once = ambiguous intent ⇒ treated as unconfirmed.
            confirmed_db = None if confirmed_db else "inventory_seed_scratch_2"
        failures = gather_and_check("reset", target_db_name=target,
                                    confirmed_db=confirmed_db)
        if failures:
            raise CommandError("GUARD REFUSED:\n- " + "\n- ".join(failures))

        seed_slug = options.get("seed")
        if seed_slug is not None:
            # Same validation lattice as seed_feature — BEFORE any DDL runs.
            if seed_slug not in SCENARIOS:
                raise CommandError(
                    f"Unknown scenario '{seed_slug}'. Valid slugs:\n  "
                    + "\n  ".join(valid_slugs()))
            if not SCENARIOS[seed_slug]["implemented"]:
                raise CommandError(
                    f"Scenario '{seed_slug}' is not executable: "
                    f"{SCENARIOS[seed_slug].get('note', 'not implemented')} "
                    f"(nothing was reset).")

        from devseed import core
        manifest = core.run_reset(target, seed_slug=seed_slug,
                                  manifest_dir=core.DEFAULT_MANIFEST_DIR)
        self.stdout.write(f"RESET OK db={target} migrated=True "
                          f"seeded={seed_slug or '-'}")
        if manifest["seeded"]:
            self.stdout.write(
                f"assertions={manifest['seeded']['assertions']['result']}")
