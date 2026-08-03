"""Pattern Design stage handler (code: cutting_pattern) — thin adapter over cutting_pattern_service (M2.3).

Adapter-first: delegates to the existing service; behavior identical. Code moves
into this package only after dispatch is migrated and proven (post-M2.6).
"""
from __future__ import annotations

from production.constants import STAGE_CUTTING_PATTERN
from production.stages.base import CompletionResult, ReopenResult, StageHandler, register

# Phase 8B (owner-approved dependency inversion — the ARCHIVE_VALIDATORS
# pattern): patterns_ai registers a READ-ONLY provider in its apps.ready();
# production consumes plain dicts, never modules (ADR-H wall intact).
# Contract: LAYOUT_PROVIDER(adda) -> {'has_usage': bool, 'choose_url': str,
# 'groups': [{...display facts...}]} or None. Errors must never break the
# stage page (callers wrap).
LAYOUT_PROVIDER = None


@register
class CuttingPatternHandler(StageHandler):
    code = STAGE_CUTTING_PATTERN
    name = 'Pattern Design'   # display name (C-2 rename 2026-07-05); code stays 'cutting_pattern'
    template_partial = 'production/_stage_panel_cutting_pattern.html'

    def snapshot(self, adda):
        from production.services import get_pattern_snapshot
        return get_pattern_snapshot(adda)

    def admin_snapshot(self, adda):
        # R8 generic snapshot: Pattern Design's output as a management
        # reference for the NEXT stage (Cutting): designs done, per-design
        # verified state, sizes, photos, lead time. LIVE reads only.
        from production.services import get_pattern_snapshot
        snap = get_pattern_snapshot(adda)
        if snap['state'] in ('absent', 'not_started'):
            return None
        record = snap['record']
        verified_ids = set()
        if record:
            verified_ids = set(record.verifications.values_list('assignment_id', flat=True))
        design_rows = [
            (f"{a.pattern.name} × {a.pieces_count}",
             '✓ verified' if a.pk in verified_ids else 'pending')
            for a in adda.product.pattern_assignments.select_related('pattern')
        ]
        totals = [
            ('Designs verified',
             f"{snap['verified_count']} / {snap['expected_pattern_count']}"),
            ('Size allocation', f"{snap['allocation_sum_pct']}%"),
            ('Photos', snap['photo_count']),
        ]
        if record is not None and getattr(record, 'lead_minutes_from_layering', None) is not None:
            totals.append(('Lead time since Layering',
                           f"{record.lead_minutes_from_layering} min"))
        sections = [{'label': 'Progress', 'rows': totals}]
        if design_rows:
            sections.append({'label': 'Pattern designs', 'rows': design_rows})
        return {'title': 'Pattern Design — reference', 'sections': sections}

    def panel_context(self, request, adda, record):
        from production.views.pattern_stage_views import _build_pattern_context
        return _build_pattern_context(request, adda)

    def contribution_schema(self, adda, worker=None):
        # R8 (spec §3/§5): the pattern master's report is a VERIFICATION
        # CHECKLIST of the product's Pattern Designs — no quantities asked.
        # `mode='checklist'` switches the worker report view/template to the
        # checklist branch (still schema-driven, no stage-name conditionals
        # there). One contribution (qty=1) books the FIXED per-Adda pay.
        from production.models import AddaStageRecord
        sr = (AddaStageRecord.objects
              .filter(adda=adda, workflow_stage__stage__code=self.code)
              .first())
        record = getattr(sr, 'cutting_pattern', None) if sr else None
        verified_ids = set(
            record.verifications.values_list('assignment_id', flat=True)
        ) if record else set()
        items = []
        for a in adda.product.pattern_assignments.select_related('pattern'):
            image = ''
            if a.pattern.reference_image:
                try:
                    image = a.pattern.reference_image.url
                except ValueError:
                    image = ''
            items.append({'assignment_id': a.pk,
                          'label': f"{a.pattern.name} × {a.pieces_count}",
                          'image': image,
                          'verified': a.pk in verified_ids})
        return {
            'line_label': 'design',
            'mode': 'checklist',
            'allow_photos': True,
            'checklist': items,
            'fields': [
                # Engine-compatibility field: the checklist submit reports ONE
                # line qty=1 through the normal chokepoint (fixed pay = rate×1).
                {'key': 'reported_quantity', 'kind': 'quantity',
                 'label': 'Job completed', 'required': True, 'unit': 'job'},
            ],
        }

    def checklist_submit(self, *, task, checked_ids, photos, actor, action):
        """R8: sync the SAME verification rows the operator console writes
        (single truth, owner C-3) via the existing skill-gated service fns,
        then report through the C-TM chokepoint (fixed pay). `action`:
        'draft' = save ticks/photos only · 'submit' = require ALL designs
        ticked → one contribution qty=1 → complete (freeze)."""
        from django.core.exceptions import ValidationError
        from production.services.worker_task_service import (
            complete_worker_task, save_draft_contributions)
        from .service import (
            attach_photo, ensure_pattern_record, unverify_pattern,
            verify_pattern)

        adda = task.stage_record.adda
        sr = task.stage_record
        assignments = list(adda.product.pattern_assignments.select_related('pattern'))
        valid_ids = {a.pk for a in assignments}
        if not valid_ids:
            raise ValidationError(
                "This product has no Pattern Designs configured — ask a "
                "manager to add them before reporting.")
        bad = set(checked_ids) - valid_ids
        if bad:
            raise ValidationError("Unknown pattern design in the checklist.")

        record = ensure_pattern_record(stage_record=sr, user=actor)
        for photo in photos:
            attach_photo(stage_record=sr, uploaded_image=photo, user=actor)
        for a in assignments:
            if a.pk in checked_ids:
                verify_pattern(record=record, assignment=a, user=actor)
            else:
                unverify_pattern(record=record, assignment=a, user=actor)

        if action == 'submit':
            missing = [a.pattern.name for a in assignments
                       if a.pk not in checked_ids]
            if missing:
                raise ValidationError(
                    f"Verify every design before submitting — pending: "
                    f"{', '.join(missing)}.")
            save_draft_contributions(task, [{'reported_quantity': '1'}],
                                     actor=actor)
            complete_worker_task(task, actor=actor)

    def start(self, *, user_id, adda, record, data):
        from accounts.models import User
        from production.services import start_pattern_stage
        return start_pattern_stage(
            adda=adda, worker_ids=data.get('worker_ids', []),
            user=User.objects.get(pk=user_id))

    def complete(self, *, user_id, adda, record, data):
        from accounts.models import User
        from production.services import complete_pattern_stage
        complete_pattern_stage(adda=adda, user=User.objects.get(pk=user_id))
        return CompletionResult()

    def reopen(self, *, user_id, record):
        from accounts.models import User
        from production.services import reopen_pattern_stage
        reopen_pattern_stage(adda=record.adda, user=User.objects.get(pk=user_id))
        return ReopenResult()

    def cost_quantity(self, record):
        # Verification stage — no per-unit quantity. None = unpriced (NULL), not 0.
        return None
