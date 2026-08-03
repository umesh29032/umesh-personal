"""Roll-to-Adda assign view — Layering stage ka data entry surface.

YEH FILE KYU HAI?
─────────────────
Single roll ko ek in-progress Adda mein assign karta hai (weight + width yahin capture).
Adda choices dropdown sirf wo Addas list karta hai jo currently Layering stage pe hain
(in-progress + current_stage.stage_type='layering').

Service delegation:
  Sara DB write `assign_roll_to_adda` service ke through. View sirf form + redirect.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import FormView

from raw_materials.forms import AssignRollForm
from raw_materials.models import ClothRoll
from raw_materials.services import assign_roll_to_adda

from .mixins import ManagementRoleMixin


class RollAssignView(LoginRequiredMixin, ManagementRoleMixin, FormView):
    template_name = 'raw_materials/roll_assign_form.html'
    form_class = AssignRollForm

    def get_roll(self):
        return get_object_or_404(ClothRoll, pk=self.kwargs['pk'])

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        # Build the (code, "code – product") options from in-progress Addas at Layering stage.
        # Local import: avoid circular at module load.
        from production.constants import STAGE_LAYERING
        from production.models import Adda
        in_progress = Adda.objects.filter(
            status=Adda.Status.IN_PROGRESS,
            current_stage__stage__code=STAGE_LAYERING,
        ).select_related('product')
        kw['adda_choices'] = [
            ('', '— pick an Adda —'),
            *[(a.code, f"{a.code} · {a.product.name}") for a in in_progress],
        ]
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['roll'] = self.get_roll()
        return ctx

    def form_valid(self, form):
        # Resolve Adda by its `code` string from the dropdown.
        from production.models import Adda
        roll = self.get_roll()
        try:
            adda = Adda.objects.get(code=form.cleaned_data['adda_code'])
            assign_roll_to_adda(
                user=self.request.user,
                roll=roll,
                adda=adda,
                weight_kg=form.cleaned_data['weight_kg'],
                width_inch=form.cleaned_data['width_inch'],
            )
        except (Adda.DoesNotExist, ValidationError) as exc:
            form.add_error(None, str(exc) if str(exc) else "Invalid Adda")
            return self.form_invalid(form)
        messages.success(self.request, f"Roll {roll.roll_id} assigned to {adda.code}.")
        return redirect('production:adda-detail', code=adda.code)
