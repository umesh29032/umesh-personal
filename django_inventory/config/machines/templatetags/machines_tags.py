"""machines template tags — the Operations-dashboard tile (R10-A).

WHY a template tag: machines sits ABOVE production in the layer map (its
models FK down to production.Adda/MachineType), so production python must
NEVER import machines. The production dashboard TEMPLATE includes this tag
instead — the python import direction stays machines→production only.
Management-gated inside the tag; graceful when the app has no data.
"""
from django import template

from accounts.services import MANAGEMENT_ROLES, user_has_role

register = template.Library()


@register.inclusion_tag('machines/_ops_tile.html')
def machines_ops_tile(user):
    if not user_has_role(user, MANAGEMENT_ROLES):
        return {'show': False}
    try:
        from machines.services import machine_service
        counts = machine_service.register_counts()
    except Exception:      # graceful-degrade posture (same as the R5 expense digest)
        return {'show': False}
    return {'show': True, 'counts': counts}
