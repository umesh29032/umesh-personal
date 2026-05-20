"""Stage service — back-compat shim.

Legacy file. Production stages now live in per-stage service files:
  • production/services/layering_service.py
  • production/services/cutting_service.py
  • production/services/_shared.py  (auth helpers)

This file re-exports the same names so older imports continue to work.
New code should import from the per-stage modules directly.
"""
from .layering_service import (   # noqa: F401
    attach_roll_to_layering,
    complete_layering,
    detach_roll_from_layering,
    record_remaining_cloth,
    remove_remaining_cloth,
    save_layering_breakup,
    save_layering_draft,
    start_layering,
    sync_layering_workers_for_skill,
    update_layering_roll_entry,
)
from .cutting_service import complete_cutting   # noqa: F401
