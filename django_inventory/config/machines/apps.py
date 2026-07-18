"""AppConfig for machines — the physical-asset layer of the R10 frozen
production architecture (2026-07-05).

Owns Machine (physical instance) + MachineAssignment (operator possession
windows) ONLY. Stage-domain metadata (MachineType, StageCategory,
Stage.work_type) lives in production beside the Stage library, so the
layering stays acyclic: machines points DOWN at production (string FKs),
production NEVER imports machines. No signals (CLAUDE.md rule #4); all
writes via services.machine_service (single writer).
"""
from django.apps import AppConfig


class MachinesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'machines'
