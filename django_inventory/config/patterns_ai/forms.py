"""patterns_ai forms — Block 3B: the manual-marker capture form ONLY.

Forms PARSE; services VALIDATE and WRITE (I-1). This form deliberately does
not expose origin (pinned to manual_photo server-side) or adda (D11 is not a
UI concern here).
"""
from django import forms

from patterns_ai.models import CaptureAsset, Marker


class ManualMarkerForm(forms.Form):
    product = forms.IntegerField(widget=forms.HiddenInput, required=False)  # replaced in view
    label = forms.CharField(
        max_length=100, required=False,
        help_text="Floor name, e.g. Master's 37in tube layout.")
    usable_width_mm = forms.IntegerField(
        min_value=1, label='Usable width (mm)',
        help_text='Taped at the table — never the roll label.')
    construction = forms.ChoiceField(
        choices=Marker.Construction.choices,
        initial=Marker.Construction.TUBULAR, label='Fabric lay')
    ratio_text = forms.CharField(
        required=False, label='Size ratio (optional)',
        help_text="Garments per repeat, e.g. 1:2, 2:2 (size code : count).")
    source = forms.ChoiceField(choices=CaptureAsset.Source.choices,
                               initial=CaptureAsset.Source.CAMERA)
    photo = forms.FileField(
        label='Chalk layout photo',
        help_text='JPEG/PNG/WEBP — the layout drawn on the top ply.')
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))

    def clean_ratio_text(self):
        raw = (self.cleaned_data.get('ratio_text') or '').strip()
        if not raw:
            return {}
        counts = {}
        try:
            for part in raw.replace(';', ',').split(','):
                if not part.strip():
                    continue
                code, n = part.split(':')
                counts[code.strip()] = int(n)
                if int(n) <= 0:
                    raise ValueError
        except ValueError:
            raise forms.ValidationError(
                "Use 'sizecode:count' pairs separated by commas, e.g. 1:2, 2:1.")
        return counts


class MarkerUsageForm(forms.Form):
    """Record 'this Adda cut with this marker' — parse-only; the feedback
    service owns every rule (usable status, D11 own-adda, plies/repeats ≥ 1)."""
    adda = forms.IntegerField(widget=forms.HiddenInput, required=False)  # select rendered in template
    plies = forms.IntegerField(min_value=1, label='Plies laid')
    repeats = forms.IntegerField(min_value=1, initial=1,
                                 label='Marker repeats along the lay')
    measured_width_mm = forms.IntegerField(
        min_value=1, required=False, label='Measured usable width (mm)',
        help_text='Taped at the table for THIS lay — leave blank if unmeasured.')
    notes = forms.CharField(required=False, max_length=255)


class MarkerOutcomeForm(forms.Form):
    """Raw facts only — every field optional (honest-NULL). UI speaks metres;
    conversion to integer mm happens at the edge (units.m_to_mm)."""
    fabric_in_m = forms.DecimalField(
        required=False, min_value=0, decimal_places=2, max_digits=8,
        label='Fabric laid (meters)',
        help_text='plies × lay length — linear metres consumed.')
    garments_cut = forms.IntegerField(required=False, min_value=0,
                                      label='Garments cut')
    garments_packed = forms.IntegerField(required=False, min_value=0,
                                         label='Garments packed')
    leftover_m = forms.DecimalField(
        required=False, min_value=0, decimal_places=2, max_digits=8,
        label='Leftover (meters)')


# ── P2 geometry-era forms (parse-only; services own every rule) ─────────────

ARUCO_CHOICES = [(d, d) for d in
                 ('DICT_5X5_1000', 'DICT_4X4_1000', 'DICT_6X6_1000')]


class MatRegisterForm(forms.Form):
    mat_code = forms.SlugField(max_length=32, label='Mat code (physical label)')
    name = forms.CharField(max_length=100, required=False)


class MatCommissionForm(forms.Form):
    """Board spec + tape control distances (ADR-E commissioning ritual).
    Distances: one per line as `from_id,to_id,expected_mm`."""
    squares_x = forms.IntegerField(min_value=4, initial=14)
    squares_y = forms.IntegerField(min_value=4, initial=10)
    square_mm = forms.DecimalField(min_value=10, initial=100)
    marker_mm = forms.DecimalField(min_value=5, initial=75)
    aruco_dict = forms.ChoiceField(choices=ARUCO_CHOICES,
                                   initial='DICT_5X5_1000')
    distances_text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3,
                                     'placeholder': '0,12,1200.0'}),
        label='Tape control distances (from_id,to_id,expected_mm per line)')
    notes = forms.CharField(max_length=200, required=False)

    def clean_distances_text(self):
        rows = []
        for i, line in enumerate(self.cleaned_data['distances_text']
                                 .strip().splitlines(), 1):
            bits = [b.strip() for b in line.split(',')]
            try:
                rows.append({'from_id': int(bits[0]), 'to_id': int(bits[1]),
                             'expected_mm': float(bits[2])})
            except (ValueError, IndexError):
                raise forms.ValidationError(
                    f'line {i}: use from_id,to_id,expected_mm (e.g. 0,12,1200.0)')
        if not rows:
            raise forms.ValidationError('at least one control distance is required.')
        return rows

    def board_spec(self):
        cd = self.cleaned_data
        return {'schema_version': 1,
                'squares_x': cd['squares_x'], 'squares_y': cd['squares_y'],
                'square_mm': float(cd['square_mm']),
                'marker_mm': float(cd['marker_mm']),
                'aruco_dict': cd['aruco_dict']}

    def control_distances(self):
        return {'schema_version': 1,
                'distances': self.cleaned_data['distances_text']}


# Phase 2: PieceCreateForm retired with PieceCreateView — registration
# is the Blueprint module's atomic register_pattern_definition.


class PatternCaptureForm(forms.Form):
    """The phone wizard: pattern photo ON the commissioned mat."""
    photo = forms.FileField(label='Pattern photo (piece flat on the mat)')
    source = forms.ChoiceField(choices=[('camera', 'Camera'),
                                        ('gallery', 'Gallery')],
                               initial='camera', widget=forms.HiddenInput)


class DxfImportForm(forms.Form):
    dxf_file = forms.FileField(label='DXF-AAMA file (one piece per file)')
