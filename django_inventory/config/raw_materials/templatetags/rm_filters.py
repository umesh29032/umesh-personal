"""raw_materials template filters.

YEH FILE KYU HAI?
─────────────────
Django template language mein default `getattr()` jaisa filter nahi hota.
master_list.html dynamic columns render karta hai — extra_columns context se
attr_name aata hai. Filter banaya hai taa-ke {{ obj|getattr:'field_name' }} kaam kare.
"""
from django import template

# template.Library() = filter/tag registration ka container.
# Django {% load rm_filters %} pe iss instance ke filters available kar deta hai.
register = template.Library()


@register.filter(name='getattr')
def get_attr(obj, attr_name):
    """Dynamic attribute access — {{ obj|getattr:'name' }} renders obj.name.

    Bonus: agar attr callable hai (method) to no-arg call ho jaata hai.
    """
    if obj is None:
        return ''
    # Python ka builtin getattr — agar field nahi hai to '' return (default arg)
    val = getattr(obj, attr_name, '')
    # Method ho to call karo (Django template ka default behavior)
    if callable(val):
        try:
            val = val()
        except TypeError:
            # Required args wala method — chhod do
            pass
    return val
