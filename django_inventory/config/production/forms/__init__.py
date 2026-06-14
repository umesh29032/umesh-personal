"""Production forms — per-stage isolation.

Pattern (Phase 6+):
  forms/_shared.py   — shared widgets / querysets used across stages
  forms/layering.py  — Stage 1 (Layering) forms
  forms/cutting.py   — Stage 2 (Cutting) forms
  forms/product_forms.py  — non-stage CRUD forms
  forms/adda_forms.py     — non-stage CRUD forms

Future stages = drop in forms/<stage>.py + re-export here.
"""
from .product_forms import ProductForm
from .adda_forms import AddaCreateForm
from .layering import (
    AttachRollForm,
    CompleteLayeringForm,
    EditRollEntryForm,
    RemainingClothForm,
    StartLayeringForm,
)
from .cutting import (
    CuttingBreakupRowForm, CuttingBundleForm, CuttingDraftForm, CuttingForm,
    CuttingStartForm,
)
from .cutting_pattern import PatternVerifyForm, SizeAllocationForm
from .rate_forms import StageRateCorrectionForm


__all__ = [
    'ProductForm',
    'AddaCreateForm',
    # Layering stage
    'StartLayeringForm',
    'AttachRollForm',
    'EditRollEntryForm',
    'RemainingClothForm',
    'CompleteLayeringForm',
    # Cutting stage
    'CuttingForm',
    'CuttingStartForm',
    'CuttingBreakupRowForm',
    'CuttingBundleForm',
    'CuttingDraftForm',
    # Cutting-pattern stage
    'PatternVerifyForm',
    'SizeAllocationForm',
    # Stage rate correction (S1.1)
    'StageRateCorrectionForm',
]
