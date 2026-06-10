"""V2-1c-iii pt.2b — worker self-report view (schema-driven, stage-agnostic).

The ONLY worker-facing write surface for WorkerStageContribution. Renders from
`StageHandler.contribution_schema(adda)` (open-closed: no stage-name conditionals
here — adding a stage needs NO edit to this file) and persists through the two
existing single-writer services: `save_draft_contributions` (replace-semantics
draft) + `complete_worker_task` (freeze + lock). No money is shown (Option B) and
no other worker's data is reachable (isolation: the view resolves ONLY the
requesting user's own task).
"""
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin

from production.models import Adda, AddaStageRecord, WorkerStageTask
from production.services.worker_task_service import (
    complete_worker_task, save_draft_contributions,
)
from production.stages.base import registry

logger = logging.getLogger('production')

# Schema `key` → the model column it maps to is 1:1 today (color_id / size_id /
# reported_quantity / bundle_item_id). Future stage-specific keys map into the
# deferred `attributes` JSONB (V2_FOUNDATION_REVIEW F1) — parsing below is
# schema-keyed so that lands without touching this view.


def _parse_lines(post, schema):
    """Parse POSTed contribution lines BY SCHEMA KEYS (never hardcoded field
    names — the anti-overfit rule from P2_SCHEMA_RENDER_VALIDATION §0).

    Inputs are named `line-<i>-<key>`; `line-count` bounds the scan. Rows with no
    quantity value are treated as empty and skipped (workers leave blank lines).
    """
    try:
        count = int(post.get('line-count', 0))
    except (TypeError, ValueError):
        count = 0
    count = max(0, min(count, 200))   # sanity bound — worker form, not an import

    qty_keys = [f['key'] for f in schema['fields'] if f['kind'] == 'quantity']
    lines = []
    for i in range(count):
        row, has_qty = {}, False
        for f in schema['fields']:
            raw = (post.get(f"line-{i}-{f['key']}") or '').strip()
            if raw == '':
                continue
            if f['kind'] == 'choice':
                # choice values are PKs — int() guards against tampered input.
                try:
                    row[f['key']] = int(raw)
                except (TypeError, ValueError):
                    raise ValidationError(f"Invalid value for {f['label']}.")
            else:
                row[f['key']] = raw
                if f['key'] in qty_keys:
                    has_qty = True
        if not row or not has_qty:
            continue   # blank line — skip silently
        for f in schema['fields']:
            if f.get('required') and f['key'] not in row:
                raise ValidationError(
                    f"Line {len(lines) + 1}: {f['label']} is required.")
        lines.append(row)
    return lines


def _display_lines(task, schema):
    """Resolve saved contribution rows back through the schema for rendering
    (choice PK → label/swatch). Schema-keyed: works for ANY stage's field set."""
    option_maps = {
        f['key']: {str(o['value']): o for o in f.get('options', [])}
        for f in schema['fields'] if f['kind'] == 'choice'
    }
    out = []
    for c in task.contributions.all().order_by('pk'):
        cells = []
        for f in schema['fields']:
            # Column keys resolve via getattr (color_id / size_id / qty…); future
            # JSONB keys would fall back to c.attributes — additive, not built.
            raw = getattr(c, f['key'], None)
            if raw is None:
                continue
            if f['kind'] == 'choice':
                opt = option_maps.get(f['key'], {}).get(str(raw), {})
                cells.append({'kind': 'choice', 'key': f['key'], 'value': raw,
                              'label': opt.get('label', f"#{raw}"),
                              'swatch': opt.get('swatch', '')})
            else:
                cells.append({'kind': 'quantity', 'key': f['key'], 'value': raw,
                              'unit': f.get('unit', '')})
        out.append({'cells': cells, 'quantity': c.reported_quantity})
    return out


