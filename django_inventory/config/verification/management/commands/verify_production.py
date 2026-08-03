"""verify_production — the production-safe subset ONLY (VER-D3): SELECT/
aggregate + settings/migration introspection; no request cycle, no sessions,
no logins, no writes. Runs EVERYWHERE (a dev run = pre-deploy rehearsal:
same checks, contamination reported informationally)."""

from django.core.management.base import CommandError

from verification.guard import environment
from verification.management.commands._base import PolarityCommand
from verification.report import build_report, exit_code, render_stdout, write_report


class Command(PolarityCommand):
    help = ("Verify production-safe invariants: DEV-contamination · flags-vs-declaration · "
            "migrations · integrity self-consistency (read-only).")
    command_name = "verify_production"

    def handle(self, *args, **options):
        self.banner()
        self.run_polarity()
        from verification.checks.production import run_production_checks
        env = environment()
        skip = options.get("skip", [])
        results = run_production_checks(env, skip_categories=skip)
        report = build_report(command=self.command_name, environment=env,
                              results=results, skipped_categories=sorted(set(skip)))
        path = write_report(report, options.get("report"))
        render_stdout(report, self.stdout.write)
        self.stdout.write(f"report: {path}")
        if exit_code(report):
            raise CommandError(
                f"verification FAILED: {report['envelope']['totals']['fail']} "
                f"red check(s) — findings route per the campaign protocol; "
                f"the engine never fixes.")
