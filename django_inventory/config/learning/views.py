"""learning.views — read-only course reader. GET only, no models, no writes.

Access (owner ruling 2026-08-02): login **and** the `learning:index` row on the
Access Control page. Tick a role there → that role gets the whole course section;
untick → it loses it. `super_admin` always passes (service-layer bypass, so an
admin cannot lock themselves out). The `student` role ships allowed — see
accounts/migrations/0020_student_role_and_learning_access.py.

WHY the check is on a shared mixin and not just the sidebar row:
`permission_service.can_access_url_name()` returns **True for any url_name that has
no rule**, and only `learning:index` carries a rule. Relying on the middleware alone
would therefore hide the menu link and still serve `/learn/sql/14-indexes/` to
anyone who typed it. Gating every learning view against the SAME url_name makes one
Access-Control checkbox govern the entire section — the documented "the view's own
mixin gates it = defense in depth" contract.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse, JsonResponse
from django.views import View
from django.views.generic import TemplateView

from learning import progress_service, services

# The ONE url_name that governs the whole section. Keep in step with the row seeded
# by accounts migration 0020 and with the MenuItem in permission_service.SIDEBAR.
LEARNING_GATE_URL_NAME = 'learning:index'


class _LearningAccessMixin(LoginRequiredMixin):
    """Login + the Access-Control switch for the learning section.

    Reuses the project's single permission chokepoint (rule 6: no raw
    `is_superuser` checks in views) so the sidebar link and the URL can never
    disagree about who may read the courses.
    """

    def dispatch(self, request, *args, **kwargs):
        # LoginRequiredMixin first: anonymous must be redirected to login, not 403'd.
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        from accounts.services.permission_service import can_access_url_name
        if not can_access_url_name(request.user, LEARNING_GATE_URL_NAME):
            return self._deny(request)
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _deny(request):
        """Deny the SAME way SidebarAccessMiddleware does.

        `/learn/` itself carries the rule, so the middleware already intercepts it
        and answers 302-to-dashboard with a message. The chapter/interview/search
        URLs carry no rule, so they reach this mixin instead — and they must behave
        identically, or a blocked user would get a friendly redirect on one URL and
        a bare 404 on the next. AJAX callers get 403 because a redirect would
        corrupt a fetch (same reasoning as the middleware).
        """
        from django.contrib import messages
        from django.shortcuts import redirect
        from django.urls import reverse
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(
                {'detail': "You don't have the access to this page."}, status=403)
        messages.error(request, "You don't have the access to this page.")
        return redirect(reverse('inventory:my_dashboard'))


class _ReadOnly(_LearningAccessMixin, TemplateView):
    """GET/HEAD only — a POST to a course page is a 405, by construction."""
    http_method_names = ['get', 'head', 'options']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Inlined once per page — no extra request for a stylesheet that only
        # this section needs.
        ctx['pygments_css'] = services.pygments_css()
        return ctx


class CourseIndexView(_ReadOnly):
    template_name = 'learning/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        courses = services.all_courses()
        # Per-course completion, so the dashboard shows a real learning state
        # rather than a static list of links (VISION §9).
        for item in courses:
            item['progress'] = progress_service.course_progress(
                user, item['course'].slug)
        ctx['courses'] = courses
        ctx['interview_total'] = services.interview_questions()['total']
        ctx['revision_pages'] = list(services.REVISION_PAGES.values())
        ctx['resume'] = progress_service.resume_point(user)
        ctx['stats'] = progress_service.learning_stats(user)
        ctx['bookmarks'] = progress_service.bookmarks_for(user)
        ctx['dash'] = progress_service.dashboard(user)
        return ctx


class CourseDetailView(_ReadOnly):
    template_name = 'learning/course.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        data = services.course_overview(kwargs['course'])
        if data is None:
            raise Http404('No such course')
        ctx.update(data)
        ctx['progress'] = progress_service.course_progress(
            self.request.user, kwargs['course'])
        ctx['states'] = progress_service.chapter_states(
            self.request.user, kwargs['course'])
        return ctx


class ChapterView(_ReadOnly):
    template_name = 'learning/chapter.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        page = services.render_chapter(kwargs['course'], kwargs['chapter'])
        if page is None:
            raise Http404('No such chapter')
        ctx['page'] = page
        ctx['chapters'] = services.chapters_for(kwargs['course'])
        # Opening a chapter IS the progress signal — no button required for the
        # "continue learning" and streak features to work.
        progress_service.mark_opened(
            self.request.user, kwargs['course'], kwargs['chapter'])
        ctx['state'] = progress_service.chapter_state(
            self.request.user, kwargs['course'], kwargs['chapter'])
        ctx['progress'] = progress_service.course_progress(
            self.request.user, kwargs['course'])
        return ctx


class InterviewPrepView(_ReadOnly):
    """Every interview question from every chapter, grouped by level.

    Generated from the chapters — so it can never fall out of step with them.
    """
    template_name = 'learning/interview.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(services.interview_questions())
        return ctx


class RevisionView(_ReadOnly):
    """A generated revision page (mistakes / cheat sheets).

    Content is harvested from the chapters at request time — VISION §8: revision
    material is generated, never written twice.
    """
    template_name = 'learning/revision.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        data = services.revision_page(kwargs['page'])
        if data is None:
            raise Http404('No such revision page')
        ctx.update(data)
        return ctx


class SearchView(_ReadOnly):
    """Search across every chapter of every course."""
    template_name = 'learning/search.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(services.search(self.request.GET.get('q', '')))
        return ctx


class _ProgressAction(_LearningAccessMixin, View):
    """POST-only companions to the read-only pages.

    The content views stay GET-only (a course page can never be POSTed to);
    user state gets its own explicit endpoints. Both return JSON so the page
    can update without a reload, and both are per-user by construction — the
    user comes from the session, never from the request body.

    Gated by the SAME Access-Control switch as the pages: a role that cannot read
    the courses must not be able to write progress against them either, or the
    write endpoints become a way to probe which chapters exist.
    """
    http_method_names = ['post']


class ToggleCompleteView(_ProgressAction):
    def post(self, request, course, chapter):
        if services.find_chapter(course, chapter) is None:
            raise Http404('No such chapter')
        done = request.POST.get('done') == '1'
        state = progress_service.set_complete(
            request.user, course, chapter, done=done)
        return JsonResponse({
            'complete': state,
            'progress': progress_service.course_progress(request.user, course)
                        | {'done_slugs': None},   # sets aren't JSON-serialisable
        })


class HeartbeatView(_ProgressAction):
    """Reading-time + scroll-depth beacon from the chapter page.

    Fire-and-forget: returns 204 with no body, because the page must never wait
    on it and a failed beat is not worth telling the reader about.
    """
    def post(self, request, course, chapter):
        if services.find_chapter(course, chapter) is not None:
            progress_service.add_time(
                request.user, course, chapter,
                seconds=request.POST.get('s', 0),
                scroll=request.POST.get('p') or None)
        return HttpResponse(status=204)


class ToggleBookmarkView(_ProgressAction):
    def post(self, request, course, chapter):
        if services.find_chapter(course, chapter) is None:
            raise Http404('No such chapter')
        return JsonResponse({
            'bookmarked': progress_service.toggle_bookmark(
                request.user, course, chapter),
        })
