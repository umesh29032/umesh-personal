"""verify_factory — full dev-world check suite over the seed_factory composite
(the three golden worlds + machines slice; manifest-required)."""

from verification.management.commands._base import DevWorldVerifyCommand


class Command(DevWorldVerifyCommand):
    help = "Verify the seed_factory world against its certified invariants (dev-only, read-only)."
    command_name = "verify_factory"
    scenario_slug = "factory"
