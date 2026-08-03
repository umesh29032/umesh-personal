"""bod.registry — the widget registry FRAMEWORK (BOD-D2: in code, zero models).

A widget = (kpi_id · section · title · read-call · certified presentation
component · gate predicate · responsive strategy · drill-down target) — the
contract §6.2 tuple. Widgets are DECLARED here so the sidebar, permissions,
docs, and the knowledge graph can enumerate them, and each renders
independently (fail-soft: one widget's failure degrades to an error tile,
never a 500 — enforced by the renderer when widgets land at BOD-C/D).

BOD-A state: the FRAMEWORK only — the registry is EMPTY by owner order ("Do
NOT implement any KPI. Do NOT wire any business data."). Every future widget
enters ONLY after its Metric Resolution Ladder row is closed at BOD-B
(BOD-D3: step-1 reuse · step-2 gated INERT extraction in the owning app ·
step-3 STOP for the owner — the BOD never owns a business calculation).
"""

from dataclasses import dataclass

# The owner's chartered section order (charter D1.5 — verbatim, fixed).
SECTIONS = (
    ("attention", "Business Attention"),
    ("production", "Production"),
    ("materials", "Raw Materials & Warehouses"),
    ("workers", "Workers"),
    ("financial", "Financial Overview"),
    ("machines", "Machines"),
    # Section 7 "Other Business Modules": content = a deferred owner
    # micro-decision, surfaced at the BOD-B ladder census (charter D1.4 #7).
)


@dataclass(frozen=True)
class Widget:
    """One dashboard tile. `read_call` = the OWNING service callable (ladder
    step-1/2 output — never BOD-local logic); `financial=True` additionally
    gates on FINANCIAL_ROLES (charter D1.6)."""

    kpi_id: str
    section: str            # a SECTIONS key
    title: str
    read_call: object       # callable() -> context dict (owning service)
    drill_down: str         # URL name of the owning module's page
    responsive_strategy: str  # the rule-11 statement, per widget
    financial: bool = False
    gate: object = None     # optional extra predicate(user) beyond the page gate


from bod import widgets as w

# BOD-C non-money waves — every entry's ladder row is CLOSED in the BOD-B
# census (BOD_BUILD_LOG §BOD-B.1) with the owner's 2026-07-18 dispositions.
# Money KPIs (F1/F2/F5/F6/W3) are ABSENT by owner order until BOD-D.
REGISTRY: tuple[Widget, ...] = (
    # Wave 1 — pure L1
    Widget("stalled-addas", "attention", "Stalled Addas", w.stalled_addas,
           "production:stalled-addas",
           "single-value tile; 1-col stack on phone"),
    Widget("pending-reports", "attention", "Pending Worker Reports", w.pending_reports,
           "production:pending-reports",
           "single-value tile; 1-col stack on phone"),
    Widget("settlements-ready", "attention", "Settlements Ready", w.settlements_ready,
           "expense:adda-settlement-list",
           "single-value tile; 1-col stack on phone"),
    Widget("settlements-blocked", "attention", "Settlements Blocked", w.settlements_blocked,
           "expense:adda-settlement-list",
           "value + one sub-line; sub-line wraps on phone"),
    Widget("active-addas", "production", "Active Addas", w.active_addas,
           "production:dashboard",
           "single-value tile; 1-col stack on phone"),
    Widget("completed-today", "production", "Completed Today", w.completed_today,
           "production:dashboard",
           "single-value tile; 1-col stack on phone"),
    Widget("machine-counts", "machines", "Machines", w.machine_counts,
           "machines:list",
           "value + three sub-lines; sub-lines stack on phone"),
    # Wave 2 — materials (gates G-1/G-2; G-3 pivot REJECTED for v1 by owner)
    Widget("roll-stock", "materials", "Roll Stock (available)", w.roll_stock,
           "raw_materials:cloth-dashboard",
           "value + three sub-lines; stacks 1-col on phone"),
    Widget("stock-by-warehouse", "materials", "Stock by Warehouse", w.stock_by_warehouse,
           "raw_materials:cloth-dashboard",
           "value + up-to-4 location rows; rows wrap on phone"),
    # Wave 3 — production extras (gate G-4) + workers (W1; W2 deferred by owner)
    Widget("on-hold-addas", "production", "On Hold", w.on_hold_addas,
           "production:dashboard",
           "single-value tile; 1-col stack on phone"),
    Widget("stage-chips", "production", "Work by Stage", w.stage_chips,
           "production:dashboard",
           "chip row; chips wrap to multiple lines on phone"),
    Widget("workers-active", "workers", "Workers Active Now", w.workers_active,
           "production:pending-reports",
           "value + one sub-line; 1-col stack on phone"),
    # BOD-D — the money wave (owner-authorized 2026-07-18). financial=True ⇒
    # FINANCIAL_ROLES gate on top of the page gate (charter D1.6). Census rows
    # F1/F2/F5/F6/F3-W3, all L1. W4 "Pending Settlements" = A1 by census —
    # deduped: the count lives on the settlements-ready attention tile, the ₹
    # dimension on expected-payouts (no duplicate tile).
    Widget("month-expenses", "financial", "This Month's Expenses", w.month_expenses,
           "expense:factory-expense-list",
           "₹ value + two sub-lines; 1-col stack on phone", financial=True),
    Widget("expense-categories", "financial", "Expenses by Category", w.expense_categories,
           "expense:factory-expense-list",
           "label→₹ rows; rows wrap on phone", financial=True),
    Widget("outstanding-payments", "financial", "Outstanding Worker Payments",
           w.outstanding_payments, "expense:payroll-overview",
           "single ₹ tile; 1-col stack on phone", financial=True),
    Widget("outstanding-advances", "financial", "Outstanding Advances",
           w.outstanding_advances, "expense:payroll-overview",
           "single ₹ tile; 1-col stack on phone", financial=True),
    Widget("expected-payouts", "financial", "Expected Worker Payouts",
           w.expected_payouts, "expense:adda-settlement-list",
           "₹ value + one sub-line; 1-col stack on phone", financial=True),
)


# Section 7 "Other Business Modules" — owner taste ruling (2026-07-18):
# "Navigation cards only. No counts." Pure links, deliberately NOT Widgets —
# nothing to read, nothing to fail-soft. (title, url_name, one-line purpose)
NAV_CARDS = (
    ("Pattern Intelligence", "patterns_ai:home", "Pattern & marker tools"),
    ("Storefront", "storefront:product_list", "Product listings"),
    ("Tracking", "tracking:dashboard", "Barcodes & movement history"),
)


def widgets_for_section(section_key):
    return [w for w in REGISTRY if w.section == section_key]
