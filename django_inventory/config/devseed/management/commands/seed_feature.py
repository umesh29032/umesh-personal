"""seed_feature <slug> — per-feature scenario slices (SEED-D7: slug validated
against the registry; unknown slug lists valid ones and exits nonzero)."""

from django.core.management.base import CommandError

from devseed.management.commands._base import GuardedSeedCommand
from devseed.scenarios import SCENARIOS, valid_slugs


class Command(GuardedSeedCommand):
    help = "Seed a self-contained feature scenario into an allowlisted scratch DB."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("feature_slug", help="Scenario slug from the registry.")

    def handle(self, *args, **options):
        slug = options["feature_slug"]
        # Slug validation FIRST (CLI usability): unknown slug = its own error class.
        if slug not in SCENARIOS:
            raise CommandError(
                f"Unknown scenario '{slug}'. Valid slugs:\n  " + "\n  ".join(valid_slugs())
            )
        self.handle_seed(slug, options)
