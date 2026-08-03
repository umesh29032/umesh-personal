"""machines models — physical assets + possession windows (R10-A).

Frozen-architecture rules (docs/R10_MACHINE_STAGES_ARCHITECTURE_2026_07_05.md):
  • rule 6: physical machines are ASSETS ONLY — runtime resources; they never
    own workflow, costing, reporting, verification or settlement (zero ₹
    fields here, ever; future MachineRate = separate table + ADR).
  • rule 8: MachineAssignment is the SINGLE owner of possession history —
    append-only windows (end-dated, never deleted), one OPEN holder per
    machine (partial unique), DateTime grain so same-day sharing = sequential
    windows and Σ(end−start) is the future utilization primitive.
Sole writer: services/machine_service.py. Views parse→gate→delegate.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel


class Machine(TimeStampedModel):
    """A physical machine (OL-001…). Identity + status; nothing else.

    `code` is IMMUTABLE once the machine has any assignment (service-enforced,
    the Product.code F1-guard pattern) — codes end up on printed floor labels.
    """

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        MAINTENANCE = 'maintenance', 'Maintenance'

    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=64)
    # String FK downward: machines → production (never the reverse).
    machine_type = models.ForeignKey(
        'production.MachineType', on_delete=models.PROTECT,
        related_name='machines',
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['code']
        constraints = [
            # DB-integrity-PR1 style: status must be a known enum value.
            models.CheckConstraint(
                check=models.Q(status__in=['active', 'inactive', 'maintenance']),
                name='machines_machine_status_enum',
            ),
        ]

    # Status is THE single truth (WP-B lesson: never a second boolean flag).
    @property
    def is_active(self) -> bool:
        return self.status == self.Status.ACTIVE

    def __str__(self):
        return f"{self.code} · {self.name}"


class MachineAssignment(TimeStampedModel):
    """Possession window: WHO holds WHICH machine, from when, optionally for
    which Adda. NULL end_at = currently assigned. Append-only: release =
    end-date, never delete (data-history principle)."""

    machine = models.ForeignKey(
        Machine, on_delete=models.PROTECT, related_name='assignments')
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='machine_assignments')
    adda = models.ForeignKey(
        'production.Adda', null=True, blank=True,
        on_delete=models.PROTECT, related_name='machine_assignments')
    start_at = models.DateTimeField(default=timezone.now)
    end_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-start_at']
        constraints = [
            # ONE open holder per machine — the ≤1-active idiom (WST pattern).
            # Django 5.0.1: partial unique uses condition=.
            models.UniqueConstraint(
                fields=['machine'],
                condition=models.Q(end_at__isnull=True),
                name='machines_one_open_assignment_per_machine',
            ),
            models.CheckConstraint(
                check=models.Q(end_at__isnull=True)
                | models.Q(end_at__gte=models.F('start_at')),
                name='machines_assignment_window_valid',
            ),
        ]

    @property
    def is_open(self) -> bool:
        return self.end_at is None

    def __str__(self):
        state = 'open' if self.is_open else 'closed'
        return f"{self.machine.code} → {self.worker} ({state})"
