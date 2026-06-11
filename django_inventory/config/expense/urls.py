"""Expense / payroll URLConf — mounted at /expense/."""
from django.urls import path

from expense import views

app_name = 'expense'

urlpatterns = [
    path('my/', views.MyEarningsView.as_view(), name='my-earnings'),
    path('payroll/', views.PayrollOverviewView.as_view(), name='payroll-overview'),
    path('workers/<int:pk>/', views.WorkerPayrollDetailView.as_view(), name='worker-detail'),
    path('workers/<int:pk>/settle/', views.SettlementCreateView.as_view(), name='settlement-create'),
    path('workers/<int:pk>/profile/', views.WorkerProfileEditView.as_view(), name='worker-profile'),
    path('advances/add/', views.AdvanceCreateView.as_view(), name='advance-add'),
    # V2-2 Adda settlements (earning + recovery event; cash stays on /settle/).
    path('settlements/', views.AddaSettlementListView.as_view(),
         name='adda-settlement-list'),
    path('settlements/start/<int:adda_pk>/', views.AddaSettlementStartView.as_view(),
         name='adda-settlement-start'),
    path('settlements/<str:reference>/', views.AddaSettlementDetailView.as_view(),
         name='adda-settlement-detail'),
]
