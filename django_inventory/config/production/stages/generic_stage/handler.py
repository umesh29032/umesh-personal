"""GenericStageHandler — ONE handler for every config-only operation (R10-B).

NOT decorated with @register: the registry FALLBACK instantiates it per stage
code (see stages/base/registry.py) for any active Stage row that has no
bespoke package. Work-type aware: MACHINE stages surface their machine type +
the instances currently assigned on this Adda; MANUAL stages just say so.
Money never enters here (frozen rules 6/10) — rates/earnings stay on the
WorkflowStage + the settlement funnel exactly like every other stage.
"""
from __future__ import annotations

from decimal import Decimal

from production.stages.base.handler import (
    CompletionResult, ReopenResult, StageHandler,
)


class GenericStageHandler(StageHandler):
    template_partial = 'production/_stage_panel_generic.html'

    def __init__(self, code: str, name: str = ''):
        self.code = code
        self.name = name or code.replace('_', ' ').title()

    # ── worker report (schema-driven phone form) ─────────────────────────
    def contribution_schema(self, adda, worker=None):
        """OP-1: on a COLOUR+SIZE pool stage the worker reports PER DIMENSION —
        choice options = that worker's ACTIVE allocated dims (labels/swatches
        ONLY; quantities never enter the schema — blind-reporting rule: the
        worker is never told how many pieces arrived). Unscoped callers
        (worker=None: A360 rollups, qty-field discovery) get the dim fields
        with empty options — key discovery works, no data leaks. NONE/QUANTITY
        stages keep the plain 3-field form."""
        from production.constants import ALLOC_DIM_COLOR_SIZE

        fields = []
        initial_lines = []
        # AE-1 gap-E fix: the flat colour/size option lists lose the PAIRING — a
        # worker allocated Red/M + Blue/XL would otherwise pass Red (a valid colour)
        # + XL (a valid size) = Red/XL, a pair never allocated. `allowed_pairs`
        # carries the worker's real allocated pairs; `pair_keys` names the choice
        # fields that form a pair, so the GENERIC parser refuses an unallocated pair
        # at entry (no stage names). None = don't pair-check (unscoped / non-dim stage).
        pair_keys, allowed_pairs = [], None
        wf = adda.product.workflow_stages.filter(stage__code=self.code).first()
        if wf is not None and wf.allocation_dimensions == ALLOC_DIM_COLOR_SIZE:
            color_opts, size_opts = [], []
            pair_keys = ['color_id', 'size_id']
            if worker is not None:
                sr = self._sr(adda)
                if sr is not None:
                    from production.models import WorkerStageAllocation
                    rows = (WorkerStageAllocation.objects
                            .filter(stage_record=sr, worker=worker,
                                    voided_at__isnull=True)
                            .select_related('color', 'size'))
                    seen_c, seen_s, seen_pairs = {}, {}, set()
                    for a in rows:
                        if a.color_id and a.color_id not in seen_c:
                            seen_c[a.color_id] = {'value': a.color_id,
                                                  'label': a.color.name,
                                                  'swatch': a.color.hex_code or ''}
                        if a.size_id and a.size_id not in seen_s:
                            seen_s[a.size_id] = {'value': a.size_id,
                                                 'label': a.size.label}
                        # J-2: one prefilled report row per allocated PAIR — the
                        # flat option lists above lose the pairing. Labels only,
                        # never quantities (blind rule holds).
                        if (a.color_id, a.size_id) not in seen_pairs:
                            seen_pairs.add((a.color_id, a.size_id))
                            initial_lines.append({'color_id': a.color_id,
                                                  'size_id': a.size_id})
                    color_opts = list(seen_c.values())
                    size_opts = list(seen_s.values())
                    # worker-scoped → we KNOW the real pairs; empty set = worker has
                    # no allocation yet (reporting is refused entirely upstream).
                    allowed_pairs = sorted(seen_pairs)
            fields += [
                {'key': 'color_id', 'kind': 'choice', 'label': 'Colour',
                 'required': True, 'options': color_opts},
                {'key': 'size_id', 'kind': 'choice', 'label': 'Size',
                 'required': True, 'options': size_opts},
            ]
        fields += [
            {'key': 'reported_quantity', 'kind': 'quantity',
             'label': 'Good pieces', 'required': True, 'unit': 'pieces'},
            {'key': 'alter_quantity', 'kind': 'observation',
             'label': 'Alter pieces', 'required': False, 'unit': 'pieces'},
            # Pre-Phase-3 A: 4-way reality — Missing = lost (theft/loss signal),
            # Damaged = scrap beyond repair. The old 'Missing / rejected' label
            # folded scrap into the loss signal; the two are now separate fields.
            {'key': 'missing_quantity', 'kind': 'observation',
             'label': 'Missing / lost', 'required': False, 'unit': 'pieces'},
            {'key': 'damaged_quantity', 'kind': 'observation',
             'label': 'Damaged / scrap', 'required': False, 'unit': 'pieces'},
        ]
        return {'line_label': 'work line', 'fields': fields,
                'initial_lines': initial_lines,
                'pair_keys': pair_keys, 'allowed_pairs': allowed_pairs}

    # ── snapshots (read-only references — frozen rule: render live rows) ──
    def _sr(self, adda):
        from .service import _get_stage_record
        return _get_stage_record(adda, self.code)

    def _totals(self, sr):
        from django.db.models import Sum
        from production.models import WorkerStageContribution
        agg = (WorkerStageContribution.objects
               .filter(task__stage_record=sr)
               .exclude(task__status='cancelled')
               .aggregate(good=Sum('good_quantity'), alter=Sum('alter_quantity'),
                          missing=Sum('missing_quantity'),
                          damaged=Sum('damaged_quantity')))
        return {k: (v or Decimal('0')) for k, v in agg.items()}

    def snapshot(self, adda):
        sr = self._sr(adda)
        if sr is None:
            return {'status': 'not_started'}
        t = self._totals(sr)
        return {
            'status': 'completed' if sr.completed_at else 'in_progress',
            'good': t['good'], 'alter': t['alter'], 'missing': t['missing'],
        }

    def admin_snapshot(self, adda):
        sr = self._sr(adda)
        if sr is None:
            return None
        from production.models import Stage
        stage = Stage.objects.select_related('machine_type').filter(
            code=self.code).first()
        t = self._totals(sr)
        rows = [('Good', t['good']), ('Alter', t['alter']),
                ('Missing', t['missing'])]
        sections = [{'label': 'Output', 'rows': rows}]
        if stage is not None and stage.work_type == 'machine':
            mrows = [('Machine type', stage.machine_type.name
                      if stage.machine_type else '—')]
            # Instances currently held on THIS Adda with the matching type —
            # possession truth from MachineAssignment (read-only reference).
            try:
                from machines.models import MachineAssignment
                open_here = (MachineAssignment.objects
                             .filter(adda=adda, end_at__isnull=True,
                                     machine__machine_type=stage.machine_type)
                             .select_related('machine', 'worker'))
                for a in open_here:
                    mrows.append((a.machine.code,
                                  a.worker.get_full_name() or a.worker.email))
            except Exception:   # machines app data unavailable — reference only
                pass
            sections.append({'label': 'Machine', 'rows': mrows})
        else:
            sections.append({'label': 'Work type', 'rows': [('Performed', 'Manual')]})
        return {'title': f'{self.name} — reference', 'sections': sections}

    # ── panel ─────────────────────────────────────────────────────────────
    def panel_context(self, request, adda, record):
        from .views_ctx import build_generic_panel_context
        return build_generic_panel_context(request, adda, self.code, self.name)

    # ── lifecycle (delegates to the generic service) ──────────────────────
    def start(self, *, user_id, adda, record, data):
        from accounts.models import User
        from .service import start_generic_stage
        return start_generic_stage(
            adda=adda, stage_code=self.code,
            worker_ids=data.get('worker_ids', []),
            user=User.objects.get(pk=user_id))

    def complete(self, *, user_id, adda, record, data):
        from accounts.models import User
        from .service import complete_generic_stage
        complete_generic_stage(
            adda=adda, stage_code=self.code,
            user=User.objects.get(pk=user_id),
            override_pending_reason=data.get('override_pending_reason'))
        return CompletionResult()

    def reopen(self, *, user_id, record):
        from accounts.models import User
        from .service import reopen_generic_stage
        reopen_generic_stage(
            adda=record.adda, stage_code=self.code,
            user=User.objects.get(pk=user_id))
        return ReopenResult()

    def cost_quantity(self, record):
        # Standard-cost quantity at advance = Σ good of this stage's
        # non-cancelled contributions (per_piece grain; NULL when nothing —
        # honest-NULL posture, same as the other handlers).
        t = self._totals(record)
        return t['good'] if t['good'] else None
