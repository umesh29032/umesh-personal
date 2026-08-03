"""patterns_ai views — Block 3B: manual-marker capture workflow.

parse→gate→delegate ONLY: the view collects input, the single-writer services
validate and write (upload + marker in ONE transaction — a failed marker never
leaves an orphan asset).
"""
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView

from accounts.services import MANAGEMENT_ROLES, user_has_role
from production.models import Product

from patterns_ai.forms import ManualMarkerForm
from patterns_ai.models import Marker
from patterns_ai.services import capture_service, marker_service

logger = logging.getLogger(__name__)


class _ManagementOnly(UserPassesTestMixin):
    def test_func(self):
        return user_has_role(self.request.user, MANAGEMENT_ROLES)


def _int_or_404(raw):
    """Tampered non-integer ids must 404, not 500 (P1 review finding —
    get_object_or_404 does not catch the ValueError int coercion raises)."""
    from django.http import Http404
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise Http404('invalid id')


class PatternHomeView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """Landing — links to the Block-3B workflow (library pages come later)."""
    template_name = 'patterns_ai/home.html'


class ManualMarkerCreateView(LoginRequiredMixin, _ManagementOnly, View):
    """Upload the chalk-layout photo + create the manual marker, atomically."""
    template_name = 'patterns_ai/manual_marker_form.html'

    def _ctx(self, form):
        return {'form': form,
                'products': Product.objects.filter(is_active=True).order_by('code')}

    def get(self, request):
        return render(request, self.template_name, self._ctx(ManualMarkerForm()))

    def post(self, request):
        form = ManualMarkerForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, self._ctx(form))
        product = get_object_or_404(Product,
                                    pk=_int_or_404(request.POST.get('product')),
                                    is_active=True)
        try:
            with transaction.atomic():
                asset = capture_service.store_capture(
                    user=request.user, product=product,
                    uploaded_file=form.cleaned_data['photo'],
                    source=form.cleaned_data['source'])
                marker = marker_service.create_marker(
                    user=request.user, product=product,
                    origin=Marker.Origin.MANUAL_PHOTO,
                    usable_width_mm=form.cleaned_data['usable_width_mm'],
                    construction=form.cleaned_data['construction'],
                    ratio_counts=form.cleaned_data['ratio_text'],
                    label=form.cleaned_data['label'],
                    notes=form.cleaned_data['notes'], photo=asset)
        except (ValidationError, PermissionDenied) as exc:
            msgs = getattr(exc, 'messages', None) or [str(exc)]
            for m in msgs:
                form.add_error(None, m)
            return render(request, self.template_name, self._ctx(form))
        messages.success(request, f'Manual marker {marker.reference} saved.')
        return redirect('patterns_ai:manual-marker-created', reference=marker.reference)


class ManualMarkerCreatedView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """Success page — the marker is now permanent factory memory."""
    template_name = 'patterns_ai/manual_marker_created.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['marker'] = get_object_or_404(
            Marker.objects.select_related('product', 'photo'),
            reference=kwargs['reference'])
        return ctx


class MarkerListView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """Read-only Marker Library list (Block 3C). Pagination + basic ordering
    only — no filters/search by scope."""
    template_name = 'patterns_ai/marker_list.html'
    PAGE_SIZE = 20
    ORDERINGS = {'newest': '-id', 'oldest': 'id',
                 'reference': 'reference', 'width': 'usable_width_mm'}

    def get_context_data(self, **kwargs):
        from django.core.paginator import Paginator
        ctx = super().get_context_data(**kwargs)
        sort = self.request.GET.get('sort', 'newest')
        order = self.ORDERINGS.get(sort, '-id')
        qs = (Marker.objects.select_related('product', 'photo')
              .order_by(order))
        page = Paginator(qs, self.PAGE_SIZE).get_page(self.request.GET.get('page'))
        ctx.update({'page': page, 'sort': sort,
                    'orderings': self.ORDERINGS.keys()})
        return ctx


class MarkerDetailView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """Read-only marker detail: biography + lineage + summary — everything
    comes from marker_query_service (no duplicated logic)."""
    template_name = 'patterns_ai/marker_detail.html'

    def get_context_data(self, **kwargs):
        from patterns_ai.services import marker_query_service as q
        ctx = super().get_context_data(**kwargs)
        marker = get_object_or_404(
            Marker.objects.select_related('product', 'photo', 'adda',
                                          'supersedes', 'benchmarked_against'),
            reference=kwargs['reference'])
        from patterns_ai.services import marker_feedback_service as fb
        usage_rows = []
        for u in q.get_marker_usage_history(marker):
            metrics = None
            outcome = getattr(u, 'outcome', None)
            if outcome is not None:
                metrics = fb.derive_metrics(outcome)
            usage_rows.append({'usage': u, 'metrics': metrics})
        ctx.update({
            'marker': marker,
            'biography': q.get_marker_biography(marker),
            'lineage': q.get_marker_lineage(marker),
            'summary': q.get_marker_summary(marker),
            'usage_rows': usage_rows,
        })
        return ctx


class MarkerThumbView(LoginRequiredMixin, _ManagementOnly, View):
    """Serve the SAFE rendition (never the original) — management-gated
    streaming so no direct media URL is ever exposed for knowledge files."""

    def get(self, request, pk):
        from django.core.files.storage import default_storage
        from django.http import FileResponse, Http404

        from patterns_ai.models import CaptureAsset
        from patterns_ai.services import capture_service

        asset = get_object_or_404(CaptureAsset, pk=pk)
        # M6 Rule M: the Hub lightbox may ask for the LARGE rendition —
        # whitelisted sizes only; the original is still never served.
        size = {'320': 320, '1024': 1024}.get(
            request.GET.get('size', '320'))
        if size is None:
            raise Http404('unknown rendition size')
        path = capture_service.get_or_create_thumbnail(asset, size=size)
        if path is None:
            raise Http404('rendition unavailable')
        return FileResponse(default_storage.open(path, 'rb'),
                            content_type='image/jpeg')


class MarkerUsageCreateView(LoginRequiredMixin, _ManagementOnly, View):
    """Record a usage fact against a marker (Block 3D). parse→gate→delegate:
    marker_feedback_service owns usability/D11/plies rules."""
    template_name = 'patterns_ai/usage_form.html'

    def _marker(self, reference):
        return get_object_or_404(
            Marker.objects.select_related('product'), reference=reference)

    def _ctx(self, marker, form):
        from production.models import Adda
        return {'marker': marker, 'form': form,
                'addas': Adda.objects.filter(product=marker.product)
                                     .order_by('-started_at')[:50]}

    def get(self, request, reference):
        from patterns_ai.forms import MarkerUsageForm
        m = self._marker(reference)
        return render(request, self.template_name, self._ctx(m, MarkerUsageForm()))

    def post(self, request, reference):
        from production.models import Adda
        from patterns_ai.forms import MarkerUsageForm
        from patterns_ai.services import marker_feedback_service as fb
        m = self._marker(reference)
        form = MarkerUsageForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._ctx(m, form))
        adda = get_object_or_404(Adda, pk=_int_or_404(request.POST.get('adda')),
                                 product=m.product)
        try:
            fb.record_usage(
                user=request.user, marker=m, adda=adda,
                plies=form.cleaned_data['plies'],
                repeats=form.cleaned_data['repeats'],
                measured_usable_width_mm=form.cleaned_data['measured_width_mm'],
                notes=form.cleaned_data['notes'])
        except (ValidationError, PermissionDenied) as exc:
            for msg in getattr(exc, 'messages', None) or [str(exc)]:
                form.add_error(None, msg)
            return render(request, self.template_name, self._ctx(m, form))
        messages.success(request, f'Usage recorded for {m.reference} on {adda.code}.')
        return redirect('patterns_ai:marker-detail', reference=m.reference)


class MarkerUsageVoidView(LoginRequiredMixin, _ManagementOnly, View):
    """Void (never edit/delete) a usage — reason mandatory (service rule)."""

    def post(self, request, pk):
        from patterns_ai.models import MarkerUsage
        from patterns_ai.services import marker_feedback_service as fb
        usage = get_object_or_404(
            MarkerUsage.objects.select_related('marker'), pk=pk)
        try:
            fb.void_usage(user=request.user, usage=usage,
                          reason=request.POST.get('reason', ''))
        except (ValidationError, PermissionDenied) as exc:
            for msg in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, msg)
        else:
            messages.success(request, 'Usage voided — kept in history.')
        return redirect('patterns_ai:marker-detail',
                        reference=usage.marker.reference)


class MarkerOutcomeCreateView(LoginRequiredMixin, _ManagementOnly, View):
    """Explicit human 'record outcome' act (N-6): raw facts in metres →
    integer-mm at the edge; derived metrics flashed after save (never stored)."""
    template_name = 'patterns_ai/outcome_form.html'

    def _usage(self, pk):
        from patterns_ai.models import MarkerUsage
        return get_object_or_404(
            MarkerUsage.objects.select_related('marker', 'adda'), pk=pk)

    def get(self, request, pk):
        from patterns_ai.forms import MarkerOutcomeForm
        u = self._usage(pk)
        return render(request, self.template_name,
                      {'usage': u, 'form': MarkerOutcomeForm()})

    def post(self, request, pk):
        from patterns_ai.forms import MarkerOutcomeForm
        from patterns_ai.services import marker_feedback_service as fb
        from patterns_ai.services.units import m_to_mm
        u = self._usage(pk)
        form = MarkerOutcomeForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'usage': u, 'form': form})
        cd = form.cleaned_data
        try:
            outcome = fb.record_outcome(
                user=request.user, usage=u,
                fabric_in_mm=m_to_mm(cd['fabric_in_m']) if cd['fabric_in_m'] is not None else None,
                garments_cut=cd['garments_cut'],
                garments_packed=cd['garments_packed'],
                leftover_mm=m_to_mm(cd['leftover_m']) if cd['leftover_m'] is not None else None)
        except (ValidationError, PermissionDenied) as exc:
            for msg in getattr(exc, 'messages', None) or [str(exc)]:
                form.add_error(None, msg)
            return render(request, self.template_name, {'usage': u, 'form': form})
        metrics = fb.derive_metrics(outcome)
        if metrics['meters_per_100'] is not None:
            messages.success(
                request,
                f'Outcome recorded — {metrics["meters_per_100"]} m per 100 '
                f'garments (derived, not stored).')
        else:
            messages.success(request,
                             'Outcome recorded — metrics pending more facts (honest-NULL).')
        return redirect('patterns_ai:marker-detail',
                        reference=u.marker.reference)


class YieldBoardView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """The Yield Board (Block 3E) — Era-1's headline read model. Pure
    projection of get_product_yield_board; product selection is the ONLY
    filter; sorting only; nothing stored, nothing cached."""
    template_name = 'patterns_ai/yield_board.html'
    SORTS = ('avg', 'usage', 'recent', 'reference')

    def get_context_data(self, **kwargs):
        from patterns_ai.services import marker_query_service as q
        ctx = super().get_context_data(**kwargs)
        products = (Product.objects
                    .filter(is_active=True, markers__isnull=False)
                    .distinct().order_by('code'))
        sort = self.request.GET.get('sort', 'avg')
        if sort not in self.SORTS:
            sort = 'avg'
        product = None
        pid = self.request.GET.get('product')
        if pid:
            product = get_object_or_404(Product, pk=_int_or_404(pid),
                                        is_active=True)
        elif products:
            product = products[0]
        ctx.update({
            'products': products, 'product': product, 'sort': sort,
            'sorts': self.SORTS,
            'rows': q.get_product_yield_board(product, sort=sort) if product else [],
        })
        return ctx


# ════════════════════════════════════════════════════════════════════════════
# P2 — Geometry/CV era views. Same law as P1: parse -> gate -> delegate;
# every rule lives in calibration_service / pattern_geometry_service.
# ════════════════════════════════════════════════════════════════════════════


class MatListView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    template_name = 'patterns_ai/mat_list.html'

    def get_context_data(self, **kwargs):
        from patterns_ai.models import CalibrationMat
        ctx = super().get_context_data(**kwargs)
        ctx['mats'] = (CalibrationMat.objects
                       .order_by('status', 'mat_code'))
        return ctx


class MatRegisterView(LoginRequiredMixin, _ManagementOnly, View):
    template_name = 'patterns_ai/mat_form.html'

    def get(self, request):
        from patterns_ai.forms import MatRegisterForm
        return render(request, self.template_name,
                      {'form': MatRegisterForm()})

    def post(self, request):
        from patterns_ai.forms import MatRegisterForm
        from patterns_ai.services import calibration_service
        form = MatRegisterForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})
        try:
            mat = calibration_service.register_mat(
                user=request.user, **form.cleaned_data)
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                form.add_error(None, m)
            return render(request, self.template_name, {'form': form})
        messages.success(request, f'Mat {mat.mat_code} registered — '
                                  'commission it before first use.')
        return redirect('patterns_ai:mat-detail', pk=mat.pk)


class MatDetailView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    template_name = 'patterns_ai/mat_detail.html'

    def get_context_data(self, **kwargs):
        from patterns_ai.forms import MatCommissionForm
        from patterns_ai.models import CalibrationMat
        ctx = super().get_context_data(**kwargs)
        mat = get_object_or_404(CalibrationMat, pk=kwargs['pk'])
        ctx.update({'mat': mat,
                    'checks': mat.checks.select_related('checked_by')
                                        .order_by('-id'),
                    'commission_form': MatCommissionForm(),
                    'recent_captures':
                        mat.captures.filter(kind='pattern_capture',
                                            status='stored')
                           .order_by('-id')[:5]})
        return ctx


class MatCommissionView(LoginRequiredMixin, _ManagementOnly, View):
    def post(self, request, pk):
        from patterns_ai.forms import MatCommissionForm
        from patterns_ai.models import CalibrationMat
        from patterns_ai.services import calibration_service
        mat = get_object_or_404(CalibrationMat, pk=pk)
        form = MatCommissionForm(request.POST, request.FILES)
        if not form.is_valid():
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f'{field}: {e}')
            return redirect('patterns_ai:mat-detail', pk=mat.pk)
        try:
            # v1 commissioning is TAPE-ONLY (photo-based checks run later as
            # rechecks on real captures stored via the wizard — custody-clean)
            mat2, check = calibration_service.commission_mat(
                user=request.user, mat=mat,
                board_spec=form.board_spec(),
                control_distances=form.control_distances(),
                notes=form.cleaned_data['notes'])
            messages.success(request,
                             f'Mat {mat.mat_code} commissioned (check '
                             f'#{check.pk} PASS).')
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
        return redirect('patterns_ai:mat-detail', pk=mat.pk)


