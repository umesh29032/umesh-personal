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
                # C-2 (owner-approved 2026-07-06): the value must be one of the
                # schema's OWN options. The worker-scoped schema limits choices to
                # that worker's active allocation, so a forged POST carrying any
                # other PK (unallocated dim — or an unallocated worker, whose
                # option list is empty) is refused HERE at parse time,
                # independent of ENFORCE_ALLOCATION_BOUND.
                if row[f['key']] not in {o['value'] for o in f.get('options', ())}:
                    raise ValidationError(
                        f"{f['label']} is not in your assigned work — "
                        "ask your manager if something is missing.")
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
        # S3: display the payable-good qty (good == reported in the thin slice).
        out.append({'cells': cells, 'quantity': c.good_quantity})
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


def _initial_form_lines(schema):
    """J-2 (owner-approved 2026-07-06): when the worker has NO saved draft yet,
    pre-render one editable row per `schema['initial_lines']` entry (one per
    allocated colour+size pair on a pool stage — the handler owns that list).
    Same spec shape as `_form_lines`, choice values pre-selected, quantities
    empty. Stages without initial_lines keep today's single blank JS row."""
    out = []
    for line in schema.get('initial_lines', []):
        fields = []
        for f in schema['fields']:
            value = line.get(f['key'])
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
        # C-3 (freeze closeout 2026-07-05): assignment alone is not enough
        # either — the LIVE Stage-Access predicate must also admit. Revoking a
        # stage's access in the Access hub closes the report path immediately,
        # even for workers assigned before the revocation. (Management passes
        # inside user_can_access_stage; the existing task truth is untouched.)
        from production.services import user_can_access_stage
        if not user_can_access_stage(request.user, stage_type):
            raise PermissionDenied(
                "Access to this stage has been revoked. Ask your administrator.")
        if not registry.has(stage_type):
            raise PermissionDenied(f"No handler registered for stage '{stage_type}'.")
        handler = registry.get(stage_type)
        # OP-1: worker-scoped schema — a pool stage limits choice options to THIS
        # worker's allocated dims (blind reporting; labels only, no quantities).
        schema = handler.contribution_schema(adda, worker=request.user)
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
        # Pre-Phase-3 B (owner: worker sees their machine): display-only resolve
        # of the worker's open machine assignment — same helper that stamps it.
        from production.services.worker_task_service import _resolve_machine_code
        return render(request, template, {
            'adda': adda, 'stage_record': sr, 'task': task,
            'machine_code': _resolve_machine_code(task),
            'stage_name': sr.workflow_stage.stage.name,
            'stage_type': stage_type,
            'schema': schema,
            'locked': locked,
            'saved_lines': saved,
            # J-2: saved draft wins; otherwise prefill one row per allocated pair.
            'form_lines': [] if locked else (_form_lines(task, schema)
                                             or _initial_form_lines(schema)),
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
            # R8 (spec §3): checklist-mode stages dispatch to the HANDLER —
            # still schema-driven (no stage names here). The handler syncs its
            # verification truth + reports via the same single-writer services.
            if schema.get('mode') == 'checklist':
                handler = registry.get(stage_type)
                # PA-13 lesson: never int() raw key material — tampered
                # 'check-abc' must not 500.
                checked = {int(k[6:]) for k in request.POST
                           if k.startswith('check-') and k[6:].isdigit()}
                handler.checklist_submit(
                    task=task, checked_ids=checked,
                    photos=request.FILES.getlist('photos'),
                    actor=request.user, action=action)
                messages.success(
                    request,
                    "Work report submitted — thank you!" if action == 'submit'
                    else "Progress saved. Submit once every design is verified.")
                return redirect(self._report_url(request, code, stage_type))
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
            # S5/S4-005: non-blocking over-allocation hint (works even with the hard bound off).
            from production.services import bound_soft_warning
            _warn = bound_soft_warning(task)
            if _warn:
                messages.warning(request, _warn)
        except ValidationError as exc:
            messages.error(request, '; '.join(exc.messages))
        except PermissionDenied:
            raise
        return redirect(self._report_url(request, code, stage_type))


class AddaReportReviewView(LoginRequiredMixin, View):
    """P1 (F5-lite): management reviews + corrects quantities for one Adda's
    payable stages BEFORE settlement. Reported stays untouched; verified is the
    correction (settlement reads verified-else-reported). Mobile-first cards."""

    def _gate(self, request):
        from accounts.services import MANAGEMENT_ROLES, user_has_role
        if not user_has_role(request.user, MANAGEMENT_ROLES):
            raise PermissionDenied("Management only.")

    def _rows(self, adda):
        from production.models import WorkerStageContribution, WorkerStageTask
        return list(
            WorkerStageContribution.objects
            .filter(task__stage_record__adda=adda,
                    task__stage_record__workflow_stage__credits_workers=True,
                    task__status__in=(WorkerStageTask.Status.COMPLETED,
                                      WorkerStageTask.Status.VERIFIED))
            .select_related('task__worker', 'color', 'size',
                            'settlement_line__adda_settlement',
                            'task__stage_record__workflow_stage__stage')
            .order_by('task__worker_id', 'pk')
        )

    def get(self, request, code):
        self._gate(request)
        adda = get_object_or_404(Adda, code=code)
        return render(request, 'production/adda_report_review.html',
                      {'adda': adda, 'rows': self._rows(adda)})

    def post(self, request, code):
        from production.services.worker_task_service import (
            set_verified_quantity, void_submitted_report,
        )
        self._gate(request)
        adda = get_object_or_404(Adda, code=code)
        # Pre-Phase-3 D: audited void of a whole submitted report (the explicit
        # path when the TRUE number is HIGHER than submitted — verification only
        # ever confirms/reduces). One action per POST; reason mandatory.
        if request.POST.get('action') == 'void_report':
            from production.models import WorkerStageTask
            try:
                task = get_object_or_404(
                    WorkerStageTask, pk=int(request.POST.get('task_id', 0)),
                    stage_record__adda=adda)
                new_task = void_submitted_report(
                    task, actor=request.user,
                    reason=request.POST.get('reason', ''))
                messages.success(
                    request,
                    f"Report voided — {new_task.worker.get_full_name() or new_task.worker.email} "
                    "can now submit the correct numbers.")
            except (ValidationError, PermissionDenied) as exc:
                messages.error(request, '; '.join(getattr(exc, 'messages', [str(exc)])))
            except (TypeError, ValueError):
                messages.error(request, "Invalid report reference.")
            return redirect(request.path)
        changed = 0
        try:
            for c in self._rows(adda):
                raw = request.POST.get(f'verified_{c.pk}')
                if raw is None:
                    continue
                raw = raw.strip()
                new_val = raw if raw != '' else None
                old_val = c.verified_quantity
                # only write actual changes — keeps logs/updated_at honest
                if str(old_val if old_val is not None else '') == (raw or ''):
                    continue
                set_verified_quantity(c, new_val, actor=request.user)
                changed += 1
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, getattr(exc, 'message', str(exc)))
            return redirect(request.path)
        if changed:
            messages.success(request, f"{changed} quantity correction(s) saved.")
        else:
            messages.info(request, "No changes.")
        return redirect(request.path)
