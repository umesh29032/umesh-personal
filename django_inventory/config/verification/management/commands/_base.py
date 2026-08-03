"""Shared thin-CLI base for the five verify commands (contract §6.2: commands
are shells; check logic lives in `verification.checks`, reporting in
`verification.report`). Phase-13 CERTIFIED state: all five commands live —
dev-world via `DevWorldVerifyCommand`, production/all via their own handles."""

from django.core.management.base import BaseCommand, CommandError

from verification.guard import gather_and_check
from verification.report import (
    ENGINE_VERSION,
    SPEC_VERSION,
    build_report,
    exit_code,
    render_stdout,
    write_report,
)


class PolarityCommand(BaseCommand):
    command_name = None   # set by subclasses; drives the §6.3 polarity matrix

    def add_arguments(self, parser):
        # Common flags (VER-D5). --skip is explicit-and-reported, never silent.
        parser.add_argument("--report", default=None, metavar="DIR",
                            help="Machine-report directory (default var/verification_reports/).")
        parser.add_argument("--skip", action="append", default=[], metavar="CATEGORY",
                            help="Exclude a check category — recorded in the report envelope.")

    def banner(self):
        self.stdout.write(
            f"verification — engine v{ENGINE_VERSION} · spec v{SPEC_VERSION} "
            f"— command: {self.command_name}")

    def run_polarity(self):
        failures = gather_and_check(self.command_name)
        if failures:
            raise CommandError("POLARITY REFUSED:\n- " + "\n- ".join(failures))

    def handle(self, *args, **options):
        self.banner()
        self.run_polarity()
        # Safety net: every live command overrides handle (or uses
        # DevWorldVerifyCommand). Reaching this = an unwired future command —
        # refuse loudly rather than pretend to verify.
        raise CommandError(
            f"'{self.command_name}' has no wired verification logic "
            f"(polarity PASSED, zero checks run, zero writes possible)."
        )


class DevWorldVerifyCommand(PolarityCommand):
    """verify_demo / verify_factory / verify_feature: manifest-REQUIRED
    (refusal names the seeder — the engine never seeds) → dev-world checks →
    deterministic report → exit code (0 green, nonzero = red count in the
    envelope, surfaced via CommandError)."""

    scenario_slug = None  # verify_feature resolves per-arg

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--manifest-dir", default=None, metavar="DIR",
                            help="Seed-manifest directory (default var/seed_manifests/).")

    def run_verify(self, slug, options):
        from verification.checks.dev_world import run_checks
        from verification.manifests import ManifestMissing, latest_manifest

        try:
            manifest = latest_manifest(slug, options.get("manifest_dir"))
        except ManifestMissing as e:
            raise CommandError(str(e))
        results, skipped = run_checks(slug, manifest,
                                      skip_categories=options.get("skip", []))
        report = build_report(command=self.command_name, environment="dev",
                              results=results, skipped_categories=skipped)
        path = write_report(report, options.get("report"))
        render_stdout(report, self.stdout.write)
        self.stdout.write(f"report: {path}")
        if exit_code(report):
            raise CommandError(
                f"verification FAILED: {report['envelope']['totals']['fail']} "
                f"red check(s) — see the report (findings route per the campaign "
                f"protocol; the engine never fixes).")

    def handle(self, *args, **options):
        self.banner()
        self.run_polarity()
        self.run_verify(self.scenario_slug, options)
