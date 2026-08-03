"""Allocation-bound legacy-row audit.

    env/bin/python config/manage.py preview_allocation_bound [--adda CODE]

The allocation bound is now always-on, so new completions can't violate it. This lists any
PRE-EXISTING COMPLETED contribution (created before the bound went hard) that would fail it
(over-bound or unallocated), on pool-participant stages. Exit 1 if any is found; exit 0 clean.
"""
import sys

from django.core.management.base import BaseCommand

from production.services import preview_bound_violations


class Command(BaseCommand):
    help = "Audit pre-existing completed rows that violate the (always-on) allocation bound."

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
                "Clean — no legacy allocation-bound violations."))
            return
        self.stdout.write(self.style.WARNING(
            f"{len(violations)} legacy allocation-bound violation(s) — pre-existing completed rows:"))
        for v in violations:
            self.stdout.write(
                f"  [{v['kind']}] adda={v['adda']} stage={v['stage']} worker={v['worker_id']} "
                f"colour={v['color_id']} size={v['size_id']} reported={v['reported']} "
                f"allocated={v['allocated']}")
        sys.exit(1)
