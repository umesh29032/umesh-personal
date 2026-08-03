"""machines URLConf — the register + assign/release actions (mgmt-only)."""
from django.urls import path

from . import views

app_name = 'machines'

urlpatterns = [
    path('', views.MachineListView.as_view(), name='list'),
    path('add/', views.MachineCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', views.MachineUpdateView.as_view(), name='edit'),
    path('<int:pk>/assign/', views.MachineAssignView.as_view(), name='assign'),
    path('assignments/<int:pk>/release/', views.MachineReleaseView.as_view(), name='release'),
]