class MatRecheckView(LoginRequiredMixin, _ManagementOnly, View):
    """Recheck the mat against a pattern capture already stored ON it —
    evidence reuse, no separate photo path (ADR-D3 custody chain)."""

    def post(self, request, pk):
        from patterns_ai.models import CalibrationMat, CaptureAsset
        from patterns_ai.services import calibration_service
        mat = get_object_or_404(CalibrationMat, pk=pk)
        capture = get_object_or_404(
            CaptureAsset, pk=_int_or_404(request.POST.get('capture')),
            mat=mat)
        try:
            check = calibration_service.record_recheck(
                user=request.user, mat=mat, photo_asset=capture,
                notes=request.POST.get('notes', ''))
            messages.success(
                request,
                f"Recheck #{check.pk}: {'PASS' if check.passed else 'FAIL'}.")
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
        return redirect('patterns_ai:mat-detail', pk=mat.pk)


class MatRetireView(LoginRequiredMixin, _ManagementOnly, View):
    def post(self, request, pk):
        from patterns_ai.models import CalibrationMat
        from patterns_ai.services import calibration_service
        mat = get_object_or_404(CalibrationMat, pk=pk)
        try:
            calibration_service.retire_mat(
                user=request.user, mat=mat,
                reason=request.POST.get('reason', ''))
            messages.success(request, f'Mat {mat.mat_code} retired.')
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
        return redirect('patterns_ai:mat-detail', pk=mat.pk)


def _hub_readiness(product):
    """PDM W1: thin delegate — the derivation moved VERBATIM into the
    read-only design facade (`pattern_design_facade.product_readiness`),
    the single supplier of design knowledge (plan §0b). Same shape, same
    strings — parity-tested."""
    from patterns_ai.services import pattern_design_facade as facade
    return facade.product_readiness(product)


def _hub_readiness_legacy_reference(product):
    """RETIRED body (kept this session for the W1 parity test; W2 review
    may delete). Rules J/K/L (§2d): DERIVED-ONLY readiness — computed at
    read from the frozen truth chain (pieces → latest confirmed version →
    per-size geometry rows), never stored (F6). Blockers block generation;
    warnings show honestly."""
    from patterns_ai.models import (PatternPiece, PatternPieceVersion,
                                    ProductFabricProfile)
    Status = PatternPieceVersion.Status
    sizes = list(product.sizes.filter(is_active=True)
                 .order_by('display_order'))
    pieces = list(PatternPiece.objects.filter(product=product)
                  .select_related('pattern', 'reference_image')
                  .prefetch_related('versions__size_geometries')
                  .order_by('pattern__name'))
    profile = ProductFabricProfile.objects.filter(product=product).first()

    rows, blockers, warnings = [], [], []
    req_cells = req_done = draft_cells = 0
    pieces_with_ref = 0
    for piece in pieces:
        name = piece.pattern.name
        confirmed = None
        draft_covered = set()
        for v in piece.versions.all():                 # prefetched
            if v.status == Status.CONFIRMED and (
                    confirmed is None
                    or v.version_no > confirmed.version_no):
                confirmed = v
            elif v.status == Status.DRAFT:
                draft_covered |= {g.size_id
                                  for g in v.size_geometries.all()}
        covered = ({g.size_id for g in confirmed.size_geometries.all()}
                   if confirmed else set())
        cells, missing, pending = [], [], []
        for s in sizes:
            if s.pk in covered:
                cells.append((s, 'ok'))
            elif s.pk in draft_covered:
                cells.append((s, 'draft'))
                pending.append(s.label)
                draft_cells += 1
            else:
                cells.append((s, 'missing'))
                missing.append(s.label)
            if not piece.is_optional:
                req_cells += 1
                if s.pk in covered:
                    req_done += 1
        if piece.on_fold:
            # M4.5 conscious law change: fold pieces are manufacturable
            # WITH a marked fold edge; the blocker now names the fix.
            no_edge = [s.label for s in sizes
                       if s.pk in covered and not (
                           (({g.size_id: g for g in
                              confirmed.size_geometries.all()}
                             [s.pk].geometry.get('features') or {})
                            .get('fold_edge')))]
            if no_edge:
                blockers.append(f'{name} — mark the fold edge in the '
                                f"Studio ({', '.join(no_edge)})")
        if missing:
            if piece.is_optional:
                warnings.append(f'{name} — missing {", ".join(missing)} '
                                '(optional: skipped honestly, never '
                                'blocks)')
            else:
                blockers.append(f'{name} — missing '
                                f'{", ".join(missing)} geometry')
        if pending:
            warnings.append(f'{name} — {", ".join(pending)} drawn but '
                            'not confirmed')
        if piece.reference_image_id:
            pieces_with_ref += 1
        else:
            warnings.append(f'{name} — missing reference image (warning)')
        # Rule K: ONE next step per piece
        if not sizes:
            nxt = 'Add product sizes first (production → Sizes)'
        elif confirmed is None and not draft_covered:
            nxt = 'Capture or import geometry'
        elif missing:
            nxt = f'Add {missing[0]} geometry'
        elif pending:
            nxt = 'Confirm the drawn sizes'
        elif not piece.reference_image_id:
            nxt = 'Add a reference image'
        else:
            nxt = 'Ready ✓'
        rows.append({'piece': piece, 'name': name, 'cells': cells,
                     'next_step': nxt, 'ready': nxt == 'Ready ✓'})

    checklist = [
        ('Product Sizes', bool(sizes),
         f'{len(sizes)} size(s)' if sizes else 'none — add on the '
         'production Sizes page', True),
        ('Pattern Types', bool(pieces),
         f'{len(pieces)} piece(s)' if pieces else 'register the pieces',
         True),
        ('Required Pieces', req_cells == 0 or req_done == req_cells,
         f'{req_done}/{req_cells} size designs confirmed', True),
        ('Confirmed Geometry', draft_cells == 0,
         'all confirmed' if draft_cells == 0
         else f'{draft_cells} drawn size(s) awaiting confirm', False),
        ('Grain', True, 'enforced at confirm — cannot be missing', False),
        ('Fold Rules',
         not any('mark the fold edge' in b for b in blockers),
         'fold edges marked' if any(p.on_fold for p in pieces)
         and not any('mark the fold edge' in b for b in blockers)
         else 'no on-fold pieces' if not any(p.on_fold for p in pieces)
         else 'on-fold pieces need their fold edge marked', True),
        ('Reference Images', pieces and pieces_with_ref == len(pieces),
         f'{pieces_with_ref}/{len(pieces)} pieces illustrated', False),
        ('Optional Pieces', True,
         f'{sum(1 for p in pieces if p.is_optional)} optional '
         '(skip honestly when incomplete)', False),
        ('Fabric Profile', profile is not None,
         'defaults set' if profile else 'no defaults yet (optional)',
         False),
    ]
    total = req_cells + len(pieces) + 1          # + fabric profile
    done = req_done + pieces_with_ref + (1 if profile else 0)
    pct = int(round(100 * done / total)) if total else 0
    ready = bool(sizes and pieces and not blockers)
    return {'sizes': sizes, 'rows': rows, 'checklist': checklist,
            'pct': pct, 'ready': ready,
            'blockers': blockers, 'warnings': warnings,
            'profile': profile}


class PatternDashboardView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """Phase 1 — the PATTERN DASHBOARD: permanent home of all pattern work
    for one product (owner-frozen platform entry, GitHub-repo model).

    Visually explains the workflow as numbered steps:
      STEP 1 Pattern Blueprint  (define the garment structure)
      STEP 2 Pattern Manager    (prepare every Product Size)
      STEP 3 Digital Cutting Table (compose manufacturing layouts, gated
             ≥1 Ready size — same law/field as the Manager gate)
    GET-only; derives everything from the read-only facade (one call)."""
    template_name = 'patterns_ai/dashboard.html'

    def get_context_data(self, **kwargs):
        from patterns_ai.services import pattern_design_facade as facade
        ctx = super().get_context_data(**kwargs)
        pid = self.request.GET.get('product')
        if not pid:
            # Rule C: no product context → a chooser, never a filter
            ctx.update({'product': None,
                        'all_products': Product.objects.filter(
                            is_active=True).order_by('code')})
            return ctx
        product = get_object_or_404(Product, pk=_int_or_404(pid),
                                    is_active=True)
        library = facade.product_design_library(product)
        sections = library['sections']
        # M2: the dashboard is the 5-STATION RAIL (UI freeze §1/§2.1) —
        # live verdicts for the two asset stations come from the frozen
        # Phase-7/8 stores (read-only counts, patterns_ai-owned models).
        from patterns_ai.models import ApprovedLayout, ApprovedLayoutUsage
        layouts_active = ApprovedLayout.objects.filter(
            product=product, status=ApprovedLayout.Status.ACTIVE).count()
        usages_active = ApprovedLayoutUsage.objects.filter(
            layout__product=product, voided_at__isnull=True).count()
        ctx.update({
            'product': product,
            'summary': library['summary'],
            'sizes_total': len(sections),
            'sizes_ready': sum(1 for s in sections if s['ready']),
            'blueprint_pieces': library['summary']['pieces_count'],
            'layouts_active': layouts_active,
            'usages_active': usages_active,
        })
        return ctx


class PatternBlueprintView(LoginRequiredMixin, UserPassesTestMixin,
                           TemplateView):
    """Phase 2 — the PATTERN BLUEPRINT module (STEP 1, frozen resp. #1):
    the product's structural DNA. Every piece + every rule (count ·
    required/optional · pair · fold · grain · fabric group), edited HERE
    and nowhere else. Never geometry. Strict gate = the OLD editor's perm
    (production.change_productpattern, super-admin bypass) — structure
    edits stay admin-level. parse→gate→delegate: all writes go through
    pattern_geometry_service (single writer)."""
    template_name = 'patterns_ai/blueprint.html'

    def test_func(self):
        from accounts.services import user_has_perm
        return user_has_perm(self.request.user,
                             'production.change_productpattern')

    def _product(self, source):
        return get_object_or_404(Product, pk=_int_or_404(source.get('product')),
                                 is_active=True)

    def get_context_data(self, **kwargs):
        from patterns_ai.models import PatternPiece
        ctx = super().get_context_data(**kwargs)
        if not self.request.GET.get('product'):
            ctx.update({'product': None,
                        'all_products': Product.objects.filter(
                            is_active=True).order_by('code')})
            return ctx
        product = self._product(self.request.GET)
        pieces = list(PatternPiece.objects.filter(product=product)
                      .select_related('pattern', 'assignment')
                      .order_by('pattern__name'))
        piece_pattern_ids = {p.pattern_id for p in pieces}
        # continuity: assignments made in the OLD editor with no PDM piece
        # row yet — shown as unregistered structure, one-click register
        unregistered = (product.pattern_assignments
                        .select_related('pattern')
                        .exclude(pattern_id__in=piece_pattern_ids)
                        .order_by('pattern__name'))
        ctx.update({
            'product': product, 'pieces': pieces,
            'unregistered': list(unregistered),
            'fabric_groups': PatternPiece.FabricGroup.choices,
            'grain_rules': PatternPiece.GrainRule.choices,
        })
        return ctx

    def post(self, request):
        from django.urls import reverse
        from patterns_ai.models import PatternPiece
        from patterns_ai.services import pattern_geometry_service as geo
        product = self._product(request.POST)
        action = request.POST.get('action', '')
        back = redirect(reverse('patterns_ai:blueprint')
                        + f'?product={product.pk}')

        def _piece():
            return get_object_or_404(
                PatternPiece, pk=_int_or_404(request.POST.get('piece')),
                product=product)

        def _safe_count(raw):
            # PA-05A-4 behavior preserved: tampered/non-numeric count never
            # 500s and never blocks — clamp ≥1, fall back to 1
            try:
                return max(1, int(raw))
            except (TypeError, ValueError):
                return 1
        try:
            if action == 'add':
                piece = geo.register_pattern_definition(
                    user=request.user, product=product,
                    name=request.POST.get('name', ''),
                    pieces_count=_safe_count(request.POST.get('pieces_count')),
                    fabric_group=request.POST.get('fabric_group') or 'body',
                    is_pair=request.POST.get('is_pair') == '1',
                    on_fold=request.POST.get('on_fold') == '1',
                    grain_rule=request.POST.get('grain_rule') or None,
                    is_optional=request.POST.get('is_optional') == '1')
                messages.success(request,
                                 f'"{piece.pattern.name}" added to the '
                                 'Blueprint.')
            elif action == 'register':
                from production.models import ProductPattern
                pattern = get_object_or_404(
                    ProductPattern,
                    pk=_int_or_404(request.POST.get('pattern')))
                geo.create_piece(user=request.user, product=product,
                                 pattern=pattern, fabric_group='body')
                messages.success(request,
                                 f'"{pattern.name}" registered — set its '
                                 'rules below.')
            elif action == 'remove':
                piece = _piece()
                name = piece.pattern.name
                geo.remove_pattern_definition(user=request.user, piece=piece)
                messages.success(request, f'"{name}" removed.')
            elif action == 'set_count':
                geo.set_piece_count(
                    user=request.user, piece=_piece(),
                    pieces_count=_safe_count(
                        request.POST.get('pieces_count')))
                messages.success(request, 'Count updated.')
            elif action == 'set_rules':
                geo.set_piece_rules(
                    user=request.user, piece=_piece(),
                    is_pair=request.POST.get('is_pair') == '1',
                    on_fold=request.POST.get('on_fold') == '1',
                    grain_rule=request.POST.get('grain_rule'),
                    fabric_group=request.POST.get('fabric_group'),
                    # M2 adr-c.2 metadata slots (advisory, never block)
                    expected_notches=request.POST.get('expected_notches',
                                                      ...),
                    seam_allowance_mm=request.POST.get('seam_allowance_mm',
                                                       ...))
                messages.success(request, 'Rules updated.')
            elif action == 'set_optional':
                geo.set_piece_optional(
                    user=request.user, piece=_piece(),
                    is_optional=request.POST.get('is_optional') == '1')
                messages.success(request, 'Updated.')
            else:
                messages.error(request, 'Unknown action.')
        except (ValidationError, ValueError) as exc:
            messages.error(request, '; '.join(getattr(exc, 'messages', None)
                                              or [str(exc)]))
        except PermissionDenied:
            messages.error(request, 'Management role required.')
        return back


