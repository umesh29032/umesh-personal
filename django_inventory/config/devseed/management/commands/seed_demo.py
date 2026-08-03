"""seed_demo — the minimal-plus demo world (SEED-D2)."""

from devseed.management.commands._base import GuardedSeedCommand


class Command(GuardedSeedCommand):
    help = "Seed the demo world (single product journey) into an allowlisted scratch DB."

    def handle(self, *args, **options):
        self.handle_seed("demo", options)
