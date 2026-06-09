"""ProductPattern CRUD — reusable pattern library + per-product assignments.

YEH FILE KYU HAI?
─────────────────
Cutting master ko pata hona chahiye ki har Product ke liye kitne aur kaunse
patterns required hain (T-Shirt = 1 Front + 1 Back + 2 Sleeve etc.). Yeh
file admin ko 2 cheez karne deti hai:

  1. PATTERN LIBRARY MANAGE KARNA (`/production/patterns/`)
     Reusable shape entries: Front Panel, Back Panel, Sleeve, Collar...
     Code (slug), name, description, optional reference image.

  2. PER-PRODUCT ASSIGNMENT (`/production/products/<pk>/patterns/`)
     Product ke liye kaunse patterns + kitne pieces per Adda.
     ProductPatternAssignment(product, pattern, pieces_count) row banata.

VIEW CLASSES:
  ProductPatternListView   → list page (filterable by perms)
  ProductPatternCreateView → naya pattern banana
  ProductPatternUpdateView → edit (code field locked after create)
  ProductPatternDeleteView → delete (refuse if assignments exist)
  ProductPatternsEditView  → per-product assignment editor (add/remove/update_count)

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
from production.models import Product, ProductPattern, ProductPatternAssignment


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


# ── Per-product pattern editor ──────────────────────────────────────────────


class ProductPatternsEditView(LoginRequiredMixin, _PatternPermissionRequired, TemplateView):
    """Per-product pattern assignment editor.

    URL: /production/products/<pk>/patterns/

    YEH PAGE 3 ACTIONS HANDLE KARTA HAI (single endpoint, POST body se action):
      • action=add          → new ProductPatternAssignment row banana
      • action=remove       → assignment row delete
      • action=update_count → existing assignment ka pieces_count change

    Single POST endpoint pattern simpler hai — har action ke liye separate
    URL nahi banane padte. Django form submit me hidden `action` field se
    branch chalti hai.
    """

    required_perm = 'production.change_productpattern'
    template_name = 'production/product_patterns_edit.html'

    def get_product(self):
        return Product.objects.get(pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = self.get_product()
        ctx['product'] = product
        # Current assignments — template iss table mein dikhata hai.
        # select_related('pattern') = ek JOIN se pattern name fetch (no N+1).
        ctx['assignments'] = (
            product.pattern_assignments
            .select_related('pattern')
            .order_by('pattern__name')
        )
        # Available = jo abhi attached nahi hain. Exclude se duplicate
        # assignment prevent (unique_together(product, pattern) constraint).
        assigned_ids = set(product.pattern_assignments.values_list('pattern_id', flat=True))
        ctx['available_patterns'] = (
            ProductPattern.active
            .exclude(pk__in=assigned_ids)
            .order_by('name')
        )
        return ctx

    def post(self, request, pk):
        product = self.get_product()
        action = request.POST.get('action', '')

        if action == 'add':
            pattern_id = request.POST.get('pattern')
            # max(1, count) = safety — never less than 1 piece per assignment.
            count = int(request.POST.get('pieces_count') or 1)
            if not pattern_id:
                messages.error(request, "Pick a pattern.")
                return redirect('production:product-patterns', pk=pk)
            # get_or_create = idempotent. Same pattern dobara add → no-op.
            ProductPatternAssignment.objects.get_or_create(
                product=product, pattern_id=pattern_id,
                defaults={'pieces_count': max(1, count)},
            )
            messages.success(request, "Pattern added.")

        elif action == 'remove':
            assign_id = request.POST.get('assignment')
            # Filter by product too — defense against IDOR (id guessing).
            ProductPatternAssignment.objects.filter(pk=assign_id, product=product).delete()
            messages.success(request, "Pattern removed.")

        elif action == 'update_count':
            assign_id = request.POST.get('assignment')
            count = int(request.POST.get('pieces_count') or 1)
            ProductPatternAssignment.objects.filter(pk=assign_id, product=product).update(
                pieces_count=max(1, count),
            )
            messages.success(request, "Count updated.")

        # Same page pe redirect — Post-Redirect-Get pattern (refresh-safe).
        return redirect('production:product-patterns', pk=pk)
