"""machine_service — THE sole writer of Machine + MachineAssignment (R10-A).

Frozen-architecture single-writer discipline (CLAUDE.md rule 5): every write
to the two machines tables happens HERE. Views parse→gate→delegate. Zero
money: this module must never import expense/settlement/rate modules
(grep-pinned in tests — frozen rule 6).
"""
import logging

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from machines.models import Machine, MachineAssignment

logger = logging.getLogger(__name__)


# ── reads (shared querysets) ─────────────────────────────────────────────────

def machines_with_holder():
    """Register queryset: machines + their OPEN assignment (0 or 1 each)."""
    return (
        Machine.objects
        .select_related('machine_type')
        .prefetch_related(
            # Only the open window — the list shows the CURRENT holder.
            # (Prefetch of a filtered reverse FK: joined in Python, no N+1.)
        )
    )


def open_assignment_for(machine):
    return (
        machine.assignments
        .select_related('worker', 'adda')
        .filter(end_at__isnull=True)
        .first()
    )


def register_counts() -> dict:
    """The PDD §25 'admin dashboard counts' — bounded aggregate reads."""
    from django.db.models import Count, Q
    by_status = Machine.objects.aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status=Machine.Status.ACTIVE)),
        maintenance=Count('id', filter=Q(status=Machine.Status.MAINTENANCE)),
    )
    by_status['assigned_now'] = MachineAssignment.objects.filter(
        end_at__isnull=True).count()
    return by_status


# ── writes (single door) ─────────────────────────────────────────────────────

def create_machine_type(*, name: str, user=None):
    """Create a MachineType (production-owned config master; THIS is its one
    service writer — explicit downward cross-app write, machines→production).
    Code auto-slugs from the name ('Overlock Machine' → 'overlock_machine')."""
    from django.utils.text import slugify
    from production.models import MachineType
    name = (name or '').strip()
    if not name:
        raise ValidationError("Machine type name is required.")
    code = slugify(name).replace('-', '_')[:32]
    mt, created = MachineType.objects.get_or_create(
        code=code, defaults={'name': name})
    if created:
        logger.info("machine_type.create code=%s by=%s", code, getattr(user, 'pk', None))
    return mt

def create_machine(*, code: str, name: str, machine_type, status='active',
                   notes: str = '', user=None) -> Machine:
    code = (code or '').strip()
    if not code:
        raise ValidationError("Machine code is required.")
    if Machine.objects.filter(code__iexact=code).exists():
        raise ValidationError(f"Machine code '{code}' already exists.")
    m = Machine.objects.create(
        code=code, name=name.strip(), machine_type=machine_type,
        status=status, notes=notes)
    logger.info("machine.create code=%s type=%s by=%s",
                m.code, machine_type.code, getattr(user, 'pk', None))
    return m


def update_machine(machine: Machine, *, name=None, machine_type=None,
                   status=None, notes=None, code=None, user=None) -> Machine:
    if code is not None:
        # MGT-F-1: compare against the DB row, NOT machine.code — a bound
        # ModelForm(instance=machine) mutates the in-memory instance during
        # is_valid() (Django construct_instance), which made this guard
        # compare new-vs-new and silently skip.
        db_code = Machine.objects.only('code').get(pk=machine.pk).code
        if code.strip() != db_code:
            # F1-guard pattern: printed floor labels — immutable once used.
            if machine.assignments.exists():
                raise ValidationError(
                    "Machine code is immutable once the machine has assignment "
                    "history (floor labels reference it). Create a new machine instead.")
            if Machine.objects.filter(code__iexact=code.strip()).exclude(pk=machine.pk).exists():
                raise ValidationError(f"Machine code '{code}' already exists.")
        machine.code = code.strip()
    if name is not None:
        machine.name = name.strip()
    if machine_type is not None:
        machine.machine_type = machine_type
    if status is not None:
        if status not in Machine.Status.values:
            raise ValidationError(f"Unknown status '{status}'.")
        machine.status = status
    if notes is not None:
        machine.notes = notes
    machine.save()
    logger.info("machine.update pk=%s by=%s", machine.pk, getattr(user, 'pk', None))
    return machine


@transaction.atomic
def assign(*, machine: Machine, worker, adda=None, start_at=None,
           user=None) -> MachineAssignment:
    """Open a possession window. Refuses when one is already open — the
    manager releases first (actionable error names the current holder)."""
    if machine.status != Machine.Status.ACTIVE:
        raise ValidationError(
            f"{machine.code} is {machine.get_status_display()} — set it "
            "Active before assigning.")
    current = open_assignment_for(machine)
    if current is not None:
        raise ValidationError(
            f"{machine.code} is currently with "
            f"{current.worker.get_full_name() or current.worker.email} "
            f"(since {timezone.localtime(current.start_at):%d %b %H:%M}). "
            "Release it first.")
    try:
        a = MachineAssignment.objects.create(
            machine=machine, worker=worker, adda=adda,
            start_at=start_at or timezone.now())
    except IntegrityError:
        # Race backstop: the partial-unique index caught a concurrent assign.
        raise ValidationError(
            f"{machine.code} was assigned by someone else a moment ago — refresh.")
    logger.info("machine.assign machine=%s worker=%s adda=%s by=%s",
                machine.code, worker.pk, getattr(adda, 'code', None),
                getattr(user, 'pk', None))
    return a


def release(assignment: MachineAssignment, *, end_at=None, user=None) -> MachineAssignment:
    if assignment.end_at is not None:
        raise ValidationError("This assignment is already released.")
    end = end_at or timezone.now()
    if end < assignment.start_at:
        raise ValidationError("Release time cannot be before the start time.")
    assignment.end_at = end
    assignment.save(update_fields=['end_at', 'updated_at'])
    logger.info("machine.release machine=%s worker=%s by=%s",
                assignment.machine.code, assignment.worker_id,
                getattr(user, 'pk', None))
    return assignment
