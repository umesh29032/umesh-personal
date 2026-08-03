"""V2-1c-iii pt.2b — worker self-report view (schema-driven, stage-agnostic).

Also hosts MyAssignedWorkView (AE-3): the worker's "My Assigned Work" bundle dashboard.
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
                # option list is empty) is refused HERE at parse time.
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
        # AE-1 gap-E: the (colour,size) PAIR must be one the worker was actually
        # allocated — flat per-field option checks above pass Red + XL separately
        # even if Red/XL was never a pair. Generic: only fires when the schema
        # declares pair_keys + allowed_pairs (dimensioned pool stages).
        allowed_pairs = schema.get('allowed_pairs')
        pair_keys = schema.get('pair_keys') or []
        if allowed_pairs is not None and pair_keys:
            pair = tuple(row.get(k) for k in pair_keys)
            if pair not in set(allowed_pairs):
                raise ValidationError(
                    f"Line {len(lines) + 1}: this colour+size combination is not "
                    "in your assigned work — ask your manager if something is missing.")
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


def _form_lines(task, schema, contribs=None):
    """Render-ready structure for the EDITABLE state: one entry per saved draft
    line, each field carrying its current value (+ per-option `selected` for
    choices) so the template stays a dumb schema loop. `contribs` overrides the
    source rows (AE-3 single-bundle mode passes ONLY the scoped bundle's lines)."""
    out = []
    for c in (contribs if contribs is not None else task.contributions.all().order_by('pk')):
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
        # P19A C-2 fix (2026-07-20): pre-production stages carry ONE SR PER LANE
        # (streams redesign), so the old single-row .get() raised
        # MultipleObjectsReturned → 500 on every multi-lane Adda, before the
        # permission check. Resolve lane-aware: the worker's OWN task picks the
        # SR; an optional ?stream=<id> narrows explicitly (URLs today don't
        # carry the lane). Single-lane behaviour is byte-identical.
        srs = list(
            AddaStageRecord.objects
            .select_related('workflow_stage__stage', 'adda__product')
            .filter(adda=adda, workflow_stage__stage__code=stage_type)
            .order_by('stream_id'))
        if not srs:
            from django.http import Http404
            raise Http404("Stage has not started for this Adda.")
        stream_raw = request.POST.get('stream') or request.GET.get('stream') or ''
        if stream_raw.isdigit():
            srs = [s for s in srs if s.stream_id == int(stream_raw)]
            if not srs:
                from django.http import Http404
                raise Http404("No such lane on this stage.")
        tasks = list(
            WorkerStageTask.objects
            .filter(stage_record__in=srs, worker=request.user)
            .exclude(status=WorkerStageTask.Status.CANCELLED)
            .order_by('stage_record__stream_id', 'pk'))
        # Prefer a lane the worker can still act on; else the first (locked view).
        open_states = (WorkerStageTask.Status.ASSIGNED,
                       WorkerStageTask.Status.IN_PROGRESS)
        task = next((t for t in tasks if t.status in open_states),
                    tasks[0] if tasks else None)
        if task is None:
            # Isolation rule (V2-1c-iv): skill alone is not enough — you report
            # only on stages you are actively assigned to.
            raise PermissionDenied("You are not assigned to this stage.")
        sr = next(s for s in srs if s.pk == task.stage_record_id)
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
        # AE-3: single-bundle scope — when the "My Assigned Work" card opens ONE
        # bundle (?color=&size=), lock the schema to that pair so the worker never
        # picks colour/size/bundle and can only enter quantities.
        self._scope_to_bundle(request, schema)
        return adda, sr, task, schema

    @staticmethod
    def _scope_to_bundle(request, schema):
        """If ?color=&size= name a pair the worker actually holds, trim the schema in
        place to just that bundle: one option per choice field (pre-fixed), one initial
        line, allowed_pairs = {that pair}. Sets schema['single_bundle'] + a label.
        Reads request.GET so it applies on both GET and the POST-back (form action keeps
        the query). Invalid/absent params → no-op (full multi-bundle form)."""
        allowed = schema.get('allowed_pairs')
        if allowed is None:
            return
        c_raw = request.GET.get('color') or ''
        s_raw = request.GET.get('size') or ''
        color_id = int(c_raw) if c_raw.isdigit() else None
        size_id = int(s_raw) if s_raw.isdigit() else None
        if (color_id, size_id) not in set(allowed):
            return   # not this worker's pair — leave the full form (defence in depth)
        label_bits = []
        for f in schema['fields']:
            if f['kind'] != 'choice':
                continue
            keep = color_id if f['key'] == 'color_id' else size_id
            f['options'] = [dict(o, selected=True) for o in f.get('options', ())
                            if o['value'] == keep]
            if f['options']:
                label_bits.append(f['options'][0]['label'])
        schema['initial_lines'] = [{'color_id': color_id, 'size_id': size_id}]
        schema['allowed_pairs'] = [(color_id, size_id)]
        schema['single_bundle'] = True
        schema['bundle_label'] = ' · '.join(label_bits)

    @staticmethod
    def _scoped_contribs(task, schema):
        """AE-3: in single-bundle mode, the editable form must show ONLY the scoped
        bundle's saved line (not the worker's other bundles on the same task). None =
        full multi-bundle form (all saved lines)."""
        if not schema.get('single_bundle'):
            return None
        c_id, s_id = schema['allowed_pairs'][0]
        return [c for c in task.contributions.all().order_by('pk')
                if c.color_id == c_id and c.size_id == s_id]

    def _report_url(self, request, code, stage_type):
        from django.urls import reverse
        url = reverse('production:worker-report', args=[code, stage_type])
        params = []
        if request.GET.get('embedded') == '1':
            params.append('embedded=1')
        # Preserve single-bundle scope across the POST-redirect loop.
        for k in ('color', 'size', 'stream'):
            v = request.GET.get(k)
            if v:
                params.append(f'{k}={v}')
        return url + ('?' + '&'.join(params) if params else '')

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
            # AE-3 single-bundle: only THIS bundle's saved line (never other bundles').
            'form_lines': [] if locked else (
                _form_lines(task, schema, contribs=self._scoped_contribs(task, schema))
                or _initial_form_lines(schema)),
            'total_quantity': sum((l['quantity'] for l in saved), start=0),
            'embedded': embedded,
            # AE-3 single-bundle mode: lock the form to one bundle + keep the scope
            # on the POST-back (form posts to this same query-carrying action).
            'single_bundle': schema.get('single_bundle', False),
            'bundle_label': schema.get('bundle_label', ''),
            'report_action': self._report_url(request, code, stage_type),
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
            # AE-3 per-bundle path: a "My Assigned Work" card opens ONE bundle. Submitting
            # it must NOT lock the worker's OTHER bundles on this stage — report_bundle
            # upserts just this bundle and completes the task only when every allocated
            # bundle has a report. (The full multi-line form keeps the save+complete path.)
            if schema.get('single_bundle') and action == 'submit' and lines:
                from production.services.worker_task_service import report_bundle
                result = report_bundle(task, lines[0], actor=request.user)
                if result['completed']:
                    messages.success(request, "Work report submitted — thank you!")
                else:
                    n = result['remaining_bundles']
                    messages.success(
                        request,
                        f"Bundle saved. {n} more bundle{'s' if n != 1 else ''} to report — "
                        "open them from My Assigned Work.")
            else:
                # Both actions persist via the SAME single-writer services — the view
                # never touches WorkerStageContribution directly (ADR 0001 discipline).
                save_draft_contributions(task, lines, actor=request.user)
                if action == 'submit':
                    complete_worker_task(task, actor=request.user)
                    messages.success(request, "Work report submitted — thank you!")
                else:
                    messages.success(request, "Draft saved. You can keep editing until you submit.")
            # AE-1: the soft over-allocation warning is retired — over-report is now
            # HARD-refused at submit (report_bundle / check_allocation_bound). No warning mode.
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


class MyAssignedWorkView(LoginRequiredMixin, View):
    """AE-3: the worker's "My Assigned Work" screen — every active bundle allocation
    across all in-progress Addas, as independent cards + a workload summary. The worker
    never picks colour/size/bundle: each card deep-links to its own quantity-only report
    (`?color=&size=`). Read-only; data via the bundle_service read-model."""

    def get(self, request):
        from production.services import my_assigned_work
        data = my_assigned_work(request.user)
        return render(request, 'production/my_assigned_work.html', {
            'cards': data['cards'], 'summary': data['summary'],
        })


class AddaSnapshotView(LoginRequiredMixin, View):
    """AE-4 Super-Admin Production Snapshot — management's operational control screen for
    ONE Adda. Per pool stage: stage totals + per-bundle rollup + per-worker×bundle detail
    (mode/allocated/completed/remaining/expected/status/times). Read-only via bundle_service;
    management-only (workers never see other workers' names/quantities — OP-1)."""

    def _gate(self, request):
        from accounts.services import MANAGEMENT_ROLES, user_has_role
        if not user_has_role(request.user, MANAGEMENT_ROLES):
            raise PermissionDenied("Production snapshot is management-only.")

    def get(self, request, code):
        self._gate(request)
        from production.constants import ALLOC_DIM_NONE
        from production.services import stage_snapshot
        adda = get_object_or_404(Adda, code=code)
        stages = []
        wss = (adda.product.workflow_stages
               .exclude(allocation_dimensions=ALLOC_DIM_NONE)
               .select_related('stage').order_by('order'))
        for ws in wss:
            for sr in (AddaStageRecord.objects
                       .filter(adda=adda, workflow_stage=ws)
                       .select_related('workflow_stage__stage', 'stream')
                       .order_by('stream_id')):
                snap = stage_snapshot(sr)
                if snap['bundles'] or snap['allocations']:
                    stages.append({
                        'sr': sr, 'name': ws.stage.name,
                        'stream': sr.stream, 'snap': snap})
        return render(request, 'production/adda_snapshot.html',
                      {'adda': adda, 'stages': stages})