class CuttingTableShellView(LoginRequiredMixin, _ManagementOnly,
                            TemplateView):
    """Phase 4 — the DIGITAL CUTTING TABLE SHELL (frozen resp. #3):
    the PERMANENT workspace structure (owner amendments 1–7). Pure READ:
    one facade call + one fabric-profile read; palette = confirmed
    designs of READY sizes only, grouped FABRIC GROUP → size (LAW 12);
    every future control rendered disabled with its phase. Gate = ≥1
    Ready size, else Dashboard redirect with the honest reason.
    Interactions/persistence/AI/exports = Phases 5–7, NOT here."""
    template_name = 'patterns_ai/cutting_table.html'

    def get(self, request, pk):
        from patterns_ai.models import (GeneratedMarkerCandidate,
                                        ProductFabricProfile)
        from patterns_ai.services import pattern_design_facade as facade
        from patterns_ai.services.svg_render import outline_preview_svg
        product = get_object_or_404(Product, pk=pk, is_active=True)
        library = facade.product_design_library(product)
        if not library['summary']['any_size_ready']:
            messages.error(request,
                           'Digital Cutting Table is locked — no size is '
                           'ready yet. Finish the required designs of at '
                           'least one size.')
            from django.urls import reverse
            return redirect(reverse('patterns_ai:dashboard')
                            + f'?product={product.pk}')
        # M4: pieces-per-garment map (Blueprint count truth, one query)
        #
        # ⚠️ DEAD AS OF 2026-08-04 — ruff F841. This dict is built and never read: not
        # by this view, not by any template. So it costs one DB query per request and
        # returns nothing. Introduced in `90c1f2f3` (Manufacturing V1 certified release,
        # 2026-07-19), which suggests an M4 feature that was prepared and never wired up
        # rather than something that became obsolete.
        #
        # NOT REMOVED: patterns_ai is a frozen module and the owner's standing rule is no
        # refactor of frozen modules without explicit approval. Deleting a prepared-but-
        # unwired feature is the owner's call, not a lint cleanup. Two options when you
        # decide: wire it into the payload if M4 still wants it, or delete these six
        # lines and reclaim the query.
        from patterns_ai.models import PatternPiece as _PP
        count_by_piece = {  # noqa: F841 — see the note above; owner decision pending
            p.pk: (p.assignment.pieces_count if p.assignment_id else 1)
            for p in _PP.objects.filter(product=product)
            .select_related('assignment')}
        # palette: FABRIC GROUP → [(size, confirmed rows)] (amendment 6)
        groups = {}
        not_ready = []
        confirmed_total = 0
        workspace_payload = {}      # Phase 5: design_key → geometry+rules
        for sec in library['sections']:
            if not sec['ready']:
                not_ready.append(sec)
                continue
            for row in sec['rows']:
                if row['status'] != 'confirmed':
                    continue                      # DCT consumes confirmed ONLY
                row['preview_svg'] = outline_preview_svg(row['outline_mm'])
                g = groups.setdefault(row['fabric_group'], {})
                g.setdefault(sec['size'].label, []).append(row)
                confirmed_total += 1
                # session-only interaction data (no writes, facade truth)
                # M4.5 R2-A: the payload ships the CAPABILITIES contract
                # (one named shape) instead of loose flags; + the DERIVED
                # opened outline for fold pieces (client never computes
                # geometry — data only).
                entry = {
                    'name': row['piece_name'], 'size': row['size_label'],
                    'group': row['fabric_group'],
                    'w': row['dims']['w_mm'] if row['dims'] else None,
                    'h': row['dims']['h_mm'] if row['dims'] else None,
                    'area': row['area_cm2'],       # 6A: utilization input
                    'outline': row['outline_mm'],
                    'piece_id': row['piece_id'], 'size_id': row['size_id'],
                    'caps': row['capabilities'],
                }
                if row['capabilities']['fold'] and row['opened_outline_mm']:
                    op = row['opened_outline_mm']
                    s = 0.0
                    for i in range(len(op)):
                        x1, y1 = op[i]
                        x2, y2 = op[(i + 1) % len(op)]
                        s += x1 * y2 - x2 * y1
                    entry['opened'] = {
                        'outline': op,
                        'w': row['opened_dims']['w_mm'],
                        'h': row['opened_dims']['h_mm'],
                        'area': round(abs(s) / 2.0 / 100.0, 1),
                    }
                    entry['fold_x_mm'] = row['fold_x_mm'] or 0.0
                workspace_payload[row['design_key']] = entry
        profile = ProductFabricProfile.objects.filter(
            product=product).first()

        # ── M4 Manufacturing Planner inputs (rows only — genericity) ──
        # ready sizes in CHART ORDER: the size-color palette cycles by
        # INDEX (F4 binding: any chart — S/M/L or 28/30/32 — colors
        # correctly; never name-keyed)
        ready_sizes = [{'id': sec['size'].pk, 'label': sec['size'].label}
                       for sec in library['sections'] if sec['ready']]
        # rolls: read-only planning facts (import-linter: patterns_ai =
        # top layer, imports-down legal). Nominal inches shown; usable
        # width stays human-confirmable (legacy Marker law).
        from raw_materials.models import ClothRoll
        rolls = [{'id': r.pk, 'label': f'{r.roll_id} · '
                  f'{r.width_inch or "?"}″ · {r.cloth_type.name}',
                  'usable_width_mm': r.usable_width_mm,
                  'one_way': r.is_one_way_nap}
                 for r in ClothRoll.objects
                 .filter(status=ClothRoll.Status.NOT_USED)
                 .select_related('cloth_type').order_by('-id')[:100]]
        import json as _json
        from patterns_ai.services import strategy_service
        recipes = [{'id': s.pk, 'name': s.name,
                    'fabric_group': s.fabric_group,
                    'layering_type': s.layering_type,
                    'piece_ids': s.piece_ids, 'size_ratio': s.size_ratio,
                    'notes': s.notes}
                   for s in strategy_service.active_recipes(product)]

        # ── Phase 7: the Approved Layout Library (manufacturing truth) ──
        from patterns_ai.models import ApprovedLayout
        from patterns_ai.services import layout_library_service as lib
        from patterns_ai.services import marker_generation_service as gen
        from django.urls import reverse
        library_rows = []
        for lay in (ApprovedLayout.objects
                    .filter(product=product)
                    .select_related('candidate__run', 'supersedes',
                                    'approved_by')
                    .order_by('-version_no')[:50]):
            m = gen.derive_candidate_metrics(lay.candidate)
            # M5: the master recognizes markers by their PLAN facts —
            # surface the frozen params (recipe · lay · notes · roll)
            params = lay.candidate.run.params or {}
            library_rows.append({
                'lay': lay, 'metrics': m,
                'stale': lib.layout_is_stale(lay),   # DERIVED (rule 6)
                'pdf_url': reverse('patterns_ai:candidate-pdf',
                                   args=[lay.candidate_id]),
                'print_url': reverse('patterns_ai:candidate-print',
                                     args=[lay.candidate_id]),
                'svg_url': reverse('patterns_ai:candidate-svg',
                                   args=[lay.candidate_id]),
                'recipe': params.get('recipe', ''),
                'notes': params.get('notes', ''),
                'layering_type': params.get('layering_type', ''),
                'roll_label': (params.get('roll') or {}).get('label', '')
                              if isinstance(params.get('roll'), dict)
                              else '',
                # lineage: which asset this one replaced (supersede chain)
                'supersedes_uid': (lay.supersedes.layout_uid
                                   if lay.supersedes_id else ''),
            })
        drafts_count = (GeneratedMarkerCandidate.objects
                        .filter(run__product=product, engine='table')
                        .exclude(library_approvals__isnull=False).count())

        # view/duplicate an approved layout (rule 4: the only read verbs)
        initial = None
        view_mode = False
        loaded_uid = ''
        export_pdf_url = ''
        for param, ro in (('view', True), ('duplicate', False)):
            lid = self.request.GET.get(param)
            if lid:
                lay = get_object_or_404(ApprovedLayout,
                                        pk=_int_or_404(lid),
                                        product=product)
                initial = lay.candidate.placements.get('placements', [])
                view_mode = ro
                loaded_uid = lay.layout_uid
                if ro:
                    export_pdf_url = reverse('patterns_ai:candidate-pdf',
                                             args=[lay.candidate_id])
                break

        return render(request, self.template_name, {
            'product': product,
            'summary': library['summary'],
            'groups': sorted(groups.items()),     # stable group order
            'not_ready': not_ready,
            'confirmed_total': confirmed_total,
            'fabric_width_mm': profile.default_width_mm if profile else None,
            # 6A: spacing rule feeds the collision pipeline (profile default)
            'spacing_mm': (float(profile.default_spacing_mm)
                           if profile and profile.default_spacing_mm
                           else 0.0),
            'workspace_payload': workspace_payload,
            'library_rows': library_rows,
            'drafts_count': drafts_count,
            'initial_placements': initial,
            'view_mode': view_mode,
            'loaded_uid': loaded_uid,
            'export_pdf_url': export_pdf_url,
            # M4 Manufacturing Planner data (rows only; *_json feeds the
            # ws-config hand-off — the template passes DATA, never logic)
            'plan_config': {
                'sizes': ready_sizes, 'rolls': rolls, 'recipes': recipes,
                'sizes_json': _json.dumps(ready_sizes),
                'rolls_json': _json.dumps(rolls),
                'recipes_json': _json.dumps(recipes),
            },
        })


class CuttingTableSaveView(LoginRequiredMixin, _ManagementOnly, View):
    """Phase 7 rule 2 — the ONE save pipeline step: Runtime Session →
    Validation → Candidate (Save Draft). Serializes EXACTLY what the
    operator built (rule 3 — the verifier checks, nothing recomputes).
    Save is NEVER approve (rule 2/8)."""

    def post(self, request, pk):
        import json as _json
        from patterns_ai.services import marker_generation_service as gen
        product = get_object_or_404(Product, pk=pk, is_active=True)
        try:
            body = _json.loads(request.body.decode() or '{}')
            run, candidate = gen.save_table_layout(
                user=request.user, product=product,
                width_mm=body.get('width_mm'),
                height_mm=body.get('height_mm') or 2200,
                spacing_mm=body.get('spacing_mm') or 0.0,
                fabric_group=body.get('fabric_group'),
                placements=body.get('placements'),
                # M4: the Marker Plan persists with the asset
                layering_type=body.get('layering_type') or 'single',
                ratio=body.get('ratio') or {},
                roll_ref=body.get('roll_ref') or None,
                recipe_label=body.get('recipe_label') or '',
                notes=body.get('notes') or '')
        except ValidationError as exc:
            return JsonResponse(
                {'ok': False,
                 'error': '; '.join(getattr(exc, 'messages', None)
                                    or [str(exc)])}, status=400)
        except ValueError:
            return JsonResponse({'ok': False, 'error': 'bad JSON body.'},
                                status=400)
        from django.urls import reverse
        return JsonResponse({
            'ok': True, 'candidate_id': candidate.pk,
            'length_mm': float(candidate.marker_length_mm),
            'approve_url': reverse('patterns_ai:table-approve',
                                   args=[product.pk, candidate.pk]),
        })


class CuttingTableApproveView(LoginRequiredMixin, _ManagementOnly, View):
    """Phase 7 rule 8 — the explicit audited HUMAN act, with the
    summary-BEFORE-approve review step (the proven M7 pattern). GET =
    review; POST = layout_library_service freezes the asset. AI / Auto
    Place / Save can never reach here."""

    def _load(self, pk, cand):
        from patterns_ai.models import GeneratedMarkerCandidate
        product = get_object_or_404(Product, pk=pk, is_active=True)
        candidate = get_object_or_404(
            GeneratedMarkerCandidate.objects.select_related('run__product'),
            pk=cand, run__product=product)
        return product, candidate

    def get(self, request, pk, cand):
        from patterns_ai.models import ApprovedLayout
        from patterns_ai.services import marker_generation_service as gen
        product, candidate = self._load(pk, cand)
        actives = (ApprovedLayout.objects
                   .filter(product=product,
                           status=ApprovedLayout.Status.ACTIVE)
                   .order_by('-version_no'))
        return render(request, 'patterns_ai/dct_approve_confirm.html', {
            'product': product, 'c': candidate,
            'metrics': gen.derive_candidate_metrics(candidate),
            'fabric_group': (candidate.run.params or {}).get(
                'fabric_group', ''),
            'is_table': bool((candidate.run.params or {}).get('table')),
            'verified': bool((candidate.verification or {}).get('ok')),
            'actives': actives,
        })

    def post(self, request, pk, cand):
        from django.urls import reverse
        from patterns_ai.models import ApprovedLayout
        from patterns_ai.services import layout_library_service as lib
        product, candidate = self._load(pk, cand)
        supersedes = None
        sid = request.POST.get('supersedes')
        if sid:
            supersedes = get_object_or_404(ApprovedLayout,
                                           pk=_int_or_404(sid),
                                           product=product)
        try:
            layout = lib.approve_table_layout(
                user=request.user, product=product, candidate=candidate,
                name=request.POST.get('name', ''), supersedes=supersedes)
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
            return redirect(reverse('patterns_ai:table-approve',
                                    args=[product.pk, candidate.pk]))
        messages.success(
            request,
            f'{layout.layout_uid} approved (V{layout.version_no}) — a '
            'frozen manufacturing asset. Nothing edits it; supersede or '
            'archive only.')
        return redirect(reverse('patterns_ai:cutting-table',
                                args=[product.pk]))


class CuttingTableLayoutArchiveView(LoginRequiredMixin, _ManagementOnly,
                                    View):
    """Phase 7 rule 4: Archive — the only other verb."""

    def post(self, request, pk, lid):
        from django.urls import reverse
        from patterns_ai.models import ApprovedLayout
        product = get_object_or_404(Product, pk=pk, is_active=True)
        layout = get_object_or_404(ApprovedLayout, pk=lid, product=product)
        from patterns_ai.services import layout_library_service as lib
        try:
            lib.archive_layout(user=request.user, layout=layout)
            messages.success(request,
                             f'{layout.layout_uid} archived — history '
                             'kept, never deleted.')
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
        return redirect(reverse('patterns_ai:cutting-table',
                                args=[product.pk]))


class ChooseLayoutView(LoginRequiredMixin, _ManagementOnly, View):
    """Phase 8B — the Adda chooses its manufacturing contract(s).

    GET: ACTIVE layouts of the Adda's product grouped by fabric group
    (stale ones shown DISABLED with the LAW-11 reason — loud, not
    hidden) + current usages with the void flow (F1: reason mandatory).
    POST: record / void — layout_usage_service only (the single
    writer). Rule 9 lived: the page offers the LIBRARY, nothing else."""

    def _adda(self, pk):
        from production.models import Adda
        return get_object_or_404(
            Adda.objects.select_related('product'), pk=pk)

    def get(self, request, pk):
        from patterns_ai.models import ApprovedLayout, ApprovedLayoutUsage
        from patterns_ai.services import layout_library_service as lib
        from patterns_ai.services import marker_generation_service as gen
        adda = self._adda(pk)
        usages = (ApprovedLayoutUsage.objects
                  .filter(adda=adda, voided_at__isnull=True)
                  .select_related('layout', 'recorded_by')
                  .order_by('fabric_group'))
        used_groups = {u.fabric_group for u in usages}
        options = []
        for lay in (ApprovedLayout.objects
                    .filter(product=adda.product,
                            status=ApprovedLayout.Status.ACTIVE)
                    .select_related('candidate__run')
                    .order_by('fabric_group', '-version_no')):
            options.append({
                'lay': lay,
                'metrics': gen.derive_candidate_metrics(lay.candidate),
                'stale': lib.layout_is_stale(lay),
                'group_taken': lay.fabric_group in used_groups,
            })
        return render(request, 'patterns_ai/choose_layout.html', {
            'adda': adda, 'usages': usages, 'options': options,
        })

    def post(self, request, pk):
        from django.urls import reverse
        from patterns_ai.models import ApprovedLayout, ApprovedLayoutUsage
        from patterns_ai.services import layout_usage_service as usage_svc
        adda = self._adda(pk)
        action = request.POST.get('action', '')
        try:
            if action == 'record':
                layout = get_object_or_404(
                    ApprovedLayout,
                    pk=_int_or_404(request.POST.get('layout')),
                    product=adda.product)
                u = usage_svc.record_usage(user=request.user, adda=adda,
                                           layout=layout)
                messages.success(
                    request,
                    f'{u.layout.layout_uid} is now the manufacturing '
                    f'contract for {u.fabric_group.upper()} on '
                    f'{adda.code}.')
            elif action == 'void':
                usage = get_object_or_404(
                    ApprovedLayoutUsage,
                    pk=_int_or_404(request.POST.get('usage')), adda=adda)
                usage_svc.void_usage(user=request.user, usage=usage,
                                     reason=request.POST.get('reason', ''))
                messages.success(request,
                                 'usage voided — history kept forever.')
            else:
                messages.error(request, 'Unknown action.')
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
        return redirect(reverse('patterns_ai:choose-layout',
                                args=[adda.pk]))