def _form_lines(task, schema):
    """Render-ready structure for the EDITABLE state: one entry per saved draft
    line, each field carrying its current value (+ per-option `selected` for
    choices) so the template stays a dumb schema loop."""
    out = []
    for c in task.contributions.all().order_by('pk'):
        fields = []
        for f in schema['fields']:
            value = getattr(c, f['key'], None)
            spec = {'key': f['key'], 'kind': f['kind'], 'label': f['label'],
                    'required': f.get('required', False),
                    'unit': f.get('unit', ''), 'value': value}
            if f['kind'] == 'choice':
                spec['options'] = [dict(o, selected=(str(o['value']) == str(value)))
                                   for o in f.get('options', [])]
            fields.append(spec)
        out.append(fields)
    return out


class WorkerReportView(LoginRequiredMixin, View):
    """GET = render the worker's report form (editable or locked); POST = save
    draft / submit & complete. Object-level isolation: resolves the requesting
    user's OWN non-cancelled task or 403 — managers correct via verified_quantity
    later (owner decision D6), they don't use this surface."""

    @method_decorator(xframe_options_sameorigin)   # ?embedded=1 iframes from the dashboard
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    # ── shared resolution ────────────────────────────────────────────────
    def _resolve(self, request, code, stage_type):
        adda = get_object_or_404(Adda, code=code)
        sr = get_object_or_404(
            AddaStageRecord.objects.select_related('workflow_stage__stage', 'adda__product'),
            adda=adda, workflow_stage__stage__code=stage_type)
        task = (WorkerStageTask.objects
                .filter(stage_record=sr, worker=request.user)
                .exclude(status=WorkerStageTask.Status.CANCELLED)
                .first())
        if task is None:
            # Isolation rule (V2-1c-iv): skill alone is not enough — you report
            # only on stages you are actively assigned to.
            raise PermissionDenied("You are not assigned to this stage.")
        if not registry.has(stage_type):
            raise PermissionDenied(f"No handler registered for stage '{stage_type}'.")
        handler = registry.get(stage_type)
        schema = handler.contribution_schema(adda)
        return adda, sr, task, schema

    def _report_url(self, request, code, stage_type):
        from django.urls import reverse
        url = reverse('production:worker-report', args=[code, stage_type])
        if request.GET.get('embedded') == '1':
            url += '?embedded=1'
        return url

    # ── GET ──────────────────────────────────────────────────────────────
    def get(self, request, code, stage_type):
        adda, sr, task, schema = self._resolve(request, code, stage_type)
        locked = task.status in (WorkerStageTask.Status.COMPLETED,
                                 WorkerStageTask.Status.VERIFIED)
        saved = _display_lines(task, schema)
        embedded = request.GET.get('embedded') == '1'
        template = ('production/worker_report_embedded.html' if embedded
                    else 'production/worker_report.html')
        return render(request, template, {
            'adda': adda, 'stage_record': sr, 'task': task,
            'stage_name': sr.workflow_stage.stage.name,
            'stage_type': stage_type,
            'schema': schema,
            'locked': locked,
            'saved_lines': saved,
            'form_lines': [] if locked else _form_lines(task, schema),
            'total_quantity': sum((l['quantity'] for l in saved), start=0),
            'embedded': embedded,
        })

    # ── POST ─────────────────────────────────────────────────────────────
    def post(self, request, code, stage_type):
        adda, sr, task, schema = self._resolve(request, code, stage_type)
        action = request.POST.get('action')
        try:
            if action not in ('draft', 'submit'):
                raise ValidationError("Unknown action.")
            lines = _parse_lines(request.POST, schema)
            if action == 'submit' and not lines:
                raise ValidationError("Add at least one line before submitting.")
            # Both actions persist via the SAME single-writer services — the view
            # never touches WorkerStageContribution directly (ADR 0001 discipline).
            save_draft_contributions(task, lines, actor=request.user)
            if action == 'submit':
                complete_worker_task(task, actor=request.user)
                messages.success(request, "Work report submitted — thank you!")
            else:
                messages.success(request, "Draft saved. You can keep editing until you submit.")
        except ValidationError as exc:
            messages.error(request, '; '.join(exc.messages))
        except PermissionDenied:
            raise
        return redirect(self._report_url(request, code, stage_type))
