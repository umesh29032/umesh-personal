"""devseed.layers — the spec §2 layer executors (SEED-B: layers 2–6).

Every executor follows the spec §6.3 converge law: get-by-natural-handle →
create-via-the-spec-mapped-writer if absent → verify state matches the
scenario else raise DivergenceError (a divergent world is DRIFT EVIDENCE —
reported, never auto-paved). Executors return {"created": n, "skipped": n}.
"""


class DivergenceError(Exception):
    """Existing handle whose state contradicts the scenario definition —
    the Phase-14 drift interface; the seeder never silently corrects it."""