class CuttingTableOptimizeView(LoginRequiredMixin, _ManagementOnly, View):
    """Phase 6C — AI Optimize, STATELESS (owner rules 2/3/7).

    THE OPTIMIZATION CONTRACT (frozen): input = canvas (width/height/
    spacing) + pieces (absolute polygon_mm + locked/rotation/mirrored/
    allow_180) + constraints; output = piece positions. Nothing else —
    no rendering, no UI, no persistence. Locked pieces = absolute fixed
    obstacles (rule 4). Reuses the EXISTING engine verbatim
    (marker_generation_service.optimize_layout → nest op:'optimize' —
    WRITES NOTHING, test-walled); grain: strict → allow_180 False,
    two_way/free → 0/180 (free's 90/270 = a safe unused subset, engine
    extension only if ever needed — never a fork)."""

    def post(self, request, pk):
        import json as _json
        from patterns_ai.services import marker_generation_service as gen
        product = get_object_or_404(Product, pk=pk, is_active=True)
        try:
            body = _json.loads(request.body.decode() or '{}')
            result = gen.optimize_layout(
                user=request.user,
                width_mm=body.get('width_mm'),
                height_mm=body.get('height_mm') or 2200,
                spacing_mm=body.get('spacing_mm') or 0.0,
                placements=body.get('placements'),
                options_wanted=3, effort=body.get('effort') or 'fast')
        except ValidationError as exc:
            return JsonResponse(
                {'ok': False,
                 'error': '; '.join(getattr(exc, 'messages', None)
                                    or [str(exc)])}, status=400)
        except ValueError:
            return JsonResponse({'ok': False, 'error': 'bad JSON body.'},
                                status=400)
        result['product'] = product.pk
        return JsonResponse(result)


class PieceListView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """PDM W2R — the LOCKED two-page workflow:
    `?product=N`         → the PRODUCT PATTERN MANAGER (sizes only:
                           verdict cards, +Add Size hand-off, gated
                           Cutting-Table entry — NO design rows);
    `?product=N&size=l`  → the PATTERN DESIGN LIBRARY for ONE size
                           (the Design-Row atoms, issues first).
    GET derives everything from the read-only facade; POST only
    orchestrates the frozen single-writer services (unchanged)."""
    template_name = 'patterns_ai/piece_list.html'

    def get_template_names(self):
        if (self.request.GET.get('product')
                and self.request.GET.get('size')):
            return ['patterns_ai/size_library.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        from django.http import Http404
        from django.urls import reverse
        from patterns_ai.models import PatternPiece
        from patterns_ai.services import pattern_design_facade as facade
        from patterns_ai.services.svg_render import outline_preview_svg
        ctx = super().get_context_data(**kwargs)
        product = None
        pid = self.request.GET.get('product')
        if pid:
            product = get_object_or_404(Product, pk=_int_or_404(pid),
                                        is_active=True)
        if product is None:
            # Rule C: no product context yet → a chooser, never a filter
            ctx.update({'product': None,
                        'all_products': Product.objects.filter(
                            is_active=True).order_by('code')})
            return ctx
        library = facade.product_design_library(product)
        ctx.update({'product': product, 'library': library,
                    'summary': library['summary']})

        size_code = self.request.GET.get('size')
        if not size_code:
            # ── the MANAGER: size verdict cards only ──
            ctx['hub'] = _hub_readiness(product)      # matrix power lens
            return ctx

        # ── the LIBRARY: exactly one size, rows enriched ──
        section = next((s for s in library['sections']
                        if s['size'].code == size_code), None)
        if section is None:
            raise Http404('unknown size for this product')
        pieces = {p.pk: p for p in
                  PatternPiece.objects.filter(product=product)
                  .prefetch_related('versions')}
        for row in section['rows']:
            row['preview_svg'] = outline_preview_svg(row['outline_mm'])
            piece = pieces[row['piece_id']]
            if row['status'] == 'confirmed' and row['version_id']:
                url = reverse('patterns_ai:version-detail',
                              args=[row['version_id']])
            elif row['status'] == 'draft':
                draft = piece.versions.filter(status='draft').first()
                url = reverse('patterns_ai:version-detail',
                              args=[draft.pk])
            else:
                url = reverse('patterns_ai:piece-detail',
                              args=[row['piece_id']])
            row['edit_url'] = f"{url}#size-{row['size_id']}"
            row['dxf_url'] = (reverse('patterns_ai:geometry-dxf',
                                      args=[row['geometry_row_id']])
                              if row['geometry_row_id'] else None)
            row['piece'] = piece            # manage-in-place forms
        # W2R2 preparation buckets — todo-first (Trello order):
        # ✖ Missing → ⚠ Needs Work (drafts) → ✓ Completed
        buckets = [
            {'key': 'missing', 'icon': '✖', 'label': 'Missing',
             'rows': [r for r in section['rows']
                      if r['status'] == 'missing']},
            {'key': 'work', 'icon': '⚠', 'label': 'Needs Work',
             'rows': [r for r in section['rows']
                      if r['status'] == 'draft']},
            {'key': 'done', 'icon': '✓', 'label': 'Completed',
             'rows': [r for r in section['rows']
                      if r['status'] == 'confirmed']},
        ]
        ctx['section'] = section
        ctx['buckets'] = buckets
        return ctx

    def post(self, request):
        """Hub actions — every write goes through a frozen M3 writer."""
        from patterns_ai.models import PatternPiece
        from patterns_ai.services import capture_service
        from patterns_ai.services import fabric_profile_service as fps
        from patterns_ai.services import pattern_geometry_service as geo
        product = get_object_or_404(
            Product, pk=_int_or_404(request.POST.get('product')),
            is_active=True)
        action = request.POST.get('action', '')
        back = redirect(f"{request.path}?product={product.pk}")

        def _piece():
            piece = get_object_or_404(
                PatternPiece, pk=_int_or_404(request.POST.get('piece')))
            if piece.product_id != product.pk:      # tamper wall
                from django.http import Http404
                raise Http404
            return piece

        try:
            # Phase 2 (frozen resp. #1): set_optional moved to the
            # Blueprint module — the Manager surface never edits rules.
            if action == 'start_universal':
                # Phase-3 D-1 explicit moment: one-tap Universal for a
                # sizeless product (production-owned writer, D-2; POST
                # only — GET stays write-free).
                from production.services.product_size_service import (
                    ensure_universal_size)
                size = ensure_universal_size(product)
                messages.success(request,
                                 f'"{size.label}" size ready — prepare its '
                                 'Pattern Designs.')
            elif action == 'upload_reference':
                piece = _piece()
                upload = request.FILES.get('reference')
                if upload is None:
                    messages.error(request, 'choose an image first.')
                    return back
                from patterns_ai.models import CaptureAsset
                asset = capture_service.store_capture(
                    user=request.user, product=product,
                    uploaded_file=upload, source='gallery',
                    kind=CaptureAsset.Kind.REFERENCE_IMAGE)
                geo.set_reference_image(user=request.user, piece=piece,
                                        asset=asset)
                messages.success(request, f'Reference image set for '
                                          f'{piece.pattern.name}.')
            elif action == 'clear_reference':
                piece = _piece()
                geo.set_reference_image(user=request.user, piece=piece,
                                        asset=None)
                messages.success(request, f'Reference image removed from '
                                          f'{piece.pattern.name}.')
            elif action == 'save_profile':
                def _num(name):
                    raw = (request.POST.get(name) or '').strip()
                    return raw or None
                fps.set_fabric_profile(
                    user=request.user, product=product,
                    default_width_mm=_num('default_width_mm'),
                    default_length_mm=_num('default_length_mm'),
                    default_spacing_mm=_num('default_spacing_mm'),
                    fabric_type=request.POST.get('fabric_type', ''),
                    gsm=_num('gsm'),
                    lay_mode=request.POST.get('lay_mode', ''))
                messages.success(request, 'Fabric defaults saved — they '
                                          'prefill NEW generations only.')
            else:
                messages.error(request, 'unknown action.')
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
        return back


# Phase 2 (frozen resp. #1): PieceCreateView retired — piece registration
# lives in the Blueprint module (register_pattern_definition, the ONLY
# public write API for Pattern Definitions).


class PieceDetailView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    template_name = 'patterns_ai/piece_detail.html'

    def get_context_data(self, **kwargs):
        from patterns_ai.models import PatternPiece
        ctx = super().get_context_data(**kwargs)
        piece = get_object_or_404(
            PatternPiece.objects.select_related('product', 'pattern'),
            pk=kwargs['pk'])
        versions = (piece.versions
                    .select_related('confirmed_by', 'set_label')
                    .prefetch_related('size_geometries__size')
                    .order_by('-version_no'))
        extractions = (piece.extractions
                       .select_related('size', 'capture')
                       .order_by('-id')[:20])
        ctx.update({'piece': piece, 'versions': versions,
                    'extractions': extractions,
                    'sizes': piece.product.sizes.filter(is_active=True)
                                  .order_by('display_order'),
                    'mats_active': _active_mats()})
        return ctx


def _active_mats():
    from patterns_ai.models import CalibrationMat
    return CalibrationMat.objects.filter(
        status=CalibrationMat.Status.ACTIVE).order_by('mat_code')


class PatternCaptureView(LoginRequiredMixin, _ManagementOnly, View):
    """Phone capture wizard: photo ON the mat -> stored capture -> gated
    extraction -> annotator. One transaction: no orphan rows on failure."""
    template_name = 'patterns_ai/capture_form.html'

    def _ctx(self, piece, form, preselect_size=None):
        return {'piece': piece, 'form': form,
                'sizes': piece.product.sizes.filter(is_active=True)
                              .order_by('display_order'),
                'mats': _active_mats(),
                # M2 §2.5: the Studio's phone hand-off preselects the size
                'preselect_size': preselect_size}

    def get(self, request, pk):
        from patterns_ai.forms import PatternCaptureForm
        from patterns_ai.models import PatternPiece
        piece = get_object_or_404(
            PatternPiece.objects.select_related('product', 'pattern'), pk=pk)
        raw = request.GET.get('size', '')
        return render(request, self.template_name,
                      self._ctx(piece, PatternCaptureForm(),
                                int(raw) if raw.isdigit() else None))

    def post(self, request, pk):
        from production.models import ProductSize
        from patterns_ai.forms import PatternCaptureForm
        from patterns_ai.models import CalibrationMat, CaptureAsset, PatternPiece
        from patterns_ai.services import (capture_service,
                                          pattern_geometry_service as geo)
        piece = get_object_or_404(
            PatternPiece.objects.select_related('product', 'pattern'), pk=pk)
        form = PatternCaptureForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, self._ctx(piece, form))
        size = get_object_or_404(
            ProductSize, pk=_int_or_404(request.POST.get('size')),
            product=piece.product)
        mat = get_object_or_404(
            CalibrationMat, pk=_int_or_404(request.POST.get('mat')))
        try:
            with transaction.atomic():
                asset = capture_service.store_capture(
                    user=request.user, product=piece.product,
                    uploaded_file=form.cleaned_data['photo'],
                    source=form.cleaned_data['source'],
                    kind=CaptureAsset.Kind.PATTERN_CAPTURE, mat=mat,
                    metadata=capture_service.extract_exif_metadata(
                        form.cleaned_data['photo']))
                # M2: the photo joins the piece×size Evidence Stack — same
                # transaction, same acquisition contract as every adapter
                from patterns_ai.services import acquisition_service
                evidence = acquisition_service.create_photo_evidence(
                    user=request.user, piece=piece, size=size,
                    capture=asset)
                extraction = geo.run_extraction(
                    user=request.user, capture=asset, piece=piece,
                    size=size, evidence=evidence)
                acquisition_service.record_verdict(evidence, extraction)
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                form.add_error(None, m)
            return render(request, self.template_name, self._ctx(piece, form))
        if extraction.gate.get('passed'):
            messages.success(request, 'Captured — review the proposal below.')
        else:
            messages.error(request, 'Capture REFUSED by the quality gate — '
                                    'reasons recorded below. Retake.')
        return redirect('patterns_ai:extraction-review', pk=extraction.pk)


class ExtractionReviewView(LoginRequiredMixin, _ManagementOnly, View):
    """The annotator: original vs proposal overlay + gate metrics +
    component confidence; HUMAN accept / reject-with-reason."""
    template_name = 'patterns_ai/extraction_review.html'

    def _ctx(self, extraction):
        from patterns_ai.services.svg_render import geometry_svg
        svg = (geometry_svg(extraction.geometry)
               if extraction.geometry else None)
        return {'x': extraction, 'svg': svg,
                'piece': extraction.piece, 'capture': extraction.capture}

    def get(self, request, pk):
        from patterns_ai.models import GeometryExtraction
        extraction = get_object_or_404(
            GeometryExtraction.objects.select_related(
                'piece__product', 'piece__pattern', 'size', 'capture'),
            pk=pk)
        return render(request, self.template_name, self._ctx(extraction))

    def post(self, request, pk):
        from patterns_ai.models import GeometryExtraction
        from patterns_ai.services import pattern_geometry_service as geo
        extraction = get_object_or_404(
            GeometryExtraction.objects.select_related(
                'piece__product', 'size', 'capture'), pk=pk)
        action = request.POST.get('action')
        try:
            if action == 'accept':
                row = geo.accept_extraction(user=request.user,
                                            extraction=extraction)
                messages.success(
                    request,
                    f'Accepted into draft v{row.version.version_no} '
                    f'({extraction.size.code}).')
                return redirect('patterns_ai:version-detail',
                                pk=row.version_id)
            geo.reject_extraction(user=request.user, extraction=extraction,
                                  reason=request.POST.get('reason', ''))
            messages.success(request, 'Proposal rejected — recorded.')
            return redirect('patterns_ai:piece-detail',
                            pk=extraction.piece_id)
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
            return redirect('patterns_ai:extraction-review', pk=pk)


