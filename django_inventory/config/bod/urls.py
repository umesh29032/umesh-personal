"""bod URLs — one GET route (v1 has zero POST surfaces, BOD-D4)."""

from django.urls import path

from bod.views import BODDashboardView

app_name = "bod"

urlpatterns = [
    path("", BODDashboardView.as_view(), name="dashboard"),
]
