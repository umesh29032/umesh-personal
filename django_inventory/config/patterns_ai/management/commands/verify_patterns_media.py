"""Integrity sweep for patterns_ai knowledge media (ADR-G; readiness N-7).

DB↔disk verification: every non-retired CaptureAsset's file must exist and
hash to its recorded sha256. Failures → status=corrupt (row+file kept — a
corrupt original is still evidence). Files on disk WITHOUT a row are reported
as WARN-with-context (N-7: rollback orphans are NOT corruption).
"""
import pathlib

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Verify checksums of all capture originals; report orphans (WARN).'

    def handle(self, *args, **options):
        from patterns_ai.models import CaptureAsset
        from patterns_ai.services import capture_service

        checked = corrupt = missing = 0
        known_paths = set()
        for asset in CaptureAsset.objects.exclude(
                status=CaptureAsset.Status.RETIRED).iterator():
            known_paths.add(asset.file.name)
            state, detail = capture_service.verify_asset(asset)
            checked += 1
            if state == 'ok':
                continue
            if state == 'missing':
                missing += 1
            else:
                corrupt += 1
            capture_service.mark_corrupt(asset=asset, detail=detail)
            self.stderr.write(self.style.ERROR(
                f'ASSET {asset.pk}: {state} — {detail}'))
        # retired assets keep their files; count them as known so they are
        # never reported as orphans.
        for name in CaptureAsset.objects.filter(
                status=CaptureAsset.Status.RETIRED).values_list('file', flat=True):
            known_paths.add(name)

        root = pathlib.Path(settings.MEDIA_ROOT) / 'patterns_ai'
        orphans = []
        if root.exists():
            for f in root.rglob('*'):
                if f.is_file():
                    rel = str(f.relative_to(settings.MEDIA_ROOT))
                    if '/derived/' in rel:
                        continue   # ADR-G derived class: regenerable, never an orphan
                    if rel not in known_paths:
                        orphans.append(rel)
        for o in orphans:
            self.stdout.write(self.style.WARNING(
                f'ORPHAN (not corruption — likely rolled-back block, N-7): {o}'))

        self.stdout.write(self.style.SUCCESS(
            f'sweep: checked={checked} corrupt={corrupt} missing={missing} '
            f'orphans={len(orphans)}'))
