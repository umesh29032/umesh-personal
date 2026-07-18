"""patterns_ai_health — the ops truth command (P5 §3).

Cron-friendly: exit 0 = healthy, 1 = degraded (each finding printed).
Checks runtime availability, node, media writability, integrity summary,
knowledge census, pending suggestions. READ-ONLY except a throwaway
media-write probe.
"""
import shutil

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Pattern Intelligence operational health check (exit 1 on degraded).'

    def handle(self, *args, **options):
        from patterns_ai.models import (CalibrationMat, CaptureAsset,
                                        Marker, MarkerOutcome,
                                        PieceSizeGeometry, SuggestionEvent)
        from patterns_ai.services import capture_service, compute_bridge

        problems = []

        def ok(label, detail=''):
            self.stdout.write(f'  OK   {label}' + (f' — {detail}' if detail else ''))

        def bad(label, detail):
            problems.append(label)
            self.stdout.write(self.style.ERROR(f'  FAIL {label} — {detail}'))

        self.stdout.write('patterns_ai health:')

        # 1. compute runtime (ADR-F)
        if compute_bridge.runtime_available():
            ok('compute venv', str(compute_bridge.compute_dir()))
        else:
            bad('compute venv', 'missing — rebuild per compute/patterns_ai/README.md')
        for tool, script in sorted(compute_bridge.TOOLS.items()):
            if (compute_bridge.compute_dir() / script).exists():
                ok(f'tool {tool}', script)
            else:
                bad(f'tool {tool}', f'{script} missing')

        # 2. node (svgnest primary engine; absence = degraded, BLF floor remains)
        node = shutil.which('node')
        if node:
            ok('node runtime', node)
        else:
            bad('node runtime', 'missing — svgnest unavailable (BLF floor only)')

        # 3. media writability (derived-class probe; knowledge untouched)
        probe = 'patterns_ai/_healthprobe/probe.txt'
        try:
            default_storage.save(probe, ContentFile(b'ok'))
            default_storage.delete(probe)
            ok('media storage writable')
        except Exception as exc:                      # noqa: BLE001 - ops surface
            bad('media storage', str(exc))

        # 4. integrity summary (verify honestly, like the sweep)
        assets = CaptureAsset.objects.exclude(status=CaptureAsset.Status.RETIRED)
        corrupt = 0
        missing = 0
        for asset in assets:
            state, _ = capture_service.verify_asset(asset)
            if state == 'mismatch':
                corrupt += 1
            elif state == 'missing':
                missing += 1
        if corrupt or missing:
            bad('media integrity', f'corrupt={corrupt} missing={missing} '
                                   '(run verify_patterns_media for detail)')
        else:
            ok('media integrity', f'{assets.count()} asset(s) verified')

        # 5. knowledge census + attention items
        ok('census',
           f'markers={Marker.objects.count()} '
           f'outcomes={MarkerOutcome.objects.count()} '
           f'geometry={PieceSizeGeometry.objects.count()} '
           f'mats_active={CalibrationMat.objects.filter(status="active").count()}')
        pending = SuggestionEvent.objects.filter(outcome='offered').count()
        if pending:
            ok('suggestions pending decision', str(pending))

        if problems:
            self.stdout.write(self.style.ERROR(
                f'DEGRADED: {len(problems)} problem(s): ' + ', '.join(problems)))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS('HEALTHY'))
