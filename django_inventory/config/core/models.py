"""Shared base models — the single source of truth for cross-app mixins.

YEH FILE KYU HAI?
─────────────────
Pehle `TimeStampedModel` aur `ActiveManager` har app (expense, production,
tracking, raw_materials) mein ALAG-ALAG copy-paste the. 4 copies = drift risk
(ek jagah change karo, baaki bhool jao). Ab ek hi jagah — yahan — define hote
hain aur sab apps `from core.models import ...` karke reuse karte hain.

`core` ek ABSTRACT-ONLY app hai: yahan ke models ka apna DB table NAHI banta
(`abstract = True`). Isliye core ki koi migration bhi nahi hoti. Future shared
concrete models (e.g. ek common `Address`) bhi yahan reh sakte hain.
"""
from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base — har row pe automatic created_at + updated_at.

    `auto_now_add=True` → INSERT pe ek baar set, baad mein change nahi.
    `auto_now=True`     → har SAVE pe refresh — "last modified" track karta hai.

    Append-only history tables (jahan row kabhi update nahi hoti) ke liye
    updated_at == created_at rehta hai (harmless).
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # abstract = is model ka apna table nahi banta; sirf fields inherit hote hain.
        abstract = True


class ActiveManager(models.Manager):
    """Non-default manager — sirf `is_active=True` rows return karta hai.

    Soft-archive pattern: master data models pe `is_active=False` flag se row
    "delete" kiye bina hide ho jaata hai. Form dropdowns + service lookups
    archived rows skip karna chahte hain; admin + audit sab dekhna chahte hain:

        Model.objects.all()    → sab rows (archived bhi)
        Model.active.all()     → sirf is_active=True

    Default `objects` ko swap NAHI karte (regression risk) — har model OPT-IN
    karta hai `active = ActiveManager()` likh ke. Jis model pe `is_active` field
    hi nahi, wahan yeh manager mat lagao (FieldError aayega).
    """

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class AbstractHistoryEntry(TimeStampedModel):
    """Abstract base for per-domain audit-log rows (tracking.ClothRollHistory,
    AddaHistory, ProductHistory). Every audit row records WHO did it (`actor`);
    each subclass adds its subject FK + a domain-specific `change_type` (with its
    own choices) + its own index.

    YEH BASE KYU? Pehle `actor` teeno history models mein byte-for-byte copy tha.
    Ek shared kernel base se naya audit column ek hi jagah add hota hai. Alag-alag
    concrete tables isliye rehti hain taaki har domain apni timeline apne FK+index
    se fast query kare (single mega-table sparse ho jaati).
    """

    # PROTECT + related_name='+' — audit row user ko delete hone se rokta hai,
    # aur User pe reverse-accessor clutter nahi banata.
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+',
    )

    class Meta:
        abstract = True


class FieldChangeMixin(models.Model):
    """Audit-triple for field-level edits — kaunsa field badla, old → new value.

    Field-diff history rows (ClothRoll, Product) use this. AddaHistory ISKO use
    NAHI karta — wo stage transitions log karta hai, scalar field diffs nahi.
    """

    field_name = models.CharField(max_length=64, blank=True)
    old_value = models.CharField(max_length=200, blank=True)
    new_value = models.CharField(max_length=200, blank=True)

    class Meta:
        abstract = True
