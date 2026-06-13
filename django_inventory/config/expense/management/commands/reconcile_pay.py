"""PAY-4 worker-pay reconciliation report.

    env/bin/python config/manage.py reconcile_pay [--adda CODE] [--all]

Prints each completed stage where worker pay doesn't reconcile with the frozen
output, plus a summary. Exits 1 if any HARD defect is found (over-allocation
etc.) so it can run in cron / a pre-deploy check. SOFT flags (the known PAY-2
gap, until allocation is universal in M2.7) are warnings — exit 0.
"""
import sys

from django.core.management.base import BaseCommand

from expense.services import reconcile_stage_pay, reconcile_summarize
from expense.services.reconciliation_service import CLEAN_FLAGS


def _fmt(v):
    return '-' if v is None else str(v)


class Command(BaseCommand):
    help = "Reconcile worker pay vs frozen stage cost (PAY-4); flag unpaid/over-allocated stages."

    def add_arguments(self, parser):
        parser.add_argument('--adda', help='Limit to one Adda code.')
        parser.add_argument('--all', action='store_true', help='Show clean rows too.')

    def handle(self, *args, **opts):
        adda = None
        if opts.get('adda'):
            from production.models import Adda
            adda = Adda.objects.filter(code=opts['adda']).first()
            if adda is None:
                self.stderr.write(self.style.ERROR(f"No Adda with code {opts['adda']!r}"))
                sys.exit(2)

        rows = reconcile_stage_pay(adda=adda)
        shown = rows if opts.get('all') else [r for r in rows if r['flag'] not in CLEAN_FLAGS]

        if shown:
            self.stdout.write(
                f"{'ADDA':<16} {'STAGE':<18} {'COST':>10} {'OUT_QTY':>9} {'ALLOC':>9}  FLAG")
            for r in shown:
                self.stdout.write(
                    f"{r['adda']:<16} {r['stage']:<18} "
                    f"{_fmt(r['processing_cost']):>10} {_fmt(r['output_qty']):>9} "
                    f"{_fmt(r['allocated_qty']):>9}  {r['flag']}")

        s = reconcile_summarize(rows)
        self.stdout.write("")
        self.stdout.write(
            f"Stages: {s['total']}  clean: {s['clean']}  "
            f"soft (PAY-2 gap): {s['soft']}  hard: {s['hard']}")
        for flag, n in sorted(s['counts'].items()):
            self.stdout.write(f"  {flag}: {n}")

        if s['hard'] > 0:
            self.stderr.write(self.style.ERROR(f"{s['hard']} HARD reconciliation defect(s)."))
            sys.exit(1)
