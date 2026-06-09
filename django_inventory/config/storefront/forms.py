"""
Admin forms for storefront models.
Each form attaches the CroppableImageWidget with the correct dimensions
and processes the image on save using Pillow.
"""
from django import forms

from .models import (
    HomePageConfig, Category, FeaturedProduct,
    HeroShowcaseCard, WhyUsCard,
)
from .widgets import CroppableImageWidget
from .services import image_service


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
        image_service.process_and_attach(
            instance,
            [('hero_background_image', 1440, 600), ('brand_logo', 200, 80)],
            cleaned_data=self.cleaned_data, form_data=self.data,
        )
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
        image_service.process_and_attach(
            instance, [('image', 400, 200)],
            cleaned_data=self.cleaned_data, form_data=self.data,
        )
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
        image_service.process_and_attach(
            instance, [('image', 400, 300)],
            cleaned_data=self.cleaned_data, form_data=self.data,
        )
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
        image_service.process_and_attach(
            instance, [('image', 200, 200)],
            cleaned_data=self.cleaned_data, form_data=self.data,
        )
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
        image_service.process_and_attach(
            instance, [('image', 200, 200)],
            cleaned_data=self.cleaned_data, form_data=self.data,
        )
        if commit:
            instance.save()
        return instance
