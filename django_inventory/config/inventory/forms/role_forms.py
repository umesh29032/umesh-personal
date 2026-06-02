from django import forms
from django.contrib.auth.models import Permission

from ..models import Role
from ..services.permission_service import (
    ROLE_EDITABLE_APPS,
    ROLE_EDITABLE_MODELS_EXCLUDED,
)


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
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = (
            Permission.objects
            .filter(content_type__app_label__in=ROLE_EDITABLE_APPS)
            .select_related('content_type')
            .order_by('content_type__app_label', 'content_type__model', 'codename')
        )
        for app_label, model in ROLE_EDITABLE_MODELS_EXCLUDED:
            qs = qs.exclude(content_type__app_label=app_label, content_type__model=model)
        self.fields['permissions'].queryset = qs
        for name, field in self.fields.items():
            if name == 'permissions':
                continue
            cls = field.widget.attrs.get('class', '')
            if 'form-control' not in cls and 'form-select' not in cls:
                field.widget.attrs['class'] = (cls + ' form-control').strip()

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if self.instance and self.instance.is_system and self.instance.code != code:
            raise forms.ValidationError("Cannot change the code of a system role.")
        return code
