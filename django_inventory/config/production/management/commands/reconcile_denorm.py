"""reconcile_denorm — verify denormalized counters vs their source (P5.3 / DM-4).

READ-ONLY. Exits 1 if any counter has drifted (so cron/CI can alert). Run:
  env/bin/python config/manage.py reconcile_denorm --settings=config.settings.local
"""
import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Verify denormalized counters against source-of-truth SUMs (read-only)."

    def handle(self, *args, **options):
        from production.services.reconciliation_service import reconcile_denorm
        mismatches = reconcile_denorm()
        if not mismatches:
            self.stdout.write(self.style.SUCCESS("✓ denormalized counters match source"))
            return
        self.stdout.write(self.style.ERROR(f"✗ {len(mismatches)} denorm mismatch(es):"))
        for m in mismatches:
            self.stdout.write(
                f"  {m['model']}#{m['pk']} ({m['adda']}) {m['field']}: "
                f"stored={m['stored']} source={m['source']}"
            )
        sys.exit(1)
