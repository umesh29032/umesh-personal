"""machines views — parse→gate→delegate ONLY (R10-A).

Management-gated register (frozen rule: machines are ops, not personal).
All writes go through services.machine_service (the single writer).
"""
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from accounts.services import MANAGEMENT_ROLES, user_has_role
from machines.models import Machine, MachineAssignment
from machines.services import machine_service
from production.models import Adda, MachineType


class _ManagementOnly(UserPassesTestMixin):
    def test_func(self):
        return user_has_role(self.request.user, MANAGEMENT_ROLES)


class MachineForm(forms.ModelForm):
    # Config-master convenience: type a NEW kind here instead of picking one
    # (register-page flow: 'Overlock Machine' the first time you buy one).
    new_type_name = forms.CharField(
        required=False, label='…or new Machine Type',
        help_text="Creates the type if it doesn't exist (e.g. Overlock Machine).")

    class Meta:
        model = Machine
        fields = ['code', 'name', 'machine_type', 'status', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['machine_type'].queryset = MachineType.active.all()
        self.fields['machine_type'].required = False   # either pick OR type new

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('machine_type') and not (cleaned.get('new_type_name') or '').strip():
            self.add_error('machine_type', 'Pick a Machine Type or name a new one.')
        return cleaned


class MachineListView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """The register: counts strip + one summary card per machine (mobile-first)."""
    template_name = 'machines/machine_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        machines = list(
            Machine.objects.select_related('machine_type').order_by('code'))
        open_by_machine = {
            a.machine_id: a
            for a in MachineAssignment.objects
            .filter(end_at__isnull=True)
            .select_related('worker', 'adda')
        }
        for m in machines:
            m.open_assignment = open_by_machine.get(m.pk)
        ctx['machines'] = machines
        ctx['counts'] = machine_service.register_counts()
        # Pickers for the inline assign panel: active workers with a
        # production role. Machines are NOT stages, so this is deliberately
        # role-based, not eligible_stage_workers (documented in the plan).
        from accounts.services import PRODUCTION_ROLES
        User = get_user_model()
        ctx['workers'] = (
            User.objects.filter(is_active=True, role__code__in=list(PRODUCTION_ROLES))
            .order_by('first_name', 'email'))   # names first — the picker reads like the floor roster
        ctx['addas'] = Adda.objects.filter(
            status=Adda.Status.IN_PROGRESS).order_by('-started_at')
        return ctx


class MachineCreateView(LoginRequiredMixin, _ManagementOnly, View):
    template_name = 'machines/machine_form.html'

    def get(self, request):
        from django.shortcuts import render
        return render(request, self.template_name, {'form': MachineForm()})

    def post(self, request):
        from django.shortcuts import render
        form = MachineForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})
        try:
            mtype = form.cleaned_data['machine_type'] or machine_service.create_machine_type(
                name=form.cleaned_data['new_type_name'], user=request.user)
            machine_service.create_machine(
                code=form.cleaned_data['code'],
                name=form.cleaned_data['name'],
                machine_type=mtype,
                status=form.cleaned_data['status'],
                notes=form.cleaned_data['notes'],
                user=request.user)
        except ValidationError as exc:
            form.add_error(None, '; '.join(exc.messages))
            return render(request, self.template_name, {'form': form})
        messages.success(request, f"Machine {form.cleaned_data['code']} created.")
        return redirect('machines:list')


class MachineUpdateView(LoginRequiredMixin, _ManagementOnly, View):
    template_name = 'machines/machine_form.html'

    def get(self, request, pk):
        from django.shortcuts import render
        machine = get_object_or_404(Machine, pk=pk)
        return render(request, self.template_name,
                      {'form': MachineForm(instance=machine), 'machine': machine})

    def post(self, request, pk):
        from django.shortcuts import render
        machine = get_object_or_404(Machine, pk=pk)
        form = MachineForm(request.POST, instance=machine)
        if not form.is_valid():
            return render(request, self.template_name,
                          {'form': form, 'machine': machine})
        try:
            mtype = form.cleaned_data['machine_type'] or machine_service.create_machine_type(
                name=form.cleaned_data['new_type_name'], user=request.user)
            machine_service.update_machine(
                machine,
                code=form.cleaned_data['code'],
                name=form.cleaned_data['name'],
                machine_type=mtype,
                status=form.cleaned_data['status'],
                notes=form.cleaned_data['notes'],
                user=request.user)
        except ValidationError as exc:
            form.add_error(None, '; '.join(exc.messages))
            return render(request, self.template_name,
                          {'form': form, 'machine': machine})
        messages.success(request, f"Machine {machine.code} updated.")
        return redirect('machines:list')


class MachineAssignView(LoginRequiredMixin, _ManagementOnly, View):
    def post(self, request, pk):
        machine = get_object_or_404(Machine, pk=pk)
        User = get_user_model()
        worker = get_object_or_404(User, pk=request.POST.get('worker'))
        adda = None
        if request.POST.get('adda'):
            adda = get_object_or_404(Adda, pk=request.POST['adda'])
        try:
            machine_service.assign(
                machine=machine, worker=worker, adda=adda, user=request.user)
        except ValidationError as exc:
            messages.error(request, '; '.join(exc.messages))
        else:
            messages.success(
                request,
                f"{machine.code} assigned to {worker.get_full_name() or worker.email}.")
        return redirect('machines:list')


class MachineReleaseView(LoginRequiredMixin, _ManagementOnly, View):
    def post(self, request, pk):
        assignment = get_object_or_404(
            MachineAssignment, pk=pk, end_at__isnull=True)
        try:
            machine_service.release(assignment, user=request.user)
        except ValidationError as exc:
            messages.error(request, '; '.join(exc.messages))
        else:
            messages.success(request, f"{assignment.machine.code} released.")
        return redirect('machines:list')
