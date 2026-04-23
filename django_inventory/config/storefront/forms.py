"""
Admin forms for storefront models.
Each form attaches the CroppableImageWidget with the correct dimensions
and processes the image on save using Pillow.
"""
from django import forms
from django.core.files.uploadedfile import UploadedFile

from .models import (
    HomePageConfig, Category, FeaturedProduct,
    HeroShowcaseCard, WhyUsCard,
)
from .widgets import CroppableImageWidget
from .processors import process_image


# ── Helper to build a save that processes image fields ────────────────────────

def _process_image_fields(form, instance, field_specs):
    """
    For each (field_name, width, height) in field_specs, check if a new file
    was uploaded, process it with Pillow, and assign back to the instance.
    """
    for field_name, target_w, target_h in field_specs:
        uploaded = form.cleaned_data.get(field_name)
        # Only process actual new uploads — not existing FieldFile references.
        # UploadedFile = InMemoryUploadedFile or TemporaryUploadedFile (new upload).
        # FieldFile = existing file on the model (not a new upload).
        if not isinstance(uploaded, UploadedFile):
            continue

        crop_data_key = field_name + '_crop_data'
        crop_json = form.data.get(crop_data_key, '')

        processed = process_image(uploaded, crop_json, target_w, target_h)
        setattr(instance, field_name, processed)


# ── HomePageConfig ───────────────────────────────────────────────────────────

class HomePageConfigForm(forms.ModelForm):
    class Meta:
        model = HomePageConfig
        fields = '__all__'
        widgets = {
            'hero_background_image': CroppableImageWidget(target_width=1440, target_height=600),
            'brand_logo': CroppableImageWidget(target_width=200, target_height=80),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        _process_image_fields(self, instance, [
            ('hero_background_image', 1440, 600),
            ('brand_logo', 200, 80),
        ])
        if commit:
            instance.save()
        return instance


# ── Category ─────────────────────────────────────────────────────────────────

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'
        widgets = {
            'image': CroppableImageWidget(target_width=400, target_height=200),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        _process_image_fields(self, instance, [
            ('image', 400, 200),
        ])
        if commit:
            instance.save()
        return instance


# ── FeaturedProduct ──────────────────────────────────────────────────────────

class FeaturedProductForm(forms.ModelForm):
    class Meta:
        model = FeaturedProduct
        fields = '__all__'
        widgets = {
            'image': CroppableImageWidget(target_width=400, target_height=300),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        _process_image_fields(self, instance, [
            ('image', 400, 300),
        ])
        if commit:
            instance.save()
        return instance


# ── HeroShowcaseCard ─────────────────────────────────────────────────────────

class HeroShowcaseCardForm(forms.ModelForm):
    class Meta:
        model = HeroShowcaseCard
        fields = '__all__'
        widgets = {
            'image': CroppableImageWidget(target_width=200, target_height=200),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        _process_image_fields(self, instance, [
            ('image', 200, 200),
        ])
        if commit:
            instance.save()
        return instance


# ── WhyUsCard ────────────────────────────────────────────────────────────────

class WhyUsCardForm(forms.ModelForm):
    class Meta:
        model = WhyUsCard
        fields = '__all__'
        widgets = {
            'image': CroppableImageWidget(target_width=200, target_height=200),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        _process_image_fields(self, instance, [
            ('image', 200, 200),
        ])
        if commit:
            instance.save()
        return instance
