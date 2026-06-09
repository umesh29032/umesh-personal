"""Stage CRUD — admin manages the global Stage library.

YEH FILE KYU HAI?
─────────────────
Pehle StageAccessRule per-stage_type table tha. Ab Stage hi pehla-class model
hai (production.models.Stage). Access controls (skills + roles) Stage row pe
hi rehte hain. Yeh views Super Admin ko Stage library CRUD karne dete hain.

Page-level access: Super Admin only (CLAUDE.md rule #6, permission_service).
"""
from __future__ import annotations

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.models import Skill
from inventory.models import Role
from accounts.services import ROLE_SUPER_ADMIN, user_has_perm
from production.models import Stage, WorkflowStage


class _StagePermissionRequired(UserPassesTestMixin):
    """Stage CRUD gate driven by Django perms (production.view/add/change/delete_stage).

    Super Admin role bypasses every perm check (see user_has_perm). Other roles
    must be granted the specific perm via the Roles & Permissions editor —
    that's the RBAC seam an admin uses to delegate Stage editing without
    handing over full super-admin rights.
    """

    required_perm = ''  # subclasses set this

    def test_func(self):
        return user_has_perm(self.request.user, self.required_perm)


class StageForm(forms.ModelForm):
    """Stage create/edit form — code + name + description + access chips."""

    access_by_skill = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Allowed Skills',
        help_text='Users with ANY of these skills can access the stage.',
    )
    access_by_role = forms.ModelMultipleChoiceField(
        # Exclude super_admin — built-in access, not editable per CLAUDE.md.
        queryset=Role.objects.exclude(code=ROLE_SUPER_ADMIN).order_by('name'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Allowed Roles',
        help_text='Users whose role (or extra_roles) matches any of these.',
    )

    class Meta:
        model = Stage
        fields = ['code', 'name', 'description', 'is_active',
                  'access_by_skill', 'access_by_role']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class StageListView(LoginRequiredMixin, _StagePermissionRequired, ListView):
    required_perm = 'production.view_stage'
    model = Stage
    template_name = 'production/stage_list.html'
    context_object_name = 'stages'

    def get_queryset(self):
        return (
            Stage.objects
            .prefetch_related('access_by_skill', 'access_by_role', 'workflow_stages__product')
            .order_by('name')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        ctx['can_add_stage'] = user_has_perm(u, 'production.add_stage')
        ctx['can_change_stage'] = user_has_perm(u, 'production.change_stage')
        ctx['can_delete_stage'] = user_has_perm(u, 'production.delete_stage')
        return ctx


class StageCreateView(LoginRequiredMixin, _StagePermissionRequired, CreateView):
    required_perm = 'production.add_stage'
    model = Stage
    form_class = StageForm
    template_name = 'production/stage_form.html'
    success_url = reverse_lazy('production:stage-list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Create'
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Stage "{self.object.name}" created.')
        return response


class StageUpdateView(LoginRequiredMixin, _StagePermissionRequired, UpdateView):
    required_perm = 'production.change_stage'
    model = Stage
    form_class = StageForm
    template_name = 'production/stage_form.html'
    success_url = reverse_lazy('production:stage-list')

    def get_form(self, form_class=None):
        # Lock `code` after creation — STAGE_LAYERING / STAGE_CUTTING constants
        # + every `__stage__code=` ORM filter would silently stop matching if
        # the code mutated. Admin can still rename via `name`.
        form = super().get_form(form_class)
        form.fields['code'].disabled = True
        form.fields['code'].help_text = (
            "Locked after creation — rename via 'Display Name' instead. "
            "Changing the code would break service-level lookups."
        )
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Edit'
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Stage "{self.object.name}" updated.')
        return response


class StageDeleteView(LoginRequiredMixin, _StagePermissionRequired, DeleteView):
    required_perm = 'production.delete_stage'
    model = Stage
    template_name = 'production/stage_confirm_delete.html'
    success_url = reverse_lazy('production:stage-list')

    def form_valid(self, form):
        # Block delete if any Product still has this Stage in its workflow —
        # PROTECT FK would IntegrityError otherwise. Show a friendly message.
        in_use = WorkflowStage.objects.filter(stage=self.object).exists()
        if in_use:
            messages.error(
                self.request,
                f'Cannot delete "{self.object.name}" — it is still part of one or '
                f'more Product flows. Remove it from those products first.',
            )
            return redirect('production:stage-list')
        messages.success(self.request, f'Stage "{self.object.name}" deleted.')
        return super().form_valid(form)
