"""My Work — karigar-scoped personal dashboard. Row-level filtered by user."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from ..services import WorkerService


class MyWorkView(LoginRequiredMixin, View):
    """
    Karigar's personal view. Shows only the logged-in user's own assignments
    and history — never cross-user data, enforced in the service layer.
    """
    template_name = 'inventory/my_work.html'

    def get(self, request):
        user = request.user
        ctx = {
            'summary': WorkerService.summary(user),
            'current_assignments': WorkerService.current_assignments(user)[:20],
            'active_batches': WorkerService.active_batches(user)[:10],
            'past_batches': WorkerService.past_batches(user)[:15],
        }
        return render(request, self.template_name, ctx)
