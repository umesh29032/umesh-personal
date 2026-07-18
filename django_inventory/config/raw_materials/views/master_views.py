"""ClothType / ClothColor / StorageLocation ke CRUD views.

YEH FILE KYU HAI?
─────────────────
Teen master models — saare ka same list/create/update/archive/delete pattern.
Code duplicate avoid karne ke liye generic base CBVs banaye (_MasterListView etc),
phir har model ka thin subclass jo sirf model + URL names override karta hai.

Shared templates teen ke teen models ke liye:
  master_list.html, master_form.html, master_confirm_archive.html, master_confirm_delete.html
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, View

from raw_materials.forms import ClothColorForm, ClothTypeForm, StorageLocationForm
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import archive_master, hard_delete_master, restore_master

from .mixins import ManagementRoleMixin, ProductionRoleMixin


# ── Shared base ──────────────────────────────────────────────────────────────

class _MasterListView(LoginRequiredMixin, ProductionRoleMixin, ListView):
    """Lists all rows for a master model (active + archived shown together)."""
    template_name = 'raw_materials/master_list.html'
    context_object_name = 'rows'
    paginate_by = None  # masters are tiny (10s–100s); skip pagination

    model = None                         # subclasses set this
    title = ''                           # display heading
    create_url_name = ''
    update_url_name = ''
    archive_url_name = ''
    delete_url_name = ''
    extra_columns = ()                   # tuples of (header, attr_name)

    def get_queryset(self):
        # Meta.ordering=['name'] on each master model gives stable order.
        return self.model.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'title': self.title,
            'create_url_name': self.create_url_name,
            'update_url_name': self.update_url_name,
            'archive_url_name': self.archive_url_name,
            'delete_url_name': self.delete_url_name,
            'extra_columns': self.extra_columns,
        })
        return ctx


# Phase-E cert (2026-07-12): master WRITES = management acts — the old
# ProductionRoleMixin let any worker create/edit/archive/delete cloth
# types/colors/locations (same name-trap class as the M9 roll-edit fix).
# Lists stay ProductionRole (read-only; SidebarItemRule additionally
# blocks workers at the middleware).
class _MasterCreateView(LoginRequiredMixin, ManagementRoleMixin, CreateView):
    template_name = 'raw_materials/master_form.html'
    title = ''
    list_url_name = ''

    def get_success_url(self):
        return reverse_lazy(self.list_url_name)

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, f"{self.title} created.")
        return resp

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = self.title
        ctx['list_url_name'] = self.list_url_name
        ctx['is_edit'] = False
        return ctx


class _MasterUpdateView(LoginRequiredMixin, ManagementRoleMixin, UpdateView):
    template_name = 'raw_materials/master_form.html'
    title = ''
    list_url_name = ''

    def get_success_url(self):
        return reverse_lazy(self.list_url_name)

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, f"{self.title} updated.")
        return resp

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = self.title
        ctx['list_url_name'] = self.list_url_name
        ctx['is_edit'] = True
        return ctx


class _MasterArchiveView(LoginRequiredMixin, ManagementRoleMixin, View):
    """POST-only soft-archive endpoint (sets is_active=False).

    GET renders a confirmation page; POST flips the flag via service.
    """
    model = None
    title = ''
    list_url_name = ''
    template_name = 'raw_materials/master_confirm_archive.html'

    def get(self, request, pk):
        from django.shortcuts import render
        obj = self.model.objects.get(pk=pk)
        return render(request, self.template_name, {
            'object': obj,
            'title': self.title,
            'list_url_name': self.list_url_name,
        })

    def post(self, request, pk):
        obj = self.model.objects.get(pk=pk)
        if obj.is_active:
            archive_master(request.user, obj)
            messages.success(request, f"{obj} archived.")
        else:
            restore_master(request.user, obj)
            messages.success(request, f"{obj} restored.")
        return redirect(self.list_url_name)


class _MasterDeleteView(LoginRequiredMixin, ManagementRoleMixin, DeleteView):
    """Hard delete. Service raises ValidationError if FK references exist."""
    model = None
    title = ''
    list_url_name = ''
    template_name = 'raw_materials/master_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy(self.list_url_name)

    # DEPLOYMENT_BACKLOG #5 (fixed MGT-E 2026-07-12): Django DeleteView ka
    # default context sirf object+form deta hai — template ko title +
    # list_url_name chahiye (Cancel link `{% url list_url_name %}`), warna
    # confirm GET NoReverseMatch 500. Archive view yehi explicitly pass karta hai.
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = self.title
        ctx['list_url_name'] = self.list_url_name
        return ctx

    def form_valid(self, form):
        try:
            hard_delete_master(self.request.user, self.object)
        except ValidationError as exc:
            messages.error(self.request, str(exc))
            return redirect(self.list_url_name)
        messages.success(self.request, f"{self.object} deleted.")
        return redirect(self.list_url_name)


# ── ClothType ────────────────────────────────────────────────────────────────

class ClothTypeListView(_MasterListView):
    model = ClothType
    title = 'Cloth Types'
    create_url_name = 'raw_materials:cloth-type-create'
    update_url_name = 'raw_materials:cloth-type-update'
    archive_url_name = 'raw_materials:cloth-type-archive'
    delete_url_name = 'raw_materials:cloth-type-delete'


class ClothTypeCreateView(_MasterCreateView):
    model = ClothType
    form_class = ClothTypeForm
    title = 'Cloth Type'
    list_url_name = 'raw_materials:cloth-type-list'


class ClothTypeUpdateView(_MasterUpdateView):
    model = ClothType
    form_class = ClothTypeForm
    title = 'Cloth Type'
    list_url_name = 'raw_materials:cloth-type-list'


class ClothTypeArchiveView(_MasterArchiveView):
    model = ClothType
    title = 'Cloth Type'
    list_url_name = 'raw_materials:cloth-type-list'


class ClothTypeDeleteView(_MasterDeleteView):
    model = ClothType
    title = 'Cloth Type'
    list_url_name = 'raw_materials:cloth-type-list'


# ── ClothColor ───────────────────────────────────────────────────────────────

class ClothColorListView(_MasterListView):
    model = ClothColor
    title = 'Cloth Colors'
    extra_columns = (('Swatch', 'hex_code'),)
    create_url_name = 'raw_materials:cloth-color-create'
    update_url_name = 'raw_materials:cloth-color-update'
    archive_url_name = 'raw_materials:cloth-color-archive'
    delete_url_name = 'raw_materials:cloth-color-delete'


class ClothColorCreateView(_MasterCreateView):
    model = ClothColor
    form_class = ClothColorForm
    title = 'Cloth Color'
    list_url_name = 'raw_materials:cloth-color-list'


class ClothColorUpdateView(_MasterUpdateView):
    model = ClothColor
    form_class = ClothColorForm
    title = 'Cloth Color'
    list_url_name = 'raw_materials:cloth-color-list'


class ClothColorArchiveView(_MasterArchiveView):
    model = ClothColor
    title = 'Cloth Color'
    list_url_name = 'raw_materials:cloth-color-list'


class ClothColorDeleteView(_MasterDeleteView):
    model = ClothColor
    title = 'Cloth Color'
    list_url_name = 'raw_materials:cloth-color-list'


# ── StorageLocation ──────────────────────────────────────────────────────────

class StorageLocationListView(_MasterListView):
    model = StorageLocation
    title = 'Storage Locations'
    extra_columns = (('Code', 'code'),)
    create_url_name = 'raw_materials:storage-create'
    update_url_name = 'raw_materials:storage-update'
    archive_url_name = 'raw_materials:storage-archive'
    delete_url_name = 'raw_materials:storage-delete'


class StorageLocationCreateView(_MasterCreateView):
    model = StorageLocation
    form_class = StorageLocationForm
    title = 'Storage Location'
    list_url_name = 'raw_materials:storage-list'


class StorageLocationUpdateView(_MasterUpdateView):
    model = StorageLocation
    form_class = StorageLocationForm
    title = 'Storage Location'
    list_url_name = 'raw_materials:storage-list'


class StorageLocationArchiveView(_MasterArchiveView):
    model = StorageLocation
    title = 'Storage Location'
    list_url_name = 'raw_materials:storage-list'


class StorageLocationDeleteView(_MasterDeleteView):
    model = StorageLocation
    title = 'Storage Location'
    list_url_name = 'raw_materials:storage-list'
