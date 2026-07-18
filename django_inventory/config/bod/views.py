"""bod.views — the dashboard shell (BOD-A: empty summary shell; widgets land
at BOD-C/D only after their BOD-B ladder rows close).

READ-ONLY BY ARCHITECTURE: TemplateView GET only (POST → 405 by Django's
default http_method_not_allowed — pinned in tests); refresh = as-of page load
+ a manual reload affordance + the visible "Last Updated" timestamp (BOD-D5)."""

from django.utils import timezone
from django.views.generic import TemplateView

from bod.mixins import BODAccessMixin
from bod.registry import NAV_CARDS, SECTIONS, widgets_for_section


class BODDashboardView(BODAccessMixin, TemplateView):
    template_name = "bod/dashboard.html"
    http_method_names = ["get", "head", "options"]  # zero-POST, explicit

    def get_context_data(self, **kwargs):
        from accounts.services import user_can_view_financials
        ctx = super().get_context_data(**kwargs)
        cache = {}  # per-request: shared owner calls run ONCE (BOD-D6 discipline)
        # Charter D1.6: financial widgets gate on FINANCIAL_ROLES ON TOP of the
        # page gate (v1 SA-only reaches here; the extra wall future-proofs any
        # widened page audience — money tiles never leak past FINANCIAL_ROLES).
        can_money = user_can_view_financials(self.request.user)
        ctx["sections"] = [
            {"key": key, "label": label,
             "widgets": [self._render_widget(wdg, cache)
                         for wdg in widgets_for_section(key)
                         if can_money or not wdg.financial]}
            for key, label in SECTIONS
        ]
        # Section 7 — nav cards only, no counts (owner taste ruling 2026-07-18)
        ctx["nav_cards"] = NAV_CARDS
        ctx["as_of"] = timezone.localtime()  # BOD-D5: current-at-load, shown on screen
        return ctx

    @staticmethod
    def _render_widget(widget, cache):
        """Fail-soft (contract §6.2): one widget's failure degrades to an
        error tile — the board never 500s on a single owner-call problem."""
        try:
            tile = widget.read_call(cache)
            return {"widget": widget, "tile": tile, "error": False}
        except Exception:
            import logging
            logging.getLogger(__name__).exception(
                "BOD widget %s failed (fail-soft)", widget.kpi_id)
            return {"widget": widget, "tile": None, "error": True}
