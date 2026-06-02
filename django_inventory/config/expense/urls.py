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
]