class VersionDetailView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    template_name = 'patterns_ai/version_detail.html'

    def get_context_data(self, **kwargs):
        from patterns_ai.models import PatternPieceVersion
        from patterns_ai.services.svg_render import geometry_svg
        ctx = super().get_context_data(**kwargs)
        version = get_object_or_404(
            PatternPieceVersion.objects.select_related(
                'piece__product', 'piece__pattern', 'confirmed_by',
                'set_label', 'superseded_by'),
            pk=kwargs['pk'])
        rows = []
        for row in (version.size_geometries.select_related(
                'size', 'source_extraction', 'copied_from')
                .order_by('size__display_order')):
            rows.append({'row': row, 'svg': geometry_svg(row.geometry),
                         'grain': (row.geometry.get('features') or {})
                                  .get('grain')})
        ctx.update({'version': version, 'rows': rows,
                    'piece': version.piece, 'is_draft':
                        version.status == version.Status.DRAFT})
        return ctx


class VersionConfirmView(LoginRequiredMixin, _ManagementOnly, View):
    def post(self, request, pk):
        from patterns_ai.models import PatternPieceVersion
        from patterns_ai.services import pattern_geometry_service as geo
        version = get_object_or_404(PatternPieceVersion, pk=pk)
        grain, tape = {}, {}
        for row in version.size_geometries.select_related('size'):
            g = request.POST.get(f'grain_{row.size_id}', '').strip()
            if g:
                try:
                    grain[row.size_id] = int(round(float(g) * 100))
                except ValueError:
                    messages.error(request,
                                   f'grain for {row.size.code}: not a number')
                    return redirect('patterns_ai:version-detail', pk=pk)
            w = request.POST.get(f'tape_w_{row.size_id}', '').strip()
            h = request.POST.get(f'tape_h_{row.size_id}', '').strip()
            if w and h:
                try:
                    tape[row.size_id] = {'width_mm': float(w),
                                         'height_mm': float(h)}
                except ValueError:
                    messages.error(request,
                                   f'tape for {row.size.code}: not numbers')
                    return redirect('patterns_ai:version-detail', pk=pk)
        try:
            geo.confirm_version(user=request.user, version=version,
                                grain_by_size=grain, tape_by_size=tape)
            messages.success(request,
                             f'v{version.version_no} CONFIRMED — geometry is '
                             'now permanent knowledge.')
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
        return redirect('patterns_ai:version-detail', pk=pk)


class VersionRejectView(LoginRequiredMixin, _ManagementOnly, View):
    def post(self, request, pk):
        from patterns_ai.models import PatternPieceVersion
        from patterns_ai.services import pattern_geometry_service as geo
        version = get_object_or_404(PatternPieceVersion, pk=pk)
        try:
            geo.reject_version(user=request.user, version=version,
                               reason=request.POST.get('reason', ''))
            messages.success(request, f'v{version.version_no} rejected.')
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
        return redirect('patterns_ai:version-detail', pk=pk)


class VersionStartNextView(LoginRequiredMixin, _ManagementOnly, View):
    def post(self, request, pk):
        from patterns_ai.models import PatternPiece
        from patterns_ai.services import pattern_geometry_service as geo
        piece = get_object_or_404(PatternPiece, pk=pk)
        try:
            draft = geo.start_next_version(user=request.user, piece=piece)
            messages.success(request,
                             f'Draft v{draft.version_no} created — carried '
                             f'{draft.size_geometries.count()} size(s) forward.')
            return redirect('patterns_ai:version-detail', pk=draft.pk)
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
            return redirect('patterns_ai:piece-detail', pk=piece.pk)


class GeometryEditorView(LoginRequiredMixin, _ManagementOnly, View):
    """Draft-only vertex editor (vanilla JS on the inline SVG); the service
    re-validates every rule server-side."""
    template_name = 'patterns_ai/geometry_edit.html'

    def _row(self, pk):
        from patterns_ai.models import PieceSizeGeometry
        return get_object_or_404(
            PieceSizeGeometry.objects.select_related(
                'version__piece__pattern', 'version__piece__product', 'size'),
            pk=pk)

    def get(self, request, pk):
        import json as _json
        row = self._row(pk)
        return render(request, self.template_name,
                      {'row': row, 'version': row.version,
                       'geometry_json': _json.dumps(row.geometry)})

    def post(self, request, pk):
        import json as _json
        from patterns_ai.services import pattern_geometry_service as geo
        row = self._row(pk)
        try:
            outer = _json.loads(request.POST.get('outer_um', '[]'))
            grain = request.POST.get('grain_cdeg') or None
            # adr-c.2: notch markers ride the same save (absent = unchanged)
            raw_notches = request.POST.get('notches')
            notches = _json.loads(raw_notches) if raw_notches else None
            # adr-c.3: fold edge — absent = unchanged · 'null' = clear
            raw_fe = request.POST.get('fold_edge')
            fold_edge = _json.loads(raw_fe) if raw_fe else ...
            geo.edit_draft_geometry(
                user=request.user, version=row.version, size=row.size,
                outer_um=outer,
                grain_cdeg=int(grain) if grain else None,
                notches=notches, fold_edge=fold_edge)
            messages.success(request, 'Draft geometry updated.')
            return redirect('patterns_ai:version-detail', pk=row.version_id)
        except _json.JSONDecodeError:
            messages.error(request, 'bad vertex payload')
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
        return redirect('patterns_ai:geometry-edit', pk=pk)


class GeometrySvgView(LoginRequiredMixin, _ManagementOnly, View):
    """SVG export (ADR-C guaranteed): download, true-scale mm."""

    def get(self, request, pk):
        from django.http import HttpResponse
        from patterns_ai.models import PieceSizeGeometry
        from patterns_ai.services.svg_render import geometry_svg
        row = get_object_or_404(
            PieceSizeGeometry.objects.select_related(
                'version__piece__pattern', 'size'), pk=pk)
        svg = geometry_svg(row.geometry, true_scale=True)
        resp = HttpResponse(svg, content_type='image/svg+xml')
        resp['Content-Disposition'] = (
            f'attachment; filename="{row.version.piece.pattern.name}'
            f'_{row.size.code}_v{row.version.version_no}.svg"')
        return resp


class GeometryDxfView(LoginRequiredMixin, _ManagementOnly, View):
    """DXF-AAMA export via the isolated runtime."""

    def get(self, request, pk):
        from django.http import HttpResponse
        from patterns_ai.models import PieceSizeGeometry
        from patterns_ai.services import pattern_geometry_service as geo
        row = get_object_or_404(
            PieceSizeGeometry.objects.select_related(
                'version__piece__pattern', 'size'), pk=pk)
        try:
            data = geo.export_dxf_bytes(row)
        except ValidationError as exc:
            messages.error(request, '; '.join(
                getattr(exc, 'messages', None) or [str(exc)]))
            return redirect('patterns_ai:version-detail', pk=row.version_id)
        resp = HttpResponse(data, content_type='application/dxf')
        resp['Content-Disposition'] = (
            f'attachment; filename="{row.version.piece.pattern.name}'
            f'_{row.size.code}_v{row.version.version_no}.dxf"')
        return resp


class GeometryPrintView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """Gate-1 overlay: true-scale print — lay the printout over the
    cardboard and the lines must match. Audit-close 2026-07-11: pieces
    larger than one sheet TILE on the exact candidate-print grid
    (numbered windows, 10 mm dashed overlap match lines, per-tile scale
    bar) — the real Body (350×510 mm) exposed the single-sheet limit."""
    template_name = 'patterns_ai/geometry_print.html'

    STEP_W, STEP_H = 180.0, 267.0        # window − 10 mm overlap
    WIN_W, WIN_H = 190.0, 277.0          # A4 printable window

    def get_context_data(self, **kwargs):
        import math
        from patterns_ai.models import PieceSizeGeometry
        from patterns_ai.services.svg_render import marker_tile_svg
        from patterns_ai.services.units import um_to_mm
        ctx = super().get_context_data(**kwargs)
        row = get_object_or_404(
            PieceSizeGeometry.objects.select_related(
                'version__piece__pattern', 'version__piece__product', 'size'),
            pk=kwargs['pk'])
        outer = row.geometry['outer']
        w_mm = float(um_to_mm(max(p[0] for p in outer)))
        h_mm = float(um_to_mm(max(p[1] for p in outer)))
        # one piece as a tile-plane "placement": tile svg draws (u, v) =
        # (ring[1], ring[0]); canonical y-up flips to page-down v
        ring = [[h_mm - float(um_to_mm(y)), float(um_to_mm(x))]
                for x, y in outer]
        placement = [{'polygon_mm': ring,
                      'key': row.version.piece.pattern.name,
                      'instance': 0}]
        cols = max(1, math.ceil(w_mm / self.STEP_W))
        rows = max(1, math.ceil(h_mm / self.STEP_H))
        tiles = []
        for r in range(rows):
            for c in range(cols):
                tiles.append({
                    'label': f'C{c + 1}-R{r + 1}',
                    'col': c + 1, 'row': r + 1,
                    'svg': marker_tile_svg(
                        placement, w_mm, h_mm,
                        c * self.STEP_W, r * self.STEP_H,
                        self.WIN_W, self.WIN_H)})
        ctx.update({'row': row, 'w_mm': round(w_mm, 1),
                    'h_mm': round(h_mm, 1),
                    'tiles': tiles, 'cols': cols, 'rows': rows})
        return ctx


class DxfImportView(LoginRequiredMixin, _ManagementOnly, View):
    template_name = 'patterns_ai/dxf_import_form.html'

    def _piece(self, pk):
        from patterns_ai.models import PatternPiece
        return get_object_or_404(
            PatternPiece.objects.select_related('product', 'pattern'), pk=pk)

    def _ctx(self, piece, form):
        return {'piece': piece, 'form': form,
                'sizes': piece.product.sizes.filter(is_active=True)
                              .order_by('display_order')}

    def get(self, request, pk):
        from patterns_ai.forms import DxfImportForm
        piece = self._piece(pk)
        return render(request, self.template_name,
                      self._ctx(piece, DxfImportForm()))

    def post(self, request, pk):
        import tempfile
        from pathlib import Path
        from production.models import ProductSize
        from patterns_ai.forms import DxfImportForm
        from patterns_ai.services import pattern_geometry_service as geo
        piece = self._piece(pk)
        form = DxfImportForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, self._ctx(piece, form))
        size = get_object_or_404(
            ProductSize, pk=_int_or_404(request.POST.get('size')),
            product=piece.product)
        try:
            with tempfile.TemporaryDirectory(prefix='pai_dxfup_') as td:
                p = Path(td) / 'upload.dxf'
                with open(p, 'wb') as fh:
                    for chunk in form.cleaned_data['dxf_file'].chunks():
                        fh.write(chunk)
                row = geo.import_dxf(user=request.user, piece=piece,
                                     size=size, dxf_path=p)
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                form.add_error(None, m)
            return render(request, self.template_name, self._ctx(piece, form))
        messages.success(request,
                         f'DXF imported into draft v{row.version.version_no} '
                         f'({size.code}) — trust: uncalibrated until '
                         'tape-accepted at confirm.')
        return redirect('patterns_ai:version-detail', pk=row.version_id)


# ════════════════════════════════════════════════════════════════════════════
# P3 — Marker Generation & Optimization. parse -> gate -> delegate;
# marker_generation_service owns every rule.
# ════════════════════════════════════════════════════════════════════════════


class GenerateMarkerView(LoginRequiredMixin, _ManagementOnly, View):
    """Run form + synchronous generation (timeboxed engines)."""
    template_name = 'patterns_ai/generate_form.html'

    def _ctx(self, product, extra=None):
        from patterns_ai.models import MarkerGenerationRun
        ctx = {'product': product,
               'all_products': Product.objects.filter(is_active=True)
                                              .order_by('code'),
               'sizes': (product.sizes.filter(is_active=True)
                         .order_by('display_order') if product else []),
               'runs': (MarkerGenerationRun.objects
                        .filter(product=product)
                        .prefetch_related('candidates')
                        .order_by('-id')[:10] if product else []),
               # §3b/§2d Rule L: incompleteness visible BEFORE the click
               'hub': _hub_readiness(product) if product else None}
        ctx.update(extra or {})
        return ctx

    def get(self, request):
        product = None
        pid = request.GET.get('product')
        if pid:
            product = get_object_or_404(Product, pk=_int_or_404(pid),
                                        is_active=True)
        # Rule G (§2c): profile = PREFILL ONLY, and only for NEW work —
        # this form. Saved layouts always display their own stored values.
        extra = {}
        if product is not None:
            from patterns_ai.models import ProductFabricProfile
            profile = ProductFabricProfile.objects.filter(
                product=product).first()
            if profile is not None:
                extra = {'prefill_width': profile.default_width_mm or '',
                         'prefill_spacing': profile.default_spacing_mm or ''}
        return render(request, self.template_name,
                      self._ctx(product, extra))

    def post(self, request):
        from patterns_ai.services import marker_generation_service as gen
        from patterns_ai.services.compute_bridge import ComputeError
        product = get_object_or_404(
            Product, pk=_int_or_404(request.POST.get('product')),
            is_active=True)
        ratio = {}
        for size in product.sizes.filter(is_active=True):
            raw = (request.POST.get(f'count_{size.pk}') or '').strip()
            if raw:
                try:
                    n = int(raw)
                except ValueError:
                    messages.error(request,
                                   f'{size.label}: count must be a number')
                    return render(request, self.template_name,
                                  self._ctx(product))
                if n > 0:
                    ratio[size] = n
        try:
            width = int(request.POST.get('usable_width_mm', ''))
            spacing = float(request.POST.get('spacing_mm', '3') or 3)
        except ValueError:
            messages.error(request, 'width/spacing must be numbers')
            return render(request, self.template_name, self._ctx(product))
        try:
            run, rows = gen.start_run(
                user=request.user, product=product, usable_width_mm=width,
                ratio=ratio, spacing_mm=spacing,
                engine=request.POST.get('engine', 'auto'))
        except ComputeError as exc:
            messages.error(request, str(exc))
            return render(request, self.template_name, self._ctx(product))
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
            return render(request, self.template_name, self._ctx(product))
        messages.success(request,
                         f'{len(rows)} layout option(s) ready — each '
                         'independently checked.')
        return redirect('patterns_ai:generation-run', pk=run.pk)


class GenerationRunView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """Candidate comparison for one run — scores derived at read."""
    template_name = 'patterns_ai/generation_run.html'

    def get_context_data(self, **kwargs):
        from patterns_ai.models import MarkerGenerationRun
        from patterns_ai.services import marker_generation_service as gen
        ctx = super().get_context_data(**kwargs)
        run = get_object_or_404(
            MarkerGenerationRun.objects.select_related('product'),
            pk=kwargs['pk'])
        cards = []
        for c in run.candidates.all().order_by('marker_length_mm'):
            cards.append({'c': c,
                          'metrics': gen.derive_candidate_metrics(c),
                          'promoted': c.promoted_markers.first()})
        ctx.update({'run': run, 'cards': cards,
                    'ratio_labels': _ratio_labels(run)})
        return ctx


