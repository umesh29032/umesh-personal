"""Raw Material ke dashboards.

YEH FILE KYU HAI?
─────────────────
Do dashboards:
  /raw-materials/         → overall index (Cloth live + Elastic/Rib/Sui/Dhaga placeholder tiles)
  /raw-materials/cloth/   → cloth-specific — Type × Color pivot, date+color filter, by-location

Type × Color pivot:
  ClothRoll queryset ko values('cloth_type', 'cloth_color').annotate(Count) se group karke
  Python side pe `type_rows` dict mein pivot kiya — har type ka colors list with counts.
"""
from datetime import datetime, time

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import TemplateView

from inventory.services import ROLE_SUPER_ADMIN, user_has_role
from raw_materials.models import ClothColor, ClothRoll, ClothType, StorageLocation

from .mixins import ProductionRoleMixin


def _parse_date(s):
    """Parse YYYY-MM-DD from querystring; tz-aware midnight in active TZ."""
    if not s:
        return None
    try:
        d = datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        return None
    return timezone.make_aware(datetime.combine(d, time.min))


class RawMaterialDashboardView(LoginRequiredMixin, ProductionRoleMixin, TemplateView):
    """Overall raw-material index — Cloth is live; other materials coming later.

    Each tile shows status + a quick number summary so users see at a glance
    which materials have inventory and which are placeholder.
    """

    template_name = 'raw_materials/raw_material_dashboard.html'

    # Future material types — purely descriptive for now. When a future migration
    # adds Elastic / Rib / etc. models, flip `live=True` and link to their dashboards.
    FUTURE_MATERIALS = [
        {'code': 'elastic', 'name': 'Elastic',   'desc': 'Waistband + cuff elastic', 'live': False},
        {'code': 'rib',     'name': 'Rib',       'desc': 'Knit ribbing rolls',       'live': False},
        {'code': 'sui',     'name': 'Sui',       'desc': 'Sewing needles',           'live': False},
        {'code': 'dhaga',   'name': 'Dhaga',     'desc': 'Sewing thread cones',      'live': False},
        {'code': 'button',  'name': 'Button',    'desc': 'Buttons + closures',       'live': False},
        {'code': 'tag',     'name': 'Tag',       'desc': 'Brand + size tags',        'live': False},
    ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cloth_total = ClothRoll.objects.count()
        cloth_available = ClothRoll.objects.filter(status=ClothRoll.Status.NOT_USED).count()
        cloth_types = ClothType.active.count()
        cloth_colors = ClothColor.active.count()
        ctx['cloth'] = {
            'total': cloth_total,
            'available': cloth_available,
            'used': cloth_total - cloth_available,
            'types': cloth_types,
            'colors': cloth_colors,
        }
        ctx['future'] = self.FUTURE_MATERIALS
        ctx['can_add_rolls'] = user_has_role(self.request.user, [ROLE_SUPER_ADMIN])
        # Time logs — saari cloth-roll movements ka top-level overview (accordion)
        from tracking.models import ClothRollHistory
        ctx['roll_events'] = (
            ClothRollHistory.objects
            .select_related('roll', 'roll__cloth_type', 'roll__cloth_color', 'actor')
            .order_by('-created_at')[:30]
        )
        return ctx


class ClothDashboardView(LoginRequiredMixin, ProductionRoleMixin, TemplateView):
    """Cloth-only dashboard: Type × Color breakup, by-location, date + color filter."""

    template_name = 'raw_materials/cloth_dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        from_dt = _parse_date(self.request.GET.get('from'))
        to_dt = _parse_date(self.request.GET.get('to'))
        if to_dt:
            to_dt = to_dt + timezone.timedelta(days=1)
        color_id = self.request.GET.get('color') or ''

        rolls = ClothRoll.objects.all()
        if from_dt:
            rolls = rolls.filter(created_at__gte=from_dt)
        if to_dt:
            rolls = rolls.filter(created_at__lt=to_dt)
        if color_id.isdigit():
            rolls = rolls.filter(cloth_color_id=int(color_id))

        ctx['total_rolls'] = rolls.count()
        ctx['available_rolls'] = rolls.filter(status=ClothRoll.Status.NOT_USED).count()
        ctx['used_rolls'] = rolls.filter(status=ClothRoll.Status.USED).count()

        # ── Type × Color breakup ───────────────────────────────────────────
        # Rows = ClothType (active). Inside each row, list every color present
        # with its count for that type. Filter (date + color) already applied
        # to `rolls`; we count per (type, color) by grouping the queryset.
        type_color_counts = (
            rolls.values('cloth_type_id', 'cloth_type__name',
                         'cloth_color_id', 'cloth_color__name', 'cloth_color__hex_code')
            .annotate(
                total=Count('id'),
                available=Count('id', filter=Q(status=ClothRoll.Status.NOT_USED)),
            )
            .order_by('cloth_type__name', 'cloth_color__name')
        )
        # Pivot: group by cloth_type.
        type_rows: dict[int, dict] = {}
        for row in type_color_counts:
            t_id = row['cloth_type_id']
            if t_id not in type_rows:
                type_rows[t_id] = {
                    'name': row['cloth_type__name'],
                    'total': 0,
                    'available': 0,
                    'colors': [],
                }
            type_rows[t_id]['colors'].append({
                'name': row['cloth_color__name'],
                'hex_code': row['cloth_color__hex_code'],
                'total': row['total'],
                'available': row['available'],
            })
            type_rows[t_id]['total'] += row['total']
            type_rows[t_id]['available'] += row['available']
        ctx['type_breakup'] = sorted(type_rows.values(), key=lambda r: r['name'])

        # ── By location ───────────────────────────────────────────────────
        ctx['by_location'] = (
            StorageLocation.active
            .annotate(
                roll_count=Count('rolls', filter=(
                    (Q(rolls__created_at__gte=from_dt) if from_dt else Q())
                    & (Q(rolls__created_at__lt=to_dt) if to_dt else Q())
                    & (Q(rolls__cloth_color_id=int(color_id)) if color_id.isdigit() else Q())
                )),
                available=Count('rolls', filter=(
                    Q(rolls__status=ClothRoll.Status.NOT_USED)
                    & (Q(rolls__created_at__gte=from_dt) if from_dt else Q())
                    & (Q(rolls__created_at__lt=to_dt) if to_dt else Q())
                    & (Q(rolls__cloth_color_id=int(color_id)) if color_id.isdigit() else Q())
                )),
            )
            .order_by('name')
        )

        ctx['recent_rolls'] = (
            rolls.select_related('cloth_type', 'cloth_color', 'storage_location')
            .order_by('-created_at')[:15]
        )
        # Time logs — ClothRollHistory latest 30 events (accordion mein render hota hai)
        from tracking.models import ClothRollHistory
        ctx['roll_events'] = (
            ClothRollHistory.objects
            .select_related('roll', 'roll__cloth_type', 'roll__cloth_color', 'actor')
            .order_by('-created_at')[:30]
        )
        ctx['active_colors'] = ClothColor.active.order_by('name')
        ctx['filter_from'] = self.request.GET.get('from', '')
        ctx['filter_to'] = self.request.GET.get('to', '')
        ctx['filter_color'] = color_id
        ctx['can_add_rolls'] = user_has_role(self.request.user, [ROLE_SUPER_ADMIN])
        return ctx
