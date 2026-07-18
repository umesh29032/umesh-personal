"""Expense / payroll URLConf — mounted at /expense/. EVERY money URL.

Route groups / workflows exposed:
  my/                 worker self-view (Expected→Earned→Paid ladder)
  payroll/ workers/   management money board + per-worker detail
  workers/<id>/settle CASH PAYMENT only (V2-2: recovery happens at settlement)
  advances/add        loan entry
  settlements/…       the V2-2 Adda-settlement lifecycle: queue (ready/waiting)
                      → start draft → preview/variance/recovery → finalize →
                      reverse / reverse&supersede / discard
All management URLs are also sidebar-rule gated (menu hidden ⇒ URL blocked)."""
from django.urls import path

from expense import views

app_name = 'expense'

urlpatterns = [
    path('my/', views.MyEarningsView.as_view(), name='my-earnings'),
    path('payroll/', views.PayrollOverviewView.as_view(), name='payroll-overview'),
    path('workers/<int:pk>/', views.WorkerPayrollDetailView.as_view(), name='worker-detail'),
    path('workers/<int:pk>/settle/', views.SettlementCreateView.as_view(), name='settlement-create'),
    path('workers/<int:pk>/profile/', views.WorkerProfileEditView.as_view(), name='worker-profile'),
    # R4 (PDD §27-D4): pay-basis change — super-admin only (enforced in service).
    path('workers/<int:pk>/pay-basis/', views.WorkerPayBasisUpdateView.as_view(),
         name='worker-pay-basis'),
    # R7 (PDD §20): Full & Final — super-admin only (enforced in fnf_service).
    path('workers/<int:pk>/fnf/', views.WorkerFnFView.as_view(),
         name='worker-fnf'),
    path('advances/add/', views.AdvanceCreateView.as_view(), name='advance-add'),
    # R5 (PDD §21 / ADR-0011): factory-level running costs — never a ledger.
    path('expenses/', views.FactoryExpenseListView.as_view(),
         name='factory-expense-list'),
    path('expenses/add/', views.FactoryExpenseCreateView.as_view(),
         name='factory-expense-add'),
    # V2-2 Adda settlements (earning + recovery event; cash stays on /settle/).
    path('settlements/', views.AddaSettlementListView.as_view(),
         name='adda-settlement-list'),
    path('settlements/start/<int:adda_pk>/', views.AddaSettlementStartView.as_view(),
         name='adda-settlement-start'),
    path('settlements/<str:reference>/', views.AddaSettlementDetailView.as_view(),
         name='adda-settlement-detail'),
    # MEE-C (Phase 16): recurring-expense surfaces — same module, no parallel app.
    path('templates/', views.ExpenseTemplateListView.as_view(),
         name='expense-template-list'),
    path('templates/add/', views.ExpenseTemplateCreateView.as_view(),
         name='expense-template-add'),
    path('generate/', views.GenerateExpensesView.as_view(),
         name='expense-generate'),
    # RMX-D (Phase 17): the material-spend window (read-only; GET-only).
    path('material-spend/', views.MaterialSpendView.as_view(),
         name='material-spend'),
]
