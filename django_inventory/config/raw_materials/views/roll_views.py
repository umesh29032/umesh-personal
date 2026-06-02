"""ClothRoll views — list, bulk create, detail.

YEH FILE KYU HAI?
─────────────────
RollListView         — /raw-materials/rolls/ ka backend. Filters, time logs, paginated list.
RollBulkCreateView   — bulk intake form. Super Admin only. Service ko delegate karta hai.
RollDetailView       — single roll detail page. Financial fields role-gated.

Filters approach:
  GET querystring se filters → get_queryset() apply → active_filter_chips
  context var template ko bhejta hai (chip strip with remove URLs).
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, FormView, ListView, UpdateView

from inventory.services import ROLE_SUPER_ADMIN, user_can_view_financials, user_has_role
from raw_materials.forms import BulkRollForm, RollEditForm
from raw_materials.models import ClothColor, ClothRoll, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls, update_roll_details

from .mixins import ProductionRoleMixin, SuperAdminOnlyMixin


class RollListView(LoginRequiredMixin, ProductionRoleMixin, ListView):
    """List + filter cloth rolls. Filters via querystring; pagination via Django."""
    template_name = 'raw_materials/roll_list.html'
    model = ClothRoll
    context_object_name = 'rolls'
    paginate_by = 50

    def get_queryset(self):
        qs = ClothRoll.objects.select_related('cloth_type', 'cloth_color', 'storage_location').order_by('-created_at')
        status = self.request.GET.get('status')
        type_id = self.request.GET.get('cloth_type')
        loc_id = self.request.GET.get('location')
        color_id = self.request.GET.get('color')
        if status in {ClothRoll.Status.NOT_USED, ClothRoll.Status.USED}:
            qs = qs.filter(status=status)
        if type_id:
            qs = qs.filter(cloth_type_id=type_id)
        if loc_id:
            qs = qs.filter(storage_location_id=loc_id)
        if color_id:
            qs = qs.filter(cloth_color_id=color_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cloth_types'] = ClothType.active.all()
        ctx['locations'] = StorageLocation.active.all()
        ctx['colors'] = ClothColor.active.order_by('name')
        ctx['can_view_financials'] = user_can_view_financials(self.request.user)
        ctx['can_add_rolls'] = user_has_role(self.request.user, [ROLE_SUPER_ADMIN])

        status = self.request.GET.get('status', '')
        type_id = self.request.GET.get('cloth_type', '')
        loc_id = self.request.GET.get('location', '')
        color_id = self.request.GET.get('color', '')
        ctx['filters'] = {
            'status': status, 'cloth_type': type_id,
            'location': loc_id, 'color': color_id,
        }

        # Build active-filter chip list with human-readable labels + a "remove
        # this one filter" URL that keeps the other filters intact. Used by the
        # summary strip rendered under the filter card.
        chips = []
        if status:
            label = dict(ClothRoll.Status.choices).get(status, status)
            chips.append({
                'group': 'Status', 'label': label,
                'remove_url': self._build_remove_url('status'),
            })
        if type_id:
            try:
                ct = ClothType.objects.get(pk=type_id)
                chips.append({
                    'group': 'Type', 'label': ct.name,
                    'remove_url': self._build_remove_url('cloth_type'),
                })
            except (ClothType.DoesNotExist, ValueError):
                pass
        if loc_id:
            try:
                loc = StorageLocation.objects.get(pk=loc_id)
                chips.append({
                    'group': 'Location', 'label': loc.name,
                    'remove_url': self._build_remove_url('location'),
                })
            except (StorageLocation.DoesNotExist, ValueError):
                pass
        if color_id:
            try:
                col = ClothColor.objects.get(pk=color_id)
                chips.append({
                    'group': 'Color', 'label': col.name,
                    'remove_url': self._build_remove_url('color'),
                })
            except (ClothColor.DoesNotExist, ValueError):
                pass
        ctx['active_filter_chips'] = chips
        ctx['filtered_count'] = self.get_queryset().count() if chips else 0

        # Time log: latest cloth-roll movement events across all rolls.
        # Lazy-import — tracking depends on raw_materials, not the other way.
        from tracking.models import ClothRollHistory
        ctx['roll_events'] = (
            ClothRollHistory.objects
            .select_related('roll', 'roll__cloth_type', 'roll__cloth_color', 'actor')
            .order_by('-created_at')[:50]
        )
        return ctx

    def _build_remove_url(self, key_to_remove):
        """Return path with one filter key stripped — used by chip ✕ button."""
        params = self.request.GET.copy()
        if key_to_remove in params:
            del params[key_to_remove]
        if 'page' in params:
            del params['page']  # any filter change resets pagination
        qs = params.urlencode()
        return self.request.path + (('?' + qs) if qs else '')


class RollBulkCreateView(LoginRequiredMixin, SuperAdminOnlyMixin, FormView):
    """Bulk intake form. POST creates N rolls in one transaction.

    Super Admin only — cloth intake is a sensitive, irreversible event.
    """
    template_name = 'raw_materials/roll_bulk_form.html'
    form_class = BulkRollForm
    success_url = reverse_lazy('raw_materials:roll-list')

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['user'] = self.request.user
        # Pull repeating breakup rows out of POST data.
        if self.request.method == 'POST':
            colors = self.request.POST.getlist('breakup_color')
            qtys = self.request.POST.getlist('breakup_qty')
            kw['raw_breakup'] = [
                {'color': c, 'qty': q} for c, q in zip(colors, qtys) if c and q
            ]
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_colors'] = ClothColor.active.order_by('name')
        # On re-render after invalid POST, repopulate breakup rows so the user
        # doesn't have to re-type their breakdown.
        submitted = []
        if self.request.method == 'POST':
            colors = self.request.POST.getlist('breakup_color')
            qtys = self.request.POST.getlist('breakup_qty')
            submitted = [
                {'color_pk': c, 'qty': q}
                for c, q in zip(colors, qtys) if c or q
            ]
        ctx['submitted_breakup'] = submitted
        return ctx

    def form_valid(self, form):
        try:
            rolls = bulk_create_rolls(
                user=self.request.user,
                cloth_type=form.cleaned_data['cloth_type'],
                storage_location=form.cleaned_data['storage_location'],
                purchased_date=form.cleaned_data['purchased_date'],
                breakup=form.cleaned_data['breakup'],
                supplier=form.cleaned_data.get('supplier', ''),
                cost_per_kg=form.cleaned_data.get('cost_per_kg'),
            )
        except (ValidationError, PermissionError) as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, f"{len(rolls)} cloth rolls created.")
        return super().form_valid(form)


class RollDetailView(LoginRequiredMixin, ProductionRoleMixin, DetailView):
    template_name = 'raw_materials/roll_detail.html'
    model = ClothRoll
    context_object_name = 'roll'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['can_view_financials'] = user_can_view_financials(self.request.user)
        # Edit allowed only when stock is NOT_USED — once attached to Adda,
        # verified width/weight live on LayeringRollEntry (history immutable).
        ctx['can_edit'] = ctx['roll'].status == ClothRoll.Status.NOT_USED
        return ctx


class RollUpdateView(LoginRequiredMixin, ProductionRoleMixin, UpdateView):
    """Stock-level edit form for a single roll.

    Why ek alag view (not generic UpdateView.save())?
        Service layer (update_roll_details) field-level diff + history log karta.
        Direct .save() history bypass karta. View calls service.

    Gate: NOT_USED rolls only. Service raises ValidationError otherwise — view
    surfaces it as form error.
    """

    template_name = 'raw_materials/roll_edit_form.html'
    model = ClothRoll
    form_class = RollEditForm
    context_object_name = 'roll'

    def get_object(self, queryset=None):
        roll = get_object_or_404(ClothRoll, pk=self.kwargs['pk'])
        if roll.status != ClothRoll.Status.NOT_USED:
            # Hard gate — service would block anyway, but redirect early for UX
            messages.error(
                self.request,
                f"Roll {roll.roll_id} is in use. Detach from its Adda before editing.",
            )
        return roll

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['user'] = self.request.user
        return kw

    def form_valid(self, form):
        try:
            update_roll_details(
                user=self.request.user,
                roll=self.object,
                width_inch=form.cleaned_data.get('width_inch'),
                weight_kg=form.cleaned_data.get('weight_kg'),
                storage_location=form.cleaned_data.get('storage_location'),
                purchased_date=form.cleaned_data.get('purchased_date'),
                supplier=form.cleaned_data.get('supplier'),
                cost_per_kg=form.cleaned_data.get('cost_per_kg'),
            )
        except (PermissionDenied, ValidationError) as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, f"Roll {self.object.roll_id} updated.")
        return redirect('raw_materials:roll-detail', pk=self.object.pk)
