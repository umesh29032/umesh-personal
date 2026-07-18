"""seed_factory — the full three-product factory (SEED-D2)."""

from devseed.management.commands._base import GuardedSeedCommand


class Command(GuardedSeedCommand):
    help = "Seed the full factory (T-SHIRT + LOWER + 3-PATTI worlds) into an allowlisted scratch DB."

    def handle(self, *args, **options):
        self.handle_seed("factory", options)
