"""acquisition_service — SINGLE WRITER for EvidenceItem (M2, the
Acquisition Layer made first-class: PRODUCT_DESIGN_FREEZE §1/§7).

The one contract every input follows:
    Evidence (any source) → Adapter (per kind) → Proposal
    (GeometryExtraction, append-only, honest refusals) → Human Review
    (one-shot) → Verified Geometry (pattern_geometry_service).

This module owns the EVIDENCE rows and orchestrates; proposals are
written ONLY by pattern_geometry_service (its table, its writer).
Ladder honesty (SAM precedent): unavailable adapters never create rows —
they report themselves unavailable at the menu; adapter failures are
RECORDED refusals, never silent.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from accounts.services import MANAGEMENT_ROLES, user_has_role

from patterns_ai.models import EvidenceItem

# menu truth (UI freeze §2.4): which kinds run TODAY vs report themselves
# honestly unavailable. Flipping an entry here is a conscious platform act.
AVAILABLE_KINDS = ('photo', 'photo_plain', 'dxf', 'svg', 'manual_dims')
UNAVAILABLE_KINDS = {
    'pdf': 'PDF import arrives with a later runtime upgrade — use DXF, '
           'SVG or a mat photo.',
    'png': 'Plain-image import arrives with a later runtime upgrade — '
           'photograph the piece on a calibration mat instead.',
    'ai_api': 'No external AI service is configured yet.',
}

# M8 params vocabulary — what a plain photo SAYS about itself. `view` is
# a label (which angle/state); `measurements` are the human tape numbers
# THIS photo evidences (owner freeze: measurements belong to individual
# evidence items). Any name is legal — width_mm/height_mm drive scale,
# everything else becomes a recorded cross-check.
PLAIN_VIEWS = ('top_full', 'folded', 'closeup', 'edge', 'corner',
               'reference', 'other')


def _validate_plain_params(params):
    """Normalize + validate photo_plain params {view, measurements}."""
    params = dict(params or {})
    view = str(params.get('view') or 'other').strip().lower()
    if view not in PLAIN_VIEWS:
        raise ValidationError(
            f'unknown view {view!r} — one of {", ".join(PLAIN_VIEWS)}.')
    raw = params.get('measurements') or {}
    if not isinstance(raw, dict):
        raise ValidationError('measurements must be a name→mm mapping.')
    measurements = {}
    for name, value in raw.items():
        key = str(name).strip().lower().replace(' ', '_')[:40]
        if not key:
            continue
        if not key.endswith('_mm'):
            key += '_mm'
        try:
            mm = float(value)
        except (TypeError, ValueError):
            raise ValidationError(f'measurement {key!r} is not a number.')
        if not (0 < mm <= 10000):
            raise ValidationError(
                f'measurement {key!r} must be 0–10000 mm.')
        measurements[key] = mm
    return {'view': view, 'measurements': measurements}


def _gate(user):
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied('management role required')


def _stack_guard(piece, size):
    if size.product_id != piece.product_id:
        raise ValidationError('size belongs to a different product.')


@transaction.atomic
def add_evidence(*, user, piece, size, kind, uploaded_file=None,
                 params=None):
    """Add ONE evidence item to the piece×size stack and immediately run
    its adapter (evidence without a verdict helps nobody). Returns
    (evidence, proposal). Refusals come back recorded, never raised."""
    from . import pattern_geometry_service as geo
    _gate(user)
    _stack_guard(piece, size)
    if kind in UNAVAILABLE_KINDS:
        raise ValidationError(UNAVAILABLE_KINDS[kind])
    if kind not in ('dxf', 'svg', 'manual_dims', 'photo_plain'):
        raise ValidationError(
            'photo evidence arrives through the capture hand-off; '
            f'kind {kind!r} does not add here.')
    if kind in ('dxf', 'svg', 'photo_plain'):
        if uploaded_file is None:
            raise ValidationError('choose a file first.')
        if uploaded_file.size > 10 * 1024 * 1024:
            raise ValidationError('file too large (10 MB limit).')
    if kind == 'photo_plain':
        # M8: plain photos JOIN the set silently — no per-item adapter.
        # The Evidence-Set adapter (build_from_evidence) proposes ONE
        # geometry from the whole stack when the human asks.
        evidence = EvidenceItem.objects.create(
            piece=piece, size=size, kind=kind, file=uploaded_file,
            params=_validate_plain_params(params), created_by=user)
        return evidence, None
    evidence = EvidenceItem.objects.create(
        piece=piece, size=size, kind=kind,
        file=uploaded_file if kind in ('dxf', 'svg') else None,
        params=params or {}, created_by=user)
    proposal = geo.run_evidence_adapter(user=user, evidence=evidence)
    record_verdict(evidence, proposal)
    return evidence, proposal


@transaction.atomic
def build_from_evidence(*, user, piece, size, primary):
    """M8 owner-frozen step 'Build Geometry From Evidence': run the
    Evidence-SET adapter — primary plain photo supplies the outline,
    every stated measurement across the stack supplies scale +
    cross-checks. One proposal from the whole set; verdict stamps the
    primary (this module stays the evidence writer)."""
    from . import pattern_geometry_service as geo
    _gate(user)
    _stack_guard(piece, size)
    if primary.piece_id != piece.pk or primary.size_id != size.pk:
        raise ValidationError('primary evidence belongs to a different '
                              'design row.')
    if primary.kind != EvidenceItem.Kind.PHOTO_PLAIN:
        raise ValidationError('choose a plain-background PHOTO as the '
                              'primary evidence.')
    proposal = geo.run_set_adapter(user=user, piece=piece, size=size,
                                   primary=primary)
    record_verdict(primary, proposal)
    return proposal


def create_photo_evidence(*, user, piece, size, capture):
    """Capture flow step 1 (same transaction as the extraction): the
    stored photo enters the Evidence Stack; the caller then runs
    run_extraction(evidence=…) and records the verdict here."""
    _gate(user)
    _stack_guard(piece, size)
    return EvidenceItem.objects.create(
        piece=piece, size=size, kind=EvidenceItem.Kind.PHOTO,
        capture=capture, created_by=user)


def record_verdict(evidence, proposal):
    """Stamp the adapter verdict onto the evidence row (single writer)."""
    if proposal.gate.get('passed'):
        evidence.status = EvidenceItem.Status.PROPOSED
    else:
        evidence.status = EvidenceItem.Status.REFUSED
        reasons = proposal.gate.get('reasons') or ['refused by the gate']
        evidence.refusal_reason = ('; '.join(str(r) for r in reasons))[:300]
    evidence._service_transition = True
    evidence.save(update_fields=['status', 'refusal_reason', 'updated_at'])


def stack_for(piece, size):
    """The piece×size Evidence Stack, newest first (read helper)."""
    return (EvidenceItem.objects.filter(piece=piece, size=size)
            .select_related('capture')
            .prefetch_related('proposals')
            .order_by('-id'))


def next_missing_design(product, after_key=None):
    """CONVEYOR (UI freeze §2.4): the next mandatory design row that is
    not confirmed, size-first order. after_key = 'piece:size' design_key
    to continue past. Returns the facade Design Row or None (marathon
    done)."""
    from .pattern_design_facade import product_design_library
    library = product_design_library(product)
    rows = [r for s in library['sections'] for r in s['rows']
            if not r['badges']['optional'] and r['status'] != 'confirmed']
    if not rows:
        return None
    if after_key:
        keys = [r['design_key'] for r in rows]
        if after_key in keys:
            i = keys.index(after_key)
            rows = rows[i + 1:] + rows[:i]      # continue forward, wrap
            return rows[0] if rows else None
    return rows[0]
