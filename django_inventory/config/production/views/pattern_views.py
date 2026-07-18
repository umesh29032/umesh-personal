"""ProductPattern CRUD — reusable pattern library + per-product assignments.

YEH FILE KYU HAI?
─────────────────
Cutting master ko pata hona chahiye ki har Product ke liye kitne aur kaunse
patterns required hain (T-Shirt = 1 Front + 1 Back + 2 Sleeve etc.). Yeh
file admin ko 2 cheez karne deti hai:

  1. PATTERN LIBRARY MANAGE KARNA (`/production/patterns/`)
     Reusable shape entries: Front Panel, Back Panel, Sleeve, Collar...
     Code (slug), name, description, optional reference image.

  2. PLATFORM ENTRY (`/production/products/<pk>/patterns/`)
     Phase 1/2: redirects into the patterns_ai platform (Dashboard);
     per-product structure ab PATTERN BLUEPRINT module mein hai
     (patterns_ai:blueprint — atomic register_pattern_definition).

VIEW CLASSES:
  ProductPatternListView   → list page (filterable by perms)
  ProductPatternCreateView → naya pattern banana
  ProductPatternUpdateView → edit (code field locked after create)
  ProductPatternDeleteView → delete (refuse if assignments exist)
  ProductPatternsEntryView / ProductPatternBlueprintRedirectView → platform redirects

RBAC (Django built-in perms — admin role editor mein assignable):
  • List/View      → production.view_productpattern
  • Add/Change/Del → production.{add,change,delete}_productpattern
Super Admin role bypasses every perm via `user_has_perm`.
"""
from __future__ import annotations

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, ListView, TemplateView, UpdateView,
)

from accounts.services import user_has_perm
from production.models import ProductPattern


class _PatternPermissionRequired(UserPassesTestMixin):
    """ProductPattern admin pages ko gate karne wala mixin.

    Django ka UserPassesTestMixin pattern follow karta hai — `test_func()`
    True return kare to view chalega, False to 403. Sub-classes
    `required_perm` set karte hain (e.g. 'production.view_productpattern').

    `user_has_perm` mein ROLE_SUPER_ADMIN implicit bypass hai — super admin
    ko har perm checkbox tick karne ki zaroorat nahi.
    """

    required_perm = ''

    def test_func(self):
        return user_has_perm(self.request.user, self.required_perm)


class ProductPatternForm(forms.ModelForm):
    class Meta:
        model = ProductPattern
        fields = ['code', 'name', 'description', 'reference_image', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ProductPatternListView(LoginRequiredMixin, _PatternPermissionRequired, ListView):
    required_perm = 'production.view_productpattern'
    model = ProductPattern
    template_name = 'production/pattern_list.html'
    context_object_name = 'patterns'

    def get_queryset(self):
        return (
            ProductPattern.objects
            .prefetch_related('product_assignments__product')
            .order_by('name')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        ctx['can_add'] = user_has_perm(u, 'production.add_productpattern')
        ctx['can_change'] = user_has_perm(u, 'production.change_productpattern')
        ctx['can_delete'] = user_has_perm(u, 'production.delete_productpattern')
        return ctx


class ProductPatternCreateView(LoginRequiredMixin, _PatternPermissionRequired, CreateView):
    required_perm = 'production.add_productpattern'
    model = ProductPattern
    form_class = ProductPatternForm
    template_name = 'production/pattern_form.html'
    success_url = reverse_lazy('production:pattern-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Pattern "{self.object.name}" created.')
        return response


class ProductPatternUpdateView(LoginRequiredMixin, _PatternPermissionRequired, UpdateView):
    required_perm = 'production.change_productpattern'
    model = ProductPattern
    form_class = ProductPatternForm
    template_name = 'production/pattern_form.html'
    success_url = reverse_lazy('production:pattern-list')

    def get_form(self, form_class=None):
        # Same rationale as Stage.code lock — services may reference the code.
        form = super().get_form(form_class)
        form.fields['code'].disabled = True
        form.fields['code'].help_text = "Locked after creation."
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Pattern "{self.object.name}" updated.')
        return response


class ProductPatternDeleteView(LoginRequiredMixin, _PatternPermissionRequired, DeleteView):
    required_perm = 'production.delete_productpattern'
    model = ProductPattern
    template_name = 'production/pattern_confirm_delete.html'
    success_url = reverse_lazy('production:pattern-list')

    def form_valid(self, form):
        if self.object.product_assignments.exists():
            messages.error(
                self.request,
                f'Cannot delete "{self.object.name}" — still assigned to a product. '
                'Detach it first.',
            )
            return redirect('production:pattern-list')
        messages.success(self.request, f'Pattern "{self.object.name}" deleted.')
        return super().form_valid(form)


# ── Phase-1 platform entry ─────────────────────────────────────────────────


class ProductPatternsEntryView(LoginRequiredMixin, TemplateView):
    """`Patterns` action → the Pattern Dashboard (patterns_ai).

    Login-only by design (Phase-1 D-2): the dashboard enforces its own
    management-role gate, and the Blueprint keeps its strict perm below —
    a perm here would 403 manager-role users the dashboard allows.
    Redirect by URL name only — no patterns_ai import (ADR-H wall).
    """

    def get(self, request, pk):
        from django.urls import reverse
        target = reverse('patterns_ai:dashboard') + f'?product={pk}'
        return redirect(target)


class ProductPatternBlueprintRedirectView(LoginRequiredMixin, TemplateView):
    """Phase 2 (owner-approved D-1): the Blueprint module lives in
    patterns_ai — production only launches the platform. Old URL kept as
    a redirect so Phase-1 links keep working."""

    def get(self, request, pk):
        from django.urls import reverse
        return redirect(reverse('patterns_ai:blueprint') + f'?product={pk}')


# Phase 2 (owner-approved): ProductPatternsEditView retired — the Pattern
# Blueprint module (patterns_ai:blueprint) is the single structure surface;
# all its POST actions (add/remove/update_count) moved there behind the
# atomic register_pattern_definition + single-writer setters.
