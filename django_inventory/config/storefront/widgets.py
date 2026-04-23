"""
Custom Django admin widget for image fields with Cropper.js integration.
Provides: locked aspect ratio cropping, live card-size preview.
"""
from django.forms.widgets import ClearableFileInput


class CroppableImageWidget(ClearableFileInput):
    """
    Extends the default file input with:
    - A hidden field for Cropper.js crop coordinates (JSON)
    - Preview at exact card dimensions
    - Cropper.js modal with locked aspect ratio
    """
    template_name = 'storefront/widgets/croppable_image.html'

    def __init__(self, attrs=None, target_width=400, target_height=300):
        self.target_width = target_width
        self.target_height = target_height
        super().__init__(attrs=attrs)

    class Media:
        css = {
            'all': (
                'https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.2/cropper.min.css',
            ),
        }
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.2/cropper.min.js',
        )

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        # Scale for admin display (large images like hero 1440px → fit in ~480px)
        preview_scale = min(1.0, 480 / self.target_width)
        preview_w = int(self.target_width * preview_scale)
        preview_h = int(self.target_height * preview_scale)

        # Safely get URL — FieldFile with no file raises ValueError on .url
        current_url = ''
        if value:
            try:
                current_url = value.url
            except ValueError:
                pass

        context['widget'].update({
            'target_width': self.target_width,
            'target_height': self.target_height,
            'aspect_ratio': round(self.target_width / self.target_height, 6),
            'preview_width': preview_w,
            'preview_height': preview_h,
            'crop_field_name': name + '_crop_data',
            'current_url': current_url,
        })
        return context

    def value_from_datadict(self, data, files, name):
        return super().value_from_datadict(data, files, name)
