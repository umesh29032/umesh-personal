"""verify_feature <slug> — scenario-scoped dev-world checks (slug validated
against the devseed scenario registry AFTER polarity — devseed is structurally
absent under production settings, where this command refuses anyway)."""

from django.core.management.base import CommandError

from verification.management.commands._base import DevWorldVerifyCommand


class Command(DevWorldVerifyCommand):
    help = "Verify one seeded feature world against its certified invariants (dev-only, read-only)."
    command_name = "verify_feature"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("feature_slug", help="Scenario slug from the devseed registry.")

    def handle(self, *args, **options):
        self.banner()
        self.run_polarity()
        from verification.checks.dev_world import feature_slug_failure
        slug = options["feature_slug"]
        failure = feature_slug_failure(slug)
        if failure:
            raise CommandError(failure)
        self.run_verify(slug, options)
