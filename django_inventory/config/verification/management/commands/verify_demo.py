"""verify_demo — full dev-world check suite over the seed_demo world
(manifest-required; the engine NEVER seeds)."""

from verification.management.commands._base import DevWorldVerifyCommand


class Command(DevWorldVerifyCommand):
    help = "Verify the seed_demo world against its certified invariants (dev-only, read-only)."
    command_name = "verify_demo"
    scenario_slug = "demo"
