"""S5 / S4-005 — allocation-bound pre-flip audit.

    env/bin/python config/manage.py preview_allocation_bound [--adda CODE]

Lists every COMPLETED contribution that WOULD fail the allocation bound if
ENFORCE_ALLOCATION_BOUND were enabled (over-bound or unallocated), on pool-participant
stages. Exit 1 if any violation is found (cron / pre-flip gate); exit 0 when clean.
RUN THIS + clear violations BEFORE turning ENFORCE_ALLOCATION_BOUND on.
"""
import sys

from django.core.management.base import BaseCommand

from production.services import preview_bound_violations


class Command(BaseCommand):
    help = "Preview allocation-bound violations before enabling ENFORCE_ALLOCATION_BOUND."

    def add_arguments(self, parser):
        parser.add_argument('--adda', help='Scope to one Adda code (default: all).')

    def handle(self, *args, **opts):
        adda = None
        if opts.get('adda'):
            from production.models import Adda
            adda = Adda.objects.filter(code=opts['adda']).first()
            if adda is None:
                self.stderr.write(f"No Adda with code {opts['adda']!r}.")
                sys.exit(2)

        violations = preview_bound_violations(adda=adda)
        if not violations:
            self.stdout.write(self.style.SUCCESS(
                "Clean — no allocation-bound violations. Safe to enable ENFORCE_ALLOCATION_BOUND."))
            return
        self.stdout.write(self.style.WARNING(
            f"{len(violations)} allocation-bound violation(s) — resolve BEFORE enabling enforcement:"))
        for v in violations:
            self.stdout.write(
                f"  [{v['kind']}] adda={v['adda']} stage={v['stage']} worker={v['worker_id']} "
                f"colour={v['color_id']} size={v['size_id']} reported={v['reported']} "
                f"allocated={v['allocated']}")
        sys.exit(1)
