"""Shared thin-CLI base for the four seeder commands (PHASE_12 §6.1: commands
are shells; ALL logic lives in the orchestration core so it is testable
without the CLI). SEED-D state: guard → dry-run/implemented gate → core
dispatch → manifest summary. Two registry entries stay non-executable by
owner ruling (spec §12 A1 · DATA-D6) and refuse with their registry note."""

from django.core.management.base import BaseCommand, CommandError

from devseed.guard import SPEC_VERSION, gather_and_check
from devseed.scenarios import SCENARIOS


class GuardedSeedCommand(BaseCommand):
    scenario_slug = None  # set by subclasses (seed_feature resolves per-arg)

    def add_arguments(self, parser):
        # --check: dry-run — print the plan, write NOTHING (SEED-D7). There is
        # deliberately NO --skip-assertions flag (assertions are not optional).
        parser.add_argument(
            "--check", action="store_true",
            help="Dry-run: print the seeding plan (scenario, layers, expected counts); write nothing.",
        )

    def banner(self, slug):
        self.stdout.write(f"devseed — spec v{SPEC_VERSION} — scenario: {slug}")

    def run_guard(self, kind="seed", target_db_name=None, confirmed_db=None):
        failures = gather_and_check(kind, target_db_name=target_db_name,
                                    confirmed_db=confirmed_db)
        if failures:
            # CommandError: Django's nonzero-exit path — refusals verbatim + complete.
            raise CommandError("GUARD REFUSED:\n- " + "\n- ".join(failures))

    def print_plan(self, slug):
        s = SCENARIOS[slug]
        self.stdout.write(f"PLAN (dry-run, nothing written): scenario={slug} "
                          f"class={s['class']} layers={s.get('layers', '(per class)')} "
                          f"implemented={s['implemented']}")

    def handle_seed(self, slug, options):
        self.banner(slug)
        self.run_guard("seed")
        if options.get("check"):
            self.print_plan(slug)
            return
        if not SCENARIOS[slug]["implemented"]:
            # spec §12 A1 (₹225 historical) / DATA-D6 (performance deferred):
            # non-executable BY OWNER RULING, never silently skipped.
            raise CommandError(
                f"Scenario '{slug}' is not executable: "
                f"{SCENARIOS[slug].get('note', 'not implemented')} "
                f"(guard PASSED, zero writes performed)."
            )
        from devseed import core
        manifest = core.seed_scenario(slug, manifest_dir=core.DEFAULT_MANIFEST_DIR)
        totals = {"created": 0, "skipped": 0}
        for c in manifest["counts"].values():
            totals["created"] += c["created"]
            totals["skipped"] += c["skipped"]
        self.stdout.write(
            f"OK scenario={slug} db={manifest['database']} "
            f"created={totals['created']} skipped={totals['skipped']} "
            f"assertions={manifest['assertions']['result']}"
        )
        if manifest.get("money"):
            self.stdout.write(
                f"money: settlement={manifest['money']['settlement']} "
                f"expected_total={manifest['money']['expected_total']} "
                f"delta_explained={manifest['money']['delta_explained']}"
            )
        return
