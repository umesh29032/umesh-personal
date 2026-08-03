from django import forms
from django.contrib.auth.models import Permission

from ..models import Role
from accounts.services.permission_service import permissions_qs_by_app


class RoleForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Permissions',
    )

    class Meta:
        model = Role
        fields = ['name', 'code', 'description', 'permissions']
        widgets = {
            # sf-input = base.html canonical input skin (.form-control was removed in Forms F-2 2026-06-16)
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'sf-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The ModelMultipleChoiceField queryset is the form's validation gate —
        # only pks IN it can be POSTed. It MUST match the curated editor
        # (ROLE_EDITOR_SECTIONS = content-type allowlist), not the whole app.
        # permissions_qs_by_app() is the same source the rendered checkbox
        # sections use, so offered == validatable. (Filtering by app_label alone
        # let a hand-crafted POST persist grants on service-only models the
        # editor deliberately hides — e.g. production.change_machinetype — which
        # live view gates then honored.)
        curated_ids = [p.pk for p in permissions_qs_by_app()]
        self.fields['permissions'].queryset = (
            Permission.objects
            .filter(pk__in=curated_ids)
            .select_related('content_type')
            .order_by('content_type__app_label', 'content_type__model', 'codename')
        )
        for name, field in self.fields.items():
            if name == 'permissions':
                continue
            cls = field.widget.attrs.get('class', '')
            if 'sf-input' not in cls:
                field.widget.attrs['class'] = (cls + ' sf-input').strip()

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if self.instance and self.instance.is_system and self.instance.code != code:
            raise forms.ValidationError("Cannot change the code of a system role.")
        return code
