"""Image-processing service — the single home for the storefront upload pipeline.

YEH FILE KYU HAI?
─────────────────
Pehle image crop/resize logic forms.py ke andar (`_process_image_fields`) tha —
matlab sirf form ke through hi chal sakta tha (seed script / future import / API
reuse nahi kar sakte the, na hi bina form ke test). Ab woh yahan service mein hai.

`processors.py` pure Pillow helper hai (no I/O side-effects beyond returning a new
file); yeh service usko orchestrate karta hai over a model instance's image fields.
"""
from django.core.files.uploadedfile import UploadedFile

from ..processors import process_image


def process_and_attach(instance, field_specs, *, cleaned_data, form_data):
    """For each (field_name, target_w, target_h) in `field_specs`: if a NEW file
    was uploaded, run it through the Pillow crop/resize pipeline and assign the
    processed result back onto `instance`.

    Decoupled from forms so any caller (form, seed, import, future API) can use it:
      • cleaned_data — mapping of field_name → uploaded value (form.cleaned_data)
      • form_data    — mapping carrying the Cropper.js crop JSON under
                       '<field>_crop_data' (form.data); '' = auto center-crop.

    Only actual NEW uploads (UploadedFile) are processed — existing FieldFile
    references on the instance are left untouched.
    """
    for field_name, target_w, target_h in field_specs:
        uploaded = cleaned_data.get(field_name)
        if not isinstance(uploaded, UploadedFile):
            continue
        crop_json = form_data.get(field_name + '_crop_data', '')
        processed = process_image(uploaded, crop_json, target_w, target_h)
        setattr(instance, field_name, processed)