def _ratio_labels(run):
    from production.models import ProductSize
    out = []
    for sid, count in (run.params.get('ratio') or {}).items():
        size = ProductSize.objects.filter(pk=int(sid)).first()
        out.append(f'{size.label if size else sid}×{count}')
    return out


class CandidateDetailView(LoginRequiredMixin, _ManagementOnly, View):
    """Visualization + benchmark + the promotion decision."""
    template_name = 'patterns_ai/candidate_detail.html'

    def _ctx(self, candidate):
        from patterns_ai.models import ProductionLayout
        from patterns_ai.services import marker_generation_service as gen
        from patterns_ai.services.svg_render import marker_svg
        bench = gen.benchmark_candidate(candidate)
        svg = marker_svg(candidate.placements['placements'],
                         candidate.run.usable_width_mm,
                         float(candidate.marker_length_mm))
        # M7 (§3f/§3g): the designation + the Production Layout Summary
        # (facts + derived-at-read — nothing stored)
        designation = (ProductionLayout.objects
                       .filter(product=candidate.run.product)
                       .select_related('approved_by').first())
        return {'c': candidate, 'run': candidate.run, 'bench': bench,
                'metrics': bench['metrics'], 'svg': svg,
                'promoted': candidate.promoted_markers.first(),
                'ratio_labels': _ratio_labels(candidate.run),
                'designation': designation,
                'is_production': bool(
                    designation
                    and designation.approved_layout_id == candidate.pk)}

    def _candidate(self, pk):
        from patterns_ai.models import GeneratedMarkerCandidate
        return get_object_or_404(
            GeneratedMarkerCandidate.objects.select_related('run__product'),
            pk=pk)

    def get(self, request, pk):
        return render(request, self.template_name,
                      self._ctx(self._candidate(pk)))

    def post(self, request, pk):
        from patterns_ai.services import marker_generation_service as gen
        candidate = self._candidate(pk)
        try:
            marker, bench = gen.promote_candidate(
                user=request.user, candidate=candidate,
                label=request.POST.get('label', '').strip(),
                notes=request.POST.get('notes', '').strip())
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
            return render(request, self.template_name, self._ctx(candidate))
        messages.success(
            request,
            f'Promoted as {marker.reference} (benchmark verdict: '
            f"{bench['verdict']}). It now lives in the Marker Library.")
        return redirect('patterns_ai:marker-detail',
                        reference=marker.reference)


class CandidateSvgView(LoginRequiredMixin, _ManagementOnly, View):
    """Download the layout SVG (derived from stored placements)."""

    def get(self, request, pk):
        from django.http import HttpResponse
        from patterns_ai.models import GeneratedMarkerCandidate
        from patterns_ai.services.svg_render import marker_svg
        c = get_object_or_404(
            GeneratedMarkerCandidate.objects.select_related('run__product'),
            pk=pk)
        # M8 (§3f): the downloaded artifact carries the summary as
        # <metadata>/<desc> — the drawable content is unchanged.
        svg = marker_svg(c.placements['placements'],
                         c.run.usable_width_mm, float(c.marker_length_mm),
                         summary=_export_summary(c, request.user))
        resp = HttpResponse(svg, content_type='image/svg+xml')
        resp['Content-Disposition'] = (
            f'attachment; filename="candidate_{c.pk}_{c.engine}.svg"')
        return resp


# ════════════════════════════════════════════════════════════════════════════
# P4 — The Cut Advisor. advisor_service = read-only brain;
# suggestion_service = the single writer of the decision spine.
# ════════════════════════════════════════════════════════════════════════════


class AdvisorView(LoginRequiredMixin, _ManagementOnly, View):
    """One coherent assistant surface: evidence-backed recommendation +
    the human decision bar + the append-only suggestion history."""
    template_name = 'patterns_ai/advisor.html'

    def _ctx(self, request):
        from patterns_ai.models import SuggestionEvent
        from patterns_ai.services import advisor_service as adv
        products = (Product.objects
                    .filter(is_active=True, markers__isnull=False)
                    .distinct().order_by('code'))
        product = None
        pid = request.GET.get('product') or request.POST.get('product')
        if pid:
            product = get_object_or_404(Product, pk=_int_or_404(pid),
                                        is_active=True)
        elif products:
            product = products[0]
        width_raw = (request.GET.get('width_mm')
                     or request.POST.get('width_mm') or '').strip()
        width_mm = None
        if width_raw:
            try:
                width_mm = int(width_raw)
            except ValueError:
                messages.error(request, 'width must be a number (mm)')
        rec = adv.recommend(product, width_mm=width_mm) if product else None
        history = (SuggestionEvent.objects
                   .filter(product=product)
                   .select_related('decided_by', 'created_by')
                   .order_by('-id')[:10]) if product else []
        return {'products': products, 'product': product,
                'width_mm': width_mm, 'rec': rec, 'history': history}

    def get(self, request):
        return render(request, self.template_name, self._ctx(request))

    def post(self, request):
        """Two actions: 'offer' (record the shown snapshot) and
        'decide_<pk>' (the one-shot human verdict)."""
        from django.urls import reverse
        from patterns_ai.models import SuggestionEvent
        from patterns_ai.services import advisor_service as adv
        from patterns_ai.services import suggestion_service as sug
        action = request.POST.get('action', '')
        ctx = self._ctx(request)
        try:
            if action == 'offer':
                if not ctx['rec']:
                    raise ValidationError('pick a product first.')
                event = sug.record_offer(
                    user=request.user, product=ctx['product'],
                    payload=adv.offer_payload(ctx['rec']),
                    source=ctx['rec']['advisor_version'])
                messages.success(request,
                                 f'Suggestion #{event.pk} recorded — now '
                                 'record your decision on it.')
            elif action.startswith('decide_'):
                event = get_object_or_404(
                    SuggestionEvent, pk=_int_or_404(action.split('_', 1)[1]),
                    product=ctx['product'])
                sug.decide(user=request.user, event=event,
                           outcome=request.POST.get('outcome', ''),
                           reason=request.POST.get('reason', ''))
                messages.success(request, f'Decision recorded on #{event.pk}.')
            else:
                messages.error(request, 'unknown action')
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
        except ValueError:
            messages.error(request, 'bad decision payload')
        url = reverse('patterns_ai:advisor') + f"?product={ctx['product'].pk}"
        if ctx['width_mm']:
            url += f"&width_mm={ctx['width_mm']}"
        return redirect(url)


# ════════════════════════════════════════════════════════════════════════════
# P5 — Management Insights (read-only executive dashboard).
# ════════════════════════════════════════════════════════════════════════════


class InsightsView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """Executive dashboard — every number derived at read from immutable
    facts via intelligence_service (SELECT-only, test-walled)."""
    template_name = 'patterns_ai/insights.html'

    def get_context_data(self, **kwargs):
        from patterns_ai.services import intelligence_service as intel
        ctx = super().get_context_data(**kwargs)
        ctx['dash'] = intel.executive_dashboard()
        return ctx


# ════════════════════════════════════════════════════════════════════════════
# Phase 4 (ROADMAP_V2) — Interactive Marker Workspace.
# ════════════════════════════════════════════════════════════════════════════


class WorkspaceView(LoginRequiredMixin, _ManagementOnly, View):
    """The interactive canvas over a candidate layout. GET renders the
    workspace; POST = save_manual_layout (single writer) -> the new
    immutable manual candidate. Reload = open any candidate here."""
    template_name = 'patterns_ai/workspace.html'

    def _candidate(self, pk):
        from patterns_ai.models import GeneratedMarkerCandidate
        return get_object_or_404(
            GeneratedMarkerCandidate.objects.select_related('run__product'),
            pk=pk)

    def get(self, request, pk):
        import json as _json
        from patterns_ai.models import (GeneratedMarkerCandidate,
                                        ProductionLayout)
        from production.models import ProductSize
        c = self._candidate(pk)
        height = (c.run.params.get('height_mm')
                  or int(float(c.marker_length_mm) * 1.2) + 200)
        # Rule D context strip (§2b): read-only labels from stored FACTS
        # (ratio/width live in run params; ★ = the designation pointer).
        ratio = c.run.params.get('ratio') or {}
        sizes = ProductSize.objects.in_bulk(
            [int(k) for k in ratio.keys() if str(k).isdigit()])
        pairs = sorted(
            (s.display_order, s.label, int(ratio[str(spk)]))
            for spk, s in sizes.items())
        designation = ProductionLayout.objects.filter(
            product=c.run.product).first()
        # Rule F switcher data: ★ production → drafts NEWEST-FIRST →
        # "＋ Generate New" (markup order = the rule, structurally).
        production_pk = designation.approved_layout_id if designation else None
        drafts = list(GeneratedMarkerCandidate.objects
                      .filter(run__product=c.run.product)
                      .exclude(pk=production_pk or 0)
                      .order_by('-pk').values_list('pk', flat=True))
        return render(request, self.template_name, {
            'c': c, 'run': c.run, 'product': c.run.product,
            'ratio_display': ' · '.join(f'{lbl}×{n}' for _o, lbl, n in pairs),
            'is_production': bool(designation
                                  and designation.approved_layout_id == c.pk),
            'production_pk': production_pk, 'drafts': drafts,
            'placements_json': _json.dumps(c.placements['placements']),
            'width_mm': c.run.usable_width_mm,
            'height_mm': int(height),
        })

    def post(self, request, pk):
        import json as _json
        from patterns_ai.services import marker_generation_service as gen
        c = self._candidate(pk)

        if request.POST.get('action') == 'optimize':
            # Phase 5 M2 — STATELESS compute endpoint: the payload carries
            # everything; the server remembers nothing; nothing persists.
            from django.http import JsonResponse
            from patterns_ai.services.compute_bridge import ComputeError
            try:
                payload = gen.optimize_layout(
                    user=request.user,
                    width_mm=request.POST.get('width_mm', ''),
                    height_mm=request.POST.get('height_mm', ''),
                    spacing_mm=request.POST.get('spacing_mm', '3'),
                    placements=_json.loads(
                        request.POST.get('placements', '')),
                    selected=_json.loads(
                        request.POST.get('selected', '[]')),
                    options_wanted=request.POST.get('options_wanted', '3'),
                    effort=request.POST.get('effort', 'balanced'),
                    seed=request.POST.get('seed', '42'))
            except _json.JSONDecodeError:
                return JsonResponse({'ok': False,
                                     'error': 'bad layout payload'})
            except (ValidationError, PermissionDenied) as exc:
                msg = '; '.join(getattr(exc, 'messages', None) or [str(exc)])
                return JsonResponse({'ok': False, 'error': msg})
            except ComputeError as exc:             # honest ops-level failure
                return JsonResponse({'ok': False, 'error': str(exc)})
            return JsonResponse(payload)

        try:
            placements = _json.loads(request.POST.get('placements', ''))
            run, saved = gen.save_manual_layout(
                user=request.user, source_candidate=c,
                width_mm=request.POST.get('width_mm', ''),
                height_mm=request.POST.get('height_mm', ''),
                placements=placements)
        except _json.JSONDecodeError:
            messages.error(request, 'bad layout payload')
            return redirect('patterns_ai:workspace', pk=pk)
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
            return redirect('patterns_ai:workspace', pk=pk)
        except ValueError:
            messages.error(request, 'width/height must be numbers')
            return redirect('patterns_ai:workspace', pk=pk)
        messages.success(
            request,
            f'Layout saved ({saved.marker_length_mm} mm, verified) — '
            "you're now editing the saved version.")
        return redirect('patterns_ai:workspace', pk=saved.pk)


def _export_summary(c, user):
    """§3f: the Production Layout Summary stamped into every export
    artifact — facts + derived-at-read, never stored."""
    from django.utils import timezone
    from patterns_ai.models import ProductionLayout
    from patterns_ai.services import marker_generation_service as gen
    m = gen.derive_candidate_metrics(c)
    d = (ProductionLayout.objects.filter(product=c.run.product)
         .select_related('approved_by').first())
    prod = bool(d and d.approved_layout_id == c.pk)
    return {
        'product_code': c.run.product.code,
        'product_name': c.run.product.name,
        'layout_id': c.pk,
        'width_mm': c.run.usable_width_mm,
        'length_mm': str(m['length_mm']),
        'utilization_pct': str(m['utilization_pct']),
        'waste_pct': str(m['waste_pct']),
        'piece_count': m['piece_count'], 'garments': m['garments'],
        'ratio': ' · '.join(_ratio_labels(c.run)),
        'verified': m['verified'], 'production': prod,
        'approved_by': str(d.approved_by) if prod else '',
        'approved_at': (timezone.localtime(d.approved_at)
                        .strftime('%Y-%m-%d %H:%M') if prod else ''),
        'generated_at': timezone.localtime().strftime('%Y-%m-%d %H:%M'),
        'generated_by': str(user),
    }


class CandidatePdfView(LoginRequiredMixin, _ManagementOnly, View):
    """M8 — the PRODUCTION DOCUMENT: pure-python PDF from the compute
    runtime (page 1 = summary, then numbered true-scale tiles).
    Verified layouts only — an unverified layout must never reach a
    cutting table."""

    def get(self, request, pk):
        from django.http import HttpResponse
        import base64
        from patterns_ai.models import GeneratedMarkerCandidate
        from patterns_ai.services import compute_bridge
        from patterns_ai.services.compute_bridge import ComputeError
        c = get_object_or_404(
            GeneratedMarkerCandidate.objects.select_related('run__product'),
            pk=pk)
        if not (c.verification or {}).get('ok'):
            messages.error(request, 'unverified layouts cannot be '
                                    'exported for production.')
            return redirect('patterns_ai:candidate-detail', pk=pk)
        summary = _export_summary(c, request.user)
        # PDF text = WinAnsi; keep the ratio separator plain
        summary['ratio'] = summary['ratio'].replace(' · ', '  ')
        try:
            result = compute_bridge.run_tool('pdf', {
                'width_mm': float(c.run.usable_width_mm),
                'length_mm': float(c.marker_length_mm),
                'summary': summary,
                'placements': c.placements['placements']})
        except ComputeError as exc:
            messages.error(request, f'PDF build failed: {exc}')
            return redirect('patterns_ai:candidate-detail', pk=pk)
        if not result.get('ok'):
            messages.error(request, result.get('error', 'PDF build failed'))
            return redirect('patterns_ai:candidate-detail', pk=pk)
        resp = HttpResponse(base64.b64decode(result['pdf_b64']),
                            content_type='application/pdf')
        resp['Content-Disposition'] = (
            f'attachment; filename="layout_{c.pk}_production.pdf"')
        return resp


