"""Money rendering — the single owner for currency display.

`{% money amount %}` renders an amount byte-identically to the legacy inline
`₹{{ amount|floatformat:2 }}`: the rupee symbol followed by Django's floatformat
with 2 decimals. Number formatting is delegated ENTIRELY to
``django.template.defaultfilters.floatformat`` — same rounding, no thousands
separator, native negative sign, ``None``/invalid -> "" — so the rendered output
is identical to what the templates produced before.

Future-proofing: the optional ``currency`` argument is reserved so multi-currency
can be introduced later WITHOUT editing any call site (it may eventually default
from company settings / request context). It is intentionally inert today —
output is INR-only (₹), exactly as the current templates render. Do not add
locale/grouping logic here without an explicit money-display decision (golden
₹225 byte-identity + ADR-0009 cost-truth).
"""
from django import template
from django.template.defaultfilters import floatformat

register = template.Library()


@register.simple_tag
def money(amount, currency=None):
    # `currency` is reserved for future multi-currency; today always INR (₹).
    # Delegate ALL number formatting to floatformat -> byte-identical to
    # `₹{{ amount|floatformat:2 }}`. No commas, no locale, no rounding changes.
    return "₹" + floatformat(amount, 2)
