"""VER-A — SEED-D6 single-implementation proof (owner ruling 2026-07-17:
"The assertion library must have exactly one implementation after the move").

Three-way pin: (1) the library lives HERE; (2) devseed consumes THIS module
object (not a copy); (3) exactly one `def run_post_seed` exists anywhere in
the config tree — a fork anywhere = red battery. Plus the spec-version
cross-pin (production-present copy vs devseed's dev-only pin)."""

import os
import re

from django.test import SimpleTestCase

import verification
from verification import assertions as shared


class SharedLibraryTests(SimpleTestCase):
    def test_library_lives_in_verification(self):
        self.assertEqual(shared.run_post_seed.__module__, "verification.assertions")
        self.assertEqual(shared.SeedAssertionError.__module__, "verification.assertions")

    def test_devseed_consumes_the_same_object(self):
        # devseed is importable under dev/test settings (battery runs there);
        # its engine + tests must reference THIS implementation.
        from devseed import core
        self.assertIs(core.run_post_seed, shared.run_post_seed)

    def test_exactly_one_implementation_in_the_tree(self):
        config_root = os.path.dirname(os.path.dirname(verification.__file__))
        hits = []
        for root, dirs, files in os.walk(config_root):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "env", "node_modules")]
            for f in files:
                if not f.endswith(".py"):
                    continue
                path = os.path.join(root, f)
                src = open(path, encoding="utf-8").read()
                if re.search(r"^def run_post_seed\(", src, re.MULTILINE):
                    hits.append(os.path.relpath(path, config_root))
        self.assertEqual(hits, [os.path.join("verification", "assertions.py")],
                         f"run_post_seed implementations found: {hits}")

    def test_old_devseed_module_is_gone(self):
        import devseed
        self.assertFalse(
            os.path.exists(os.path.join(os.path.dirname(devseed.__file__), "assertions.py")),
            "devseed/assertions.py must not exist after the SEED-D6 move")

    def test_spec_version_cross_pin(self):
        # Two constants by structural necessity (devseed is dev-only) — but
        # divergence is drift: this pin keeps them identical forever.
        from devseed.guard import SPEC_VERSION as devseed_pin
        from verification.report import SPEC_VERSION as engine_pin
        self.assertEqual(engine_pin, devseed_pin)