class CandidatePrintView(LoginRequiredMixin, _ManagementOnly, View):
    """M8 — full-marker tiled TRUE-SCALE print page (browser print;
    same tile grid + numbering as the PDF; Gate-1-style scale bar)."""
    template_name = 'patterns_ai/candidate_print.html'

    STEP_W, STEP_H = 180.0, 267.0        # window − 10 mm overlap
    WIN_W, WIN_H = 190.0, 277.0

    def get(self, request, pk):
        import math
        from patterns_ai.models import GeneratedMarkerCandidate
        from patterns_ai.services.svg_render import marker_tile_svg
        c = get_object_or_404(
            GeneratedMarkerCandidate.objects.select_related('run__product'),
            pk=pk)
        if not (c.verification or {}).get('ok'):
            messages.error(request, 'unverified layouts cannot be '
                                    'printed for production.')
            return redirect('patterns_ai:candidate-detail', pk=pk)
        W = float(c.run.usable_width_mm)
        L = float(c.marker_length_mm)
        cols = max(1, math.ceil(W / self.STEP_W))
        rows = max(1, math.ceil(L / self.STEP_H))
        placements = c.placements['placements']
        tiles = []
        for row in range(rows):
            for col in range(cols):
                tiles.append({
                    'label': f'C{col + 1}-R{row + 1}',
                    'col': col + 1, 'row': row + 1,
                    'svg': marker_tile_svg(
                        placements, W, L,
                        col * self.STEP_W, row * self.STEP_H,
                        self.WIN_W, self.WIN_H)})
        return render(request, self.template_name, {
            'c': c, 'run': c.run, 'product': c.run.product,
            'summary': _export_summary(c, request.user),
            'tiles': tiles, 'cols': cols, 'rows': rows})


class ApproveProductionView(LoginRequiredMixin, _ManagementOnly, View):
    """🔒 M7 (§3g + owner refinement 5): Approve = its own explicit,
    audited act — NEVER bundled with Save. GET = the review step (the
    Production Layout Summary is read BEFORE approving); POST = the
    frozen single-writer moves the pointer. Nothing else happens."""
    template_name = 'patterns_ai/approve_confirm.html'

    def _candidate(self, pk):
        from patterns_ai.models import GeneratedMarkerCandidate
        return get_object_or_404(
            GeneratedMarkerCandidate.objects.select_related('run__product'),
            pk=pk)

    def get(self, request, pk):
        from patterns_ai.models import ProductionLayout
        from patterns_ai.services import marker_generation_service as gen
        c = self._candidate(pk)
        designation = (ProductionLayout.objects
                       .filter(product=c.run.product)
                       .select_related('approved_by').first())
        return render(request, self.template_name, {
            'c': c, 'run': c.run, 'product': c.run.product,
            'metrics': gen.derive_candidate_metrics(c),
            'ratio_labels': _ratio_labels(c.run),
            'designation': designation,
            'already': bool(designation
                            and designation.approved_layout_id == c.pk)})

    def post(self, request, pk):
        from patterns_ai.models import ProductionLayout
        from patterns_ai.services import production_layout_service as pls
        c = self._candidate(pk)
        designation = ProductionLayout.objects.filter(
            product=c.run.product).first()
        already = bool(designation
                       and designation.approved_layout_id == c.pk)
        try:
            pls.approve_production_layout(user=request.user,
                                          product=c.run.product, layout=c)
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
            return redirect('patterns_ai:candidate-detail', pk=pk)
        if already:
            messages.info(request,
                          f'Layout #{c.pk} is already the production '
                          'layout — nothing changed.')
        else:
            messages.success(request,
                             f'Layout #{c.pk} is now the production '
                             'layout ★ — the previous one stays in the '
                             'Layout switcher history.')
        return redirect('patterns_ai:candidate-detail', pk=pk)


class ToolRedirectView(LoginRequiredMixin, _ManagementOnly, View):
    """THE entry point — a smart redirect, not a page. M4 §18-d
    retirement (owner-confirmed): the ★ ProductionLayout designation and
    the generator-era workspace/generate chain leave NAVIGATION (their
    data + pages stay live at their URLs). New deterministic priority =
    platform stations only: ready size → the Digital Cutting Table (its
    Layout Library included) · pieces → the Studio · nothing →
    Blueprint. Rule C: product pinned by the URL; Rule E: every decision
    logged."""

    def get(self, request, product_pk):
        from django.urls import reverse
        from patterns_ai.models import PatternPiece
        from patterns_ai.services import pattern_design_facade as facade
        product = get_object_or_404(Product, pk=product_pk, is_active=True)
        library = facade.product_design_library(product)
        if library['summary']['any_size_ready']:
            reason = 'cutting table'
            url = reverse('patterns_ai:cutting-table', args=[product.pk])
        elif PatternPiece.objects.filter(product=product).exists():
            reason = 'studio'
            url = reverse('patterns_ai:studio') + f'?product={product.pk}'
        else:
            reason = 'blueprint'
            url = (reverse('patterns_ai:blueprint')
                   + f'?product={product.pk}')
        logger.info(
            'patterns.tool.redirect product=%s dest=%s reason="%s" user=%s',
            product.pk, url, reason, request.user.pk)
        return redirect(url)


# ════════════════════════════════════════════════════════════════════════════
# M2 — the PATTERN INTELLIGENCE STUDIO (UI_WORKFLOW_FREEZE §2.3/§2.4/§2.5).
# One room, two modes: BROWSE (the Pattern Library shelf) · WORK (one
# piece × size: Evidence Stack → proposals → review → refine → publish).
# parse → gate → delegate: every write goes through the single writers
# (acquisition_service for evidence, pattern_geometry_service for truth).
# ════════════════════════════════════════════════════════════════════════════

# compare-overlay palette (workspace skin: proposal identity colors —
# distinct from the frozen semantic color law + reserved size palette)
_PROPOSAL_COLORS = ['#2563eb', '#d97706', '#059669', '#7c3aed']


def _payload_stats(payload):
    """Display stats for one canonical payload: mm outline + w/h/area/
    vertex count (view-local; display only)."""
    outer = payload['outer']
    outline_mm = [[x / 1000.0, y / 1000.0] for x, y in outer]
    w = max(p[0] for p in outline_mm)
    h = max(p[1] for p in outline_mm)
    s = 0.0
    for i in range(len(outline_mm)):
        x1, y1 = outline_mm[i]
        x2, y2 = outline_mm[(i + 1) % len(outline_mm)]
        s += x1 * y2 - x2 * y1
    return {'outline_mm': outline_mm, 'w_mm': round(w, 1),
            'h_mm': round(h, 1),
            'area_cm2': round(abs(s) / 2.0 / 100.0, 1),
            'vertices': len(outer),
            'notches': len((payload.get('features') or {})
                           .get('notches') or [])}


def _overlay_svg(stats_list, colors):
    """Compare mode (UI freeze §4): 2+ proposal outlines in ONE viewBox,
    color-coded, semi-transparent fills so deviations read instantly."""
    if not stats_list:
        return ''
    w = max(s['w_mm'] for s in stats_list)
    h = max(s['h_mm'] for s in stats_list)
    pad = max(w, h) * 0.04 + 2
    parts = [f'<svg class="cmp-svg" viewBox="{-pad} {-pad} '
             f'{w + 2 * pad} {h + 2 * pad}" '
             'xmlns="http://www.w3.org/2000/svg">']
    for i, st in enumerate(stats_list):
        color = colors[i % len(colors)]
        pts = ' '.join(f'{x:.2f},{(h - y):.2f}'
                       for x, y in st['outline_mm'])
        parts.append(f'<polygon points="{pts}" fill="{color}" '
                     f'fill-opacity="0.12" stroke="{color}" '
                     'stroke-width="1.2" '
                     'vector-effect="non-scaling-stroke"/>')
    parts.append('</svg>')
    return ''.join(parts)


def _confidence_display(extraction):
    """UI freeze §4 confidence panel — DISPLAY ONLY, never a gate."""
    base = {'manual_dims': ('Manual dimensions', 100),
            'dxf': ('DXF', 99), 'svg': ('SVG', 95)}
    if extraction.capture_id is not None:
        conf = extraction.confidence or {}
        overall = conf.get('overall')
        return {'label': 'Photo (mat-calibrated)',
                'overall': overall, 'detail': conf}
    label, default = base.get(extraction.backend,
                              (extraction.backend, None))
    overall = (extraction.confidence or {}).get('overall', default)
    return {'label': label, 'overall': overall, 'detail': {}}


class StudioView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """BROWSE mode — the Pattern Library shelf (UI freeze §2.3): size
    tabs (hierarchy law: Product → Size → Piece), the creation checklist
    (the SAME readiness truth that gates the DCT, surfaced where work
    happens), shelf rows, the conveyor entry. GET-only."""
    template_name = 'patterns_ai/studio.html'

    def get_context_data(self, **kwargs):
        from django.urls import reverse
        from patterns_ai.models import PatternPiece
        from patterns_ai.services import (acquisition_service,
                                          pattern_design_facade as facade)
        from patterns_ai.services.svg_render import outline_preview_svg
        ctx = super().get_context_data(**kwargs)
        pid = self.request.GET.get('product')
        if not pid:
            ctx.update({'product': None,
                        'all_products': Product.objects.filter(
                            is_active=True).order_by('code')})
            return ctx
        product = get_object_or_404(Product, pk=_int_or_404(pid),
                                    is_active=True)
        library = facade.product_design_library(product)
        sections = library['sections']
        size_code = self.request.GET.get('size')
        active = next((s for s in sections
                       if s['size'].code == size_code),
                      sections[0] if sections else None)
        if active:
            pieces = {p.pk: p for p in
                      PatternPiece.objects.filter(product=product)
                      .prefetch_related('versions')}
            for row in active['rows']:
                row['preview_svg'] = outline_preview_svg(row['outline_mm'])
                row['work_url'] = reverse(
                    'patterns_ai:studio-work',
                    args=[row['piece_id'], row['size_id']])
                piece = pieces[row['piece_id']]
                if row['status'] == 'confirmed' and row['version_id']:
                    row['history_url'] = reverse(
                        'patterns_ai:version-detail',
                        args=[row['version_id']])
                elif row['status'] == 'draft':
                    draft = piece.versions.filter(status='draft').first()
                    row['history_url'] = reverse(
                        'patterns_ai:version-detail', args=[draft.pk])
                else:
                    row['history_url'] = reverse(
                        'patterns_ai:piece-detail', args=[row['piece_id']])
                row['dxf_url'] = (reverse('patterns_ai:geometry-dxf',
                                          args=[row['geometry_row_id']])
                                  if row['geometry_row_id'] else None)
                row['svg_url'] = (reverse('patterns_ai:geometry-svg',
                                          args=[row['geometry_row_id']])
                                  if row['geometry_row_id'] else None)
            # checklist chips: mandatory ✓/✖ first, then optional ○/✓
            chips = ([{'name': r['piece_name'],
                       'done': r['status'] == 'confirmed',
                       'optional': False}
                      for r in active['rows']
                      if not r['badges']['optional']]
                     + [{'name': r['piece_name'],
                         'done': r['status'] == 'confirmed',
                         'optional': True}
                        for r in active['rows']
                        if r['badges']['optional']])
            # todo-first shelf buckets (W2R2 order, kept from the Manager)
            buckets = [
                {'icon': '✖', 'label': 'Missing',
                 'rows': [r for r in active['rows']
                          if r['status'] == 'missing']},
                {'icon': '⚠', 'label': 'Needs work',
                 'rows': [r for r in active['rows']
                          if r['status'] == 'draft']},
                {'icon': '✓', 'label': 'Complete',
                 'rows': [r for r in active['rows']
                          if r['status'] == 'confirmed']},
            ]
        else:
            chips, buckets = [], []
        nxt = acquisition_service.next_missing_design(product)
        ctx.update({
            'product': product, 'summary': library['summary'],
            'sections': sections, 'active': active, 'chips': chips,
            'buckets': buckets,
            'conveyor': nxt,
            'conveyor_url': (reverse('patterns_ai:studio-work',
                                     args=[nxt['piece_id'], nxt['size_id']])
                             if nxt else None),
        })
        return ctx


