"""verify_all — environment-aware composition (VER-D7): dev = every
manifest-present world + the production-safe rehearsal; prod = the
production-safe subset only. Run-all-then-aggregate — no fail-fast."""

from django.core.management.base import CommandError

from verification.guard import environment
from verification.management.commands._base import PolarityCommand
from verification.report import build_report, exit_code, render_stdout, write_report


class Command(PolarityCommand):
    help = "Run every applicable verification for this environment and aggregate one report."
    command_name = "verify_all"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--manifest-dir", default=None, metavar="DIR",
                            help="Seed-manifest directory (default var/seed_manifests/).")

    def handle(self, *args, **options):
        self.banner()
        self.run_polarity()
        from verification.checks.compose import compose_all
        env = environment()
        results, skipped = compose_all(env,
                                       manifest_dir=options.get("manifest_dir"),
                                       skip_categories=options.get("skip", []))
        report = build_report(command=self.command_name, environment=env,
                              results=results, skipped_categories=skipped)
        path = write_report(report, options.get("report"))
        render_stdout(report, self.stdout.write)
        self.stdout.write(f"report: {path}")
        if exit_code(report):
            raise CommandError(
                f"verification FAILED: {report['envelope']['totals']['fail']} "
                f"red check(s) — findings route per the campaign protocol; "
                f"the engine never fixes.")
