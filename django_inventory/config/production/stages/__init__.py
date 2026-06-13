"""Per-stage packages for the production stage engine (M2).

Each manufacturing stage lives in its own subpackage — production/stages/<stage>/
with handler.py (+ service.py, views.py, models.py) — mirroring the shop floor.
The framework (StageHandler contract + registry) lives in stages/base/.

Adding a stage = drop a folder whose handler.py self-registers; the registry
autodiscovers it. See docs/TARGET_ARCHITECTURE.md.
"""