class StudioWorkView(LoginRequiredMixin, _ManagementOnly, View):
    """WORK mode — one piece × size (UI freeze §2.4): Evidence Stack
    (left) · proposal canvas + compare (center) · inspector (right).
    POST = parse → gate → delegate to the single writers only."""
    template_name = 'patterns_ai/studio_work.html'

    def _load(self, piece_pk, size_pk):
        from production.models import ProductSize
        from patterns_ai.models import PatternPiece
        piece = get_object_or_404(
            PatternPiece.objects.select_related('product', 'pattern',
                                                'reference_image'),
            pk=piece_pk)
        size = get_object_or_404(ProductSize, pk=size_pk,
                                 product=piece.product)
        return piece, size

    def _ctx(self, request, piece, size):
        from django.urls import reverse
        from patterns_ai.models import PatternPieceVersion
        from patterns_ai.services import acquisition_service
        from patterns_ai.services.svg_render import geometry_svg

        stack = []
        proposals_by_id = {}
        for ev in acquisition_service.stack_for(piece, size):
            proposal = None
            for p in ev.proposals.all():          # prefetched, newest wins
                if proposal is None or p.pk > proposal.pk:
                    proposal = p
            entry = {'ev': ev, 'proposal': proposal}
            if ev.kind == 'photo_plain':
                # M8 set membership: view label + tape-number chips
                p = ev.params or {}
                entry['view'] = p.get('view') or 'other'
                entry['measurements'] = [
                    {'name': n.removesuffix('_mm').replace('_', ' '),
                     'mm': v}
                    for n, v in (p.get('measurements') or {}).items()]
            if proposal is not None:
                proposals_by_id[proposal.pk] = proposal
                entry['confidence'] = _confidence_display(proposal)
                if proposal.geometry:
                    entry['stats'] = _payload_stats(proposal.geometry)
            stack.append(entry)
        plain_photos = [e for e in stack
                        if e['ev'].kind == 'photo_plain']

        # selected proposal (canvas): ?proposal= or newest reviewable
        sel_id = self.request_int(request, 'proposal')
        selected = proposals_by_id.get(sel_id)
        if selected is None:
            selected = next(
                (e['proposal'] for e in stack
                 if e['proposal'] is not None
                 and e['proposal'].geometry
                 and e['proposal'].status == 'proposed'), None)
        canvas_svg = (geometry_svg(selected.geometry)
                      if selected is not None and selected.geometry
                      else None)

        # compare mode: ?compare=id,id (this stack's proposals only)
        compare_rows, compare_svg = [], None
        raw_cmp = (request.GET.get('compare') or '').strip()
        if raw_cmp:
            ids = [int(x) for x in raw_cmp.split(',')
                   if x.strip().isdigit()]
            chosen = [proposals_by_id[i] for i in ids
                      if i in proposals_by_id
                      and proposals_by_id[i].geometry]
            stats = [_payload_stats(p.geometry) for p in chosen]
            for i, (p, st) in enumerate(zip(chosen, stats)):
                compare_rows.append(
                    {'p': p, 'stats': st,
                     'color': _PROPOSAL_COLORS[i % len(_PROPOSAL_COLORS)],
                     'confidence': _confidence_display(p)})
            if len(stats) >= 2:
                compare_svg = _overlay_svg(stats, _PROPOSAL_COLORS)

        # current design state (draft/confirmed) for the inspector
        Status = PatternPieceVersion.Status
        draft = piece.versions.filter(status=Status.DRAFT).first()
        confirmed = (piece.versions.filter(status=Status.CONFIRMED)
                     .order_by('-version_no').first())
        draft_rows = []
        if draft:
            for row in (draft.size_geometries.select_related('size')
                        .order_by('size__display_order')):
                grain = ((row.geometry.get('features') or {})
                         .get('grain') or {})
                draft_rows.append(
                    {'row': row,
                     'grain_deg': (grain.get('angle_cdeg', 0) or 0) / 100.0,
                     'is_this': row.size_id == size.pk,
                     'stats': _payload_stats(row.geometry)})
        this_draft_row = next((d for d in draft_rows if d['is_this']), None)
        confirmed_row = (confirmed.size_geometries.filter(size=size)
                         .select_related('size').first()
                         if confirmed else None)

        # phone hand-off (UI freeze §2.5): QR + short link to the capture
        # page with this size preselected
        capture_url = request.build_absolute_uri(
            reverse('patterns_ai:pattern-capture', args=[piece.pk])
            + f'?size={size.pk}')
        try:
            import qrcode
            import qrcode.image.svg
            qr_svg = qrcode.make(
                capture_url,
                image_factory=qrcode.image.svg.SvgPathImage,
                box_size=9).to_string().decode()
        except Exception:                          # lib absent: link only
            qr_svg = None

        actual_notches = None
        active_row = this_draft_row['row'] if this_draft_row else confirmed_row
        if active_row is not None:
            actual_notches = len((active_row.geometry.get('features') or {})
                                 .get('notches') or [])

        # ── M4.5 R2-C: one-shot capability proposals (DETERMINISTIC —
        # rule ⑩; the expert owns the answer; drafts only — confirmed
        # geometry is immutable) ──
        from patterns_ai.services import fold_service
        fold_proposal = None
        symmetry_proposal = None
        has_fold_edge = (active_row is not None
                         and fold_service.get_fold_edge(
                             active_row.geometry) is not None)
        if this_draft_row is not None and not has_fold_edge:
            if piece.on_fold:
                fold_proposal = fold_service.detect_fold_edge(
                    this_draft_row['row'].geometry)
            else:
                # honest v1 boundary: a straight vertical edge exists —
                # only the EXPERT knows whether this is a half-pattern
                # (a pocket has vertical edges too). One-shot judgment.
                symmetry_proposal = fold_service.detect_fold_edge(
                    this_draft_row['row'].geometry)

        return {
            'piece': piece, 'size': size, 'product': piece.product,
            'stack': stack, 'selected': selected, 'canvas_svg': canvas_svg,
            'compare_rows': compare_rows, 'compare_svg': compare_svg,
            'draft': draft, 'draft_rows': draft_rows,
            'this_draft_row': this_draft_row,
            'confirmed': confirmed, 'confirmed_row': confirmed_row,
            'capture_url': capture_url, 'qr_svg': qr_svg,
            'actual_notches': actual_notches,
            'has_fold_edge': has_fold_edge,
            'fold_proposal': fold_proposal,
            'symmetry_proposal': symmetry_proposal,
            'evidence_count': len(stack),
            'sel_confidence': (_confidence_display(selected)
                               if selected is not None else None),
            'available_note': None,
            # M8 Evidence-Set adapter surfaces
            'plain_photos': plain_photos,
            'sel_cross_checks': (
                [{'name': n.removesuffix('_mm').replace('_', ' '), **c}
                 for n, c in ((selected.result.get('set') or {})
                              .get('cross_checks') or {}).items()]
                if selected is not None else []),
        }

    @staticmethod
    def request_int(request, name):
        raw = request.GET.get(name, '')
        return int(raw) if raw.isdigit() else None

    def get(self, request, piece_pk, size_pk):
        piece, size = self._load(piece_pk, size_pk)
        return render(request, self.template_name,
                      self._ctx(request, piece, size))

    def post(self, request, piece_pk, size_pk):
        from django.urls import reverse
        from patterns_ai.models import GeometryExtraction
        from patterns_ai.services import (acquisition_service,
                                          capture_service,
                                          pattern_geometry_service as geo)
        piece, size = self._load(piece_pk, size_pk)
        action = request.POST.get('action', '')
        back = redirect(reverse('patterns_ai:studio-work',
                                args=[piece.pk, size.pk]))

        def _proposal():
            p = get_object_or_404(
                GeometryExtraction,
                pk=_int_or_404(request.POST.get('proposal')))
            if p.piece_id != piece.pk or p.size_id != size.pk:  # tamper wall
                from django.http import Http404
                raise Http404
            return p

        try:
            if action == 'add_dxf' or action == 'add_svg':
                upload = request.FILES.get('evidence_file')
                _, proposal = acquisition_service.add_evidence(
                    user=request.user, piece=piece, size=size,
                    kind=action.removeprefix('add_'),
                    uploaded_file=upload)
                if proposal.gate.get('passed'):
                    messages.success(request,
                                     'Evidence added — proposal ready to '
                                     'review.')
                else:
                    messages.error(request,
                                   'Adapter refused (recorded): '
                                   + '; '.join(proposal.gate.get('reasons')
                                               or []))
            elif action == 'add_plain_photo':
                # M8: plain photo JOINS the set (no per-item adapter) —
                # measurement rows arrive as parallel name/mm arrays
                names = request.POST.getlist('m_name')
                values = request.POST.getlist('m_mm')
                measurements = {n: v for n, v in zip(names, values)
                                if n.strip() and v.strip()}
                acquisition_service.add_evidence(
                    user=request.user, piece=piece, size=size,
                    kind='photo_plain',
                    uploaded_file=request.FILES.get('evidence_file'),
                    params={'view': request.POST.get('view', 'other'),
                            'measurements': measurements})
                messages.success(
                    request,
                    'Photo joined the evidence set — add more angles / '
                    'measurements, then Build geometry from evidence.')
            elif action == 'build_from_evidence':
                from patterns_ai.models import EvidenceItem
                primary = get_object_or_404(
                    EvidenceItem,
                    pk=_int_or_404(request.POST.get('primary')))
                proposal = acquisition_service.build_from_evidence(
                    user=request.user, piece=piece, size=size,
                    primary=primary)
                if proposal.gate.get('passed'):
                    messages.success(
                        request,
                        'Geometry proposed from the evidence set — '
                        'review it against the photos and cross-checks.')
                else:
                    messages.error(request,
                                   'Set adapter refused (recorded): '
                                   + '; '.join(proposal.gate.get('reasons')
                                               or []))
            elif action == 'add_dims':
                _, proposal = acquisition_service.add_evidence(
                    user=request.user, piece=piece, size=size,
                    kind='manual_dims',
                    params={'width_mm': request.POST.get('width_mm'),
                            'height_mm': request.POST.get('height_mm')})
                if proposal.gate.get('passed'):
                    messages.success(request,
                                     'Rectangle constructed from your '
                                     'numbers — accept, then refine its '
                                     'outline in the editor.')
                else:
                    messages.error(request,
                                   'Adapter refused (recorded): '
                                   + '; '.join(proposal.gate.get('reasons')
                                               or []))
            elif action == 'use_proposal':
                row = geo.accept_extraction(user=request.user,
                                            extraction=_proposal())
                messages.success(
                    request,
                    f'Accepted into draft v{row.version.version_no} — '
                    'refine the outline, then Verify & Publish.')
            elif action == 'reject_proposal':
                geo.reject_extraction(user=request.user,
                                      extraction=_proposal(),
                                      reason=request.POST.get('reason', ''))
                messages.success(request, 'Proposal rejected — recorded.')
            elif action == 'set_reference':
                upload = request.FILES.get('reference')
                if upload is None:
                    messages.error(request, 'choose an image first.')
                    return back
                from patterns_ai.models import CaptureAsset
                asset = capture_service.store_capture(
                    user=request.user, product=piece.product,
                    uploaded_file=upload, source='gallery',
                    kind=CaptureAsset.Kind.REFERENCE_IMAGE)
                geo.set_reference_image(user=request.user, piece=piece,
                                        asset=asset)
                messages.success(request, 'Reference image set.')
            elif action == 'start_next_version':
                draft = geo.start_next_version(user=request.user,
                                               piece=piece)
                messages.success(
                    request,
                    f'Draft v{draft.version_no} opened — carried '
                    f'{draft.size_geometries.count()} size(s) forward.')
            elif action in ('accept_fold_edge', 'mark_fold_capable'):
                # M4.5 R2-C: one-shot capability acceptance — the
                # deterministic proposal becomes permanent pattern
                # knowledge through the single writers.
                import json as _json
                from patterns_ai.models import PatternPieceVersion
                fe = _json.loads(request.POST.get('fold_edge') or 'null')
                draft = piece.versions.filter(
                    status=PatternPieceVersion.Status.DRAFT).first()
                row = (draft.size_geometries.filter(size=size).first()
                       if draft else None)
                if fe is None or row is None:
                    messages.error(request, 'no draft geometry to mark.')
                    return back
                if action == 'mark_fold_capable':
                    geo.set_piece_rules(user=request.user, piece=piece,
                                        on_fold=True)
                geo.edit_draft_geometry(
                    user=request.user, version=draft, size=size,
                    outer_um=row.geometry['outer'], fold_edge=fe)
                messages.success(
                    request,
                    'Fold capability recorded — permanent pattern '
                    'knowledge (asked once, owned forever).')
            elif action == 'publish':
                return self._publish(request, piece, size, back)
            else:
                messages.error(request, 'unknown action.')
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
        return back

    def _publish(self, request, piece, size, back):
        """Verify & Publish (UI freeze §2.4): the tape dialog confirms the
        WHOLE draft version (ADR-D law — versions are piece-level; the
        dialog lists every size honestly). On success the CONVEYOR
        advances to the next missing mandatory design."""
        from django.urls import reverse
        from patterns_ai.models import PatternPieceVersion
        from patterns_ai.services import (acquisition_service,
                                          pattern_geometry_service as geo)
        draft = piece.versions.filter(
            status=PatternPieceVersion.Status.DRAFT).first()
        if draft is None:
            messages.error(request, 'no draft to publish — accept a '
                                    'proposal first.')
            return back
        grain, tape = {}, {}
        for row in draft.size_geometries.select_related('size'):
            g = request.POST.get(f'grain_{row.size_id}', '').strip()
            if g:
                try:
                    grain[row.size_id] = int(round(float(g) * 100))
                except ValueError:
                    messages.error(request,
                                   f'grain for {row.size.code}: not a '
                                   'number')
                    return back
            w = request.POST.get(f'tape_w_{row.size_id}', '').strip()
            h = request.POST.get(f'tape_h_{row.size_id}', '').strip()
            if w and h:
                try:
                    tape[row.size_id] = {'width_mm': float(w),
                                         'height_mm': float(h)}
                except ValueError:
                    messages.error(request,
                                   f'tape for {row.size.code}: not numbers')
                    return back
        try:
            geo.confirm_version(user=request.user, version=draft,
                                grain_by_size=grain, tape_by_size=tape)
        except (ValidationError, PermissionDenied) as exc:
            for m in getattr(exc, 'messages', None) or [str(exc)]:
                messages.error(request, m)
            return back
        nxt = acquisition_service.next_missing_design(
            piece.product, after_key=f'{piece.pk}:{size.pk}')
        if nxt is not None:
            messages.success(
                request,
                f'v{draft.version_no} PUBLISHED ✓ — conveyor: next is '
                f"{nxt['piece_name']} · {nxt['size_code']}.")
            return redirect(reverse('patterns_ai:studio-work',
                                    args=[nxt['piece_id'],
                                          nxt['size_id']]))
        messages.success(
            request,
            f'v{draft.version_no} PUBLISHED ✓ — every mandatory design '
            'is confirmed. The size shelf is complete.')
        return redirect(reverse('patterns_ai:studio')
                        + f'?product={piece.product_id}&size={size.code}')


class StudioEvidenceCountView(LoginRequiredMixin, _ManagementOnly, View):
    """Tiny poll target for the phone hand-off panel (UI freeze §2.5):
    the desktop watches the stack grow while the phone uploads."""

    def get(self, request, piece_pk, size_pk):
        from django.http import JsonResponse
        from patterns_ai.models import EvidenceItem, PatternPiece
        piece = get_object_or_404(PatternPiece, pk=piece_pk)
        count = EvidenceItem.objects.filter(piece=piece,
                                            size_id=size_pk).count()
        return JsonResponse({'count': count})


class CuttingTableRecipeView(LoginRequiredMixin, _ManagementOnly, View):
    """M4 §4 — save the session's Marker Plan as a MARKER RECIPE (R1:
    the UI word; model = ManufacturingStrategy). parse → gate →
    strategy_service (single writer). Returns the refreshed recipe list
    so the dialog updates without a reload."""

    def post(self, request, pk):
        import json as _json
        from patterns_ai.services import strategy_service
        product = get_object_or_404(Product, pk=pk, is_active=True)
        try:
            body = _json.loads(request.body.decode() or '{}')
            # M5: recipe MANAGEMENT — deactivate (knowledge soft-state)
            if body.get('action') == 'deactivate':
                from patterns_ai.models import ManufacturingStrategy
                recipe = get_object_or_404(
                    ManufacturingStrategy,
                    pk=_int_or_404(body.get('recipe_id')),
                    product=product)
                strategy_service.deactivate_recipe(user=request.user,
                                                   recipe=recipe)
                recipes = [{'id': s.pk, 'name': s.name,
                            'fabric_group': s.fabric_group,
                            'layering_type': s.layering_type,
                            'piece_ids': s.piece_ids,
                            'size_ratio': s.size_ratio,
                            'notes': s.notes}
                           for s in strategy_service.active_recipes(
                               product)]
                return JsonResponse({'ok': True, 'recipes': recipes})
            recipe = strategy_service.save_recipe(
                user=request.user, product=product,
                name=body.get('name'),
                fabric_group=body.get('fabric_group'),
                layering_type=body.get('layering_type') or 'single',
                piece_ids=body.get('piece_ids') or [],
                size_ratio=body.get('size_ratio') or {},
                optimize_intent=body.get('optimize_intent') or 'balanced',
                notes=body.get('notes') or '')
        except ValidationError as exc:
            return JsonResponse(
                {'ok': False,
                 'error': '; '.join(getattr(exc, 'messages', None)
                                    or [str(exc)])}, status=400)
        except ValueError:
            return JsonResponse({'ok': False, 'error': 'bad JSON body.'},
                                status=400)
        recipes = [{'id': s.pk, 'name': s.name,
                    'fabric_group': s.fabric_group,
                    'layering_type': s.layering_type,
                    'piece_ids': s.piece_ids, 'size_ratio': s.size_ratio,
                    'notes': s.notes}
                   for s in strategy_service.active_recipes(product)]
        return JsonResponse({'ok': True, 'recipe_id': recipe.pk,
                             'recipes': recipes})
