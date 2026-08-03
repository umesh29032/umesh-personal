"""learning app tests — the course reader.

What these PIN (the promises that must not silently break):
  1. Every course folder on disk is fully served — no page is silently dropped.
  2. The reader is READ-ONLY: POST is refused, and the app has no models.
  3. Login is required (the content is not public yet).
  4. Markdown becomes real HTML: headings, tables, code, teaching blockquotes.
  5. Cross-chapter `.md` links are rewritten to web URLs (multi-tab reading).
  6. The interview page is GENERATED from the chapters, so it can never drift.
  7. Unknown course/chapter → 404, never a 500.
"""
from django.apps import apps
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from learning import services
from learning.registry import COURSES, DOCS_ROOT


def _learner(email):
    """A user who is ALLOWED to read the courses.

    Since 2026-08-02 `/learn/` is governed by the `learning:index` Access-Control
    row, seeded to the `student` role (accounts migration 0020). A role-less user
    now gets a 404 — correct behaviour, so every test learner needs that role.
    """
    from accounts.models import Role
    user = User.objects.create_user(email=email, password='x')
    user.role = Role.objects.get(code='student')
    user.save(update_fields=['role'])
    return user


class RegistryTests(TestCase):
    def test_every_markdown_file_is_reachable(self):
        """A course folder's .md files must ALL be served.

        This is the regression that matters: `ARCHITECTURE.md` was dropped by
        the first version of the filename regex, losing a real page silently.
        """
        for course in COURSES:
            folder = DOCS_ROOT / course.folder
            on_disk = {p.name for p in folder.glob('*.md')}
            served = {ref.filename for ref in services.chapters_for(course.slug)}
            self.assertEqual(on_disk, served,
                             f'{course.slug}: pages on disk but not served: '
                             f'{on_disk - served}')

    def test_slugs_are_unique_and_url_safe(self):
        for course in COURSES:
            slugs = [ref.slug for ref in services.chapters_for(course.slug)]
            self.assertEqual(len(slugs), len(set(slugs)), 'duplicate slug')
            for s in slugs:
                self.assertRegex(s, r'^[a-z0-9-]+$')

    def test_chapters_are_in_teaching_order(self):
        nums = [r.number for r in services.chapters_for('sql')]
        self.assertEqual(nums, sorted(nums), 'chapters must be ordered')
        self.assertTrue(nums[0].startswith('00'), 'overview comes first')

    def test_titles_come_from_the_files_own_h1(self):
        ref = services.find_chapter('sql', '07-joins')
        self.assertIn('JOIN', ref.title)


class RenderTests(TestCase):
    def test_markdown_becomes_html(self):
        page = services.render_chapter('sql', '07-joins')
        self.assertIsNotNone(page)
        self.assertIn('<h1 id="purpose">', page.html)   # anchored for the TOC
        self.assertIn('<table>', page.html)
        self.assertIn('<pre>', page.html)
        self.assertIn('<blockquote>', page.html)        # the Samjho/warning boxes

    def test_the_twelve_teaching_sections_become_the_toc(self):
        page = services.render_chapter('sql', '07-joins')
        titles = [s['title'] for s in page.sections]
        for expected in ('Purpose', 'The Problem', 'Interview Questions',
                         'Cheat Sheet', 'Homework'):
            self.assertIn(expected, titles)

    def test_internal_md_links_are_rewritten_to_urls(self):
        """`](07_JOINs.md)` must become `/learn/sql/07-joins/` — otherwise every
        cross-reference in the course 404s in a browser."""
        page = services.render_chapter('sql', '08-group-by-and-aggregates')
        self.assertNotIn('.md"', page.html)
        self.assertIn('/learn/sql/', page.html)

    def test_page_title_is_not_duplicated(self):
        """The hero shows the title; the prose must not repeat it."""
        page = services.render_chapter('sql', '07-joins')
        self.assertNotIn('JOINs: How Tables Point at Each Other', page.html)

    def test_nav_blockquote_is_stripped_but_teaching_boxes_survive(self):
        page = services.render_chapter('sql', '07-joins')
        self.assertNotIn('Part of', page.html[:400])
        self.assertIn('Samjho', page.html)

    def test_prev_next_chain_is_complete(self):
        refs = services.chapters_for('sql')
        first = services.render_chapter('sql', refs[0].slug)
        last = services.render_chapter('sql', refs[-1].slug)
        self.assertIsNone(first.prev)
        self.assertIsNone(last.next)
        self.assertEqual(first.next.slug, refs[1].slug)

    def test_unknown_course_or_chapter_returns_none_not_error(self):
        self.assertIsNone(services.render_chapter('nope', 'nope'))
        self.assertIsNone(services.render_chapter('sql', 'no-such-chapter'))


class InterviewHarvestTests(TestCase):
    def test_questions_are_harvested_from_every_level(self):
        data = services.interview_questions()
        self.assertGreater(data['total'], 100, 'expected a large question bank')
        by_level = {g['level']: g['count'] for g in data['groups']}
        for level in ('Junior', 'Mid', 'Senior', 'Staff'):
            self.assertGreater(by_level[level], 0, f'no {level} questions found')

    def test_each_question_links_back_to_its_chapter(self):
        data = services.interview_questions()
        q = data['groups'][0]['questions'][0]
        self.assertTrue(q['question'])
        self.assertTrue(q['answer'])
        self.assertIn(q['course'].slug, {c.slug for c in COURSES})
        self.assertTrue(q['chapter'].slug)


class AccessAndViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _learner('learner@test')

    def test_login_is_required(self):
        for url in (reverse('learning:index'),
                    reverse('learning:interview'),
                    reverse('learning:course', args=['sql']),
                    reverse('learning:chapter', args=['sql', '07-joins'])):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302, url)
            self.assertIn('/app/', resp.url)

    def test_pages_render_for_a_logged_in_user(self):
        self.client.force_login(self.user)
        for url in (reverse('learning:index'),
                    reverse('learning:interview'),
                    reverse('learning:course', args=['sql']),
                    reverse('learning:course', args=['deployment']),
                    reverse('learning:chapter', args=['sql', '07-joins'])):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_every_single_chapter_of_every_course_renders(self):
        """The whole corpus, end to end. A broken .md must fail HERE, loudly,
        not when the owner opens it."""
        self.client.force_login(self.user)
        for course in COURSES:
            for ref in services.chapters_for(course.slug):
                url = reverse('learning:chapter', args=[course.slug, ref.slug])
                self.assertEqual(self.client.get(url).status_code, 200,
                                 f'{course.slug}/{ref.slug} failed to render')

    def test_read_only_post_is_refused(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse('learning:chapter',
                                        args=['sql', '07-joins']))
        self.assertEqual(resp.status_code, 405)

    def test_unknown_urls_are_404_not_500(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(
            reverse('learning:course', args=['nope'])).status_code, 404)
        self.assertEqual(self.client.get(
            reverse('learning:chapter', args=['sql', 'nope'])).status_code, 404)

    def test_app_has_no_CONTENT_models(self):
        """THE CORE-LAW ALARM (docs/LEARNING_PLATFORM_VISION.md §2).

        Progress models are allowed — progress is user state. CONTENT models are
        forbidden, because the markdown is the single source of truth. If a model
        ever appears here that is not per-user state, the law has been broken.
        """
        allowed = {'LessonProgress', 'Bookmark'}      # per-user state only
        found = {m.__name__ for m in apps.get_app_config('learning').get_models()}
        self.assertTrue(found <= allowed,
                        f'unexpected model(s) in learning: {found - allowed}. '
                        'Content must never be stored — see VISION §2.')

    def test_no_model_stores_chapter_text(self):
        """A content model could also sneak in as a big text field on a progress
        model. Guard the shape, not just the name."""
        for model in apps.get_app_config('learning').get_models():
            for f in model._meta.get_fields():
                if getattr(f, 'get_internal_type', None) and \
                        f.get_internal_type() == 'TextField':
                    self.fail(f'{model.__name__}.{f.name} is a TextField — '
                              'chapter content must live in markdown, not the DB.')


class ProgressTests(TestCase):
    """Per-user learning state: progress, completion %, resume, bookmarks.

    The isolation test is the important one — one learner's state must never be
    visible to another.
    """

    @classmethod
    def setUpTestData(cls):
        cls.a = _learner('learner-a@test')
        cls.b = _learner('learner-b@test')

    def test_opening_a_chapter_records_progress(self):
        from learning.models import LessonProgress
        self.client.force_login(self.a)
        url = reverse('learning:chapter', args=['sql', '07-joins'])
        self.client.get(url)
        row = LessonProgress.objects.get(user=self.a, course_slug='sql',
                                         chapter_slug='07-joins')
        self.assertEqual(row.open_count, 1)
        self.assertIsNone(row.completed_at, 'opening is not completing')
        self.client.get(url)
        row.refresh_from_db()
        self.assertEqual(row.open_count, 2)

    def test_mark_complete_and_uncomplete(self):
        from learning import progress_service
        self.client.force_login(self.a)
        url = reverse('learning:toggle-complete', args=['sql', '07-joins'])
        self.assertTrue(self.client.post(url, {'done': '1'}).json()['complete'])
        self.assertTrue(progress_service.chapter_state(
            self.a, 'sql', '07-joins')['complete'])
        self.assertFalse(self.client.post(url, {'done': '0'}).json()['complete'])

    def test_course_percentage_counts_only_real_chapters(self):
        from learning import progress_service
        from learning.models import LessonProgress
        from django.utils import timezone
        # a completed row for a chapter that no longer exists must NOT inflate %
        LessonProgress.objects.create(
            user=self.a, course_slug='sql', chapter_slug='99-deleted',
            completed_at=timezone.now())
        p = progress_service.course_progress(self.a, 'sql')
        self.assertEqual(p['done'], 0)
        self.assertEqual(p['percent'], 0)

    def test_bookmark_toggles(self):
        self.client.force_login(self.a)
        url = reverse('learning:toggle-bookmark', args=['sql', '07-joins'])
        self.assertTrue(self.client.post(url).json()['bookmarked'])
        self.assertFalse(self.client.post(url).json()['bookmarked'])

    def test_resume_point_is_the_last_opened_chapter(self):
        from learning import progress_service
        self.client.force_login(self.a)
        self.client.get(reverse('learning:chapter', args=['sql', '05-select-basics']))
        self.client.get(reverse('learning:chapter', args=['sql', '07-joins']))
        resume = progress_service.resume_point(self.a)
        self.assertEqual(resume['chapter'].slug, '07-joins')

    def test_progress_is_isolated_between_users(self):
        from learning import progress_service
        self.client.force_login(self.a)
        self.client.post(reverse('learning:toggle-complete',
                                 args=['sql', '07-joins']), {'done': '1'})
        self.assertEqual(progress_service.course_progress(self.a, 'sql')['done'], 1)
        self.assertEqual(progress_service.course_progress(self.b, 'sql')['done'], 0)
        self.assertIsNone(progress_service.resume_point(self.b))

    def test_progress_endpoints_require_login_and_reject_get(self):
        url = reverse('learning:toggle-complete', args=['sql', '07-joins'])
        self.assertEqual(self.client.post(url).status_code, 302)   # anonymous
        self.client.force_login(self.a)
        self.assertEqual(self.client.get(url).status_code, 405)    # POST-only

    def test_unknown_chapter_cannot_create_progress(self):
        from learning.models import LessonProgress
        self.client.force_login(self.a)
        resp = self.client.post(reverse('learning:toggle-complete',
                                        args=['sql', 'not-a-chapter']),
                                {'done': '1'})
        self.assertEqual(resp.status_code, 404)
        self.assertFalse(LessonProgress.objects.filter(
            chapter_slug='not-a-chapter').exists())


class GeneratedRevisionTests(TestCase):
    """VISION §8: revision material is GENERATED from the chapters, never
    written twice. These pins are what make that claim true rather than a hope."""

    @classmethod
    def setUpTestData(cls):
        cls.user = _learner('revise@test')

    def test_harvest_pulls_one_named_section_from_every_chapter(self):
        items = services.harvest_section('Beginner Mistakes')
        self.assertGreater(len(items), 60, 'expected most chapters to contribute')
        for item in items:
            self.assertTrue(item['html'])
            self.assertTrue(item['chapter'].slug)

    def test_harvest_of_a_missing_heading_is_empty_not_an_error(self):
        self.assertEqual(services.harvest_section('No Such Heading Anywhere'), ())

    def test_harvest_stops_at_the_next_section(self):
        """A harvested section must not swallow the sections that follow it —
        otherwise every revision page becomes the whole chapter."""
        items = services.harvest_section('Cheat Sheet')
        joined = ' '.join(i['html'] for i in items)
        self.assertNotIn('Further Reading', joined)
        self.assertNotIn('id="homework"', joined)

    def test_both_revision_pages_render(self):
        self.client.force_login(self.user)
        for slug in ('mistakes', 'cheatsheet'):
            resp = self.client.get(reverse('learning:revision', args=[slug]))
            self.assertEqual(resp.status_code, 200)
            self.assertGreater(resp.context['count'], 60)

    def test_unknown_revision_page_is_404(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(
            reverse('learning:revision', args=['nope'])).status_code, 404)

    def test_revision_requires_login(self):
        self.assertEqual(self.client.get(
            reverse('learning:revision', args=['mistakes'])).status_code, 302)


# Overview + reference pages are deliberately outside the teaching contract:
# 00 is the course map, ARCHITECTURE.md is a reference diagram page.
EXEMPT = {'00_COURSE_OVERVIEW.md', 'ARCHITECTURE.md'}

# The 19-section teaching contract (VISION §7), matched by PREFIX so a chapter
# may enrich a heading ("Beginner Mistakes (the greatest hits)").
CONTRACT = (
    'Learning Objectives', 'Purpose', 'The Problem', 'Theory',
    'Real World Example', 'Visual Diagram', 'Practical',
    'Production Walkthrough', 'Debugging Guide', 'Performance Notes',
    'Security Considerations', 'Architecture Decisions', 'Best Practices',
    'Beginner Mistakes', 'Interview Questions', 'Revision Notes',
    'Cheat Sheet', 'My ERP', 'Practice Tasks', 'Homework', 'Further Reading',
)


class ChapterContractTests(TestCase):
    """Every teaching chapter must carry the full section contract, and every
    generated page must actually receive content from every chapter.

    Both pins exist because both promises broke silently once:
      - ch 42 used `# Beginner Mistakes (the greatest hits)`, which the
        exact-match harvester rejected — its interview questions never
        reached the interview bank at all.
      - the deployment course kept Further Reading at H2, so it never
        appeared in the chapter TOC (which is built from H1s only).
    """

    def _headings(self, course, ref):
        """H1s of a chapter, ignoring `#` comment lines inside code fences."""
        raw = (DOCS_ROOT / course.folder / ref.filename).read_text()
        out, fence = [], False
        for line in raw.splitlines():
            if line.startswith('```'):
                fence = not fence
                continue
            if not fence and line.startswith('# '):
                out.append(line[2:].strip())
        return out[1:]                      # drop the file's own title H1

    def test_every_chapter_carries_the_full_teaching_contract(self):
        missing = {}
        for course in COURSES:
            for ref in services.chapters_for(course.slug):
                if ref.filename in EXEMPT:
                    continue
                heads = self._headings(course, ref)
                gaps = [s for s in CONTRACT
                        if not any(h.startswith(s) for h in heads)]
                if gaps:
                    missing[f'{course.slug}/{ref.filename}'] = gaps
        self.assertEqual(missing, {}, f'sections missing: {missing}')

    def test_every_chapter_feeds_every_generated_page(self):
        """A chapter that contributes nothing to a revision page is content
        that was written and then silently lost."""
        for heading in ('Beginner Mistakes', 'Interview Questions',
                        'Cheat Sheet', 'Revision Notes', 'Practice Tasks'):
            got = {(d['course'].slug, d['chapter'].filename)
                   for d in services.harvest_section(heading)}
            for course in COURSES:
                for ref in services.chapters_for(course.slug):
                    if ref.filename in EXEMPT:
                        continue
                    self.assertIn((course.slug, ref.filename), got,
                                  f'{course.slug}/{ref.filename} contributes '
                                  f'nothing to "{heading}"')

    def test_enriched_headings_are_still_harvested(self):
        """The exact ch-42 regression: a parenthetical suffix must not hide a
        section from the generated pages."""
        body = services._section_body(
            '# Cheat Sheet (the playbook of playbooks)\nkeep this\n# Next\nno',
            'Cheat Sheet')
        self.assertEqual(body, 'keep this')

    def test_every_labelled_question_reaches_the_interview_bank(self):
        """The regression that cost the most: the deployment course wrote its
        questions as `**Junior — "Q"** A` instead of `- **Junior:** Q — A`, so
        all 185 of them were invisible on the interview page. Count what the
        chapters CLAIM against what the bank SHOWS."""
        import re
        claimed = 0
        for course in COURSES:
            for ref in services.chapters_for(course.slug):
                raw = (DOCS_ROOT / course.folder / ref.filename).read_text()
                section = services._section_body(raw, 'Interview Questions')
                if section:
                    claimed += len(re.findall(
                        r'\*\*(?:Junior|Mid|Senior|Staff)\b', section))
        self.assertEqual(services.interview_questions()['total'], claimed,
                         'questions written in chapters but not shown on the '
                         'interview page — check the bullet format')

    def test_every_question_has_a_question_and_an_answer(self):
        """A truncated answer is worse than no answer: it looks complete."""
        for group in services.interview_questions()['groups']:
            for q in group['questions']:
                self.assertTrue(q['question'].strip(), f'{q["chapter"].slug}')
                self.assertTrue(q['answer'].strip(),
                                f'{q["chapter"].slug}: "{q["question"][:60]}"'
                                ' has no answer')

    def test_every_chapter_has_the_why_interviewers_ask_block(self):
        """VISION §6 item 15 asks for THREE things per question: the levelled
        Q+A, plus why the interviewer asks, plus the common wrong answer. The
        Q+A half shipped everywhere long before the other half, and the status
        table said "contract complete" while 63 of 69 chapters were missing it.
        This pins the second half so the same overstatement cannot recur.
        """
        missing, malformed = [], []
        for course in COURSES:
            for ref in services.chapters_for(course.slug):
                if ref.filename in EXEMPT:
                    continue
                raw = (DOCS_ROOT / course.folder / ref.filename).read_text()
                if 'Why interviewers ask these' not in raw:
                    missing.append(f'{course.slug}/{ref.filename}')
                    continue
                block = raw.split(
                    '### Why interviewers ask these')[1].split('\n# ')[0]
                # header row + separator + 3-4 data rows
                rows = [ln for ln in block.splitlines()
                        if ln.startswith('| ') and '---' not in ln]
                data = rows[1:]
                if not 3 <= len(data) <= 4:
                    malformed.append(
                        f'{course.slug}/{ref.filename}: {len(data)} rows')
                if 'killer follow-up' not in block:
                    malformed.append(
                        f'{course.slug}/{ref.filename}: no killer follow-up')
                for row in data:
                    # 3 cells => exactly 4 pipes; a raw newline or stray pipe
                    # inside a cell silently breaks the rendered table
                    if row.count('|') != 4:
                        malformed.append(
                            f'{course.slug}/{ref.filename}: bad cells {row[:50]}')
        self.assertEqual(missing, [], f'chapters with no why-they-ask: {missing}')
        self.assertEqual(malformed, [], f'malformed blocks: {malformed}')

    def test_a_wrapped_answer_is_not_truncated(self):
        """Answers are wrapped over several lines in the .md; the parser must
        read the whole bullet, not just its first line."""
        items = services._level_items(
            '- **Mid:** Why? — because of one reason,\n'
            '  and a second reason.\n'
            '- **Senior:** Next? — later.\n')
        self.assertEqual(len(items), 2)
        self.assertIn('second reason', items[0][1])
        self.assertNotIn('Next?', items[0][1])   # must stop at the next bullet

    def test_further_reading_is_a_toc_section_in_both_courses(self):
        """It is the last section of every chapter; at H2 it was unreachable."""
        for slug, chapter in (('sql', '14-indexes'),
                              ('deployment', '12-caddy')):
            page = services.render_chapter(slug, chapter)
            titles = [s['title'] for s in page.sections]
            self.assertTrue(any(t.startswith('Further Reading') for t in titles),
                            f'{slug}/{chapter} TOC: {titles}')


class LearningAccessControlTests(TestCase):
    """Owner ruling 2026-08-02: `/learn/` is governed by ONE Access-Control row.

    Workers are factory staff — they have no use for SQL/deployment courses, and
    the owner wants to hand the link to peers (later: paying students) without
    exposing the factory. So the `student` role reads courses and nothing else.

    The subtle part these tests exist for: `can_access_url_name()` returns **True
    for any url_name with no rule**, and only `learning:index` carries one. A
    sidebar-only gate would hide the menu link and still serve
    `/learn/sql/14-indexes/` to anyone who typed it. Hence
    `_LearningAccessMixin` on every learning view — and hence
    `test_a_blocked_role_cannot_reach_a_chapter_by_typing_the_url`, which is the
    test that would have caught that hole.
    """

    @classmethod
    def setUpTestData(cls):
        from accounts.models import Role
        cls.roles = {r.code: r for r in Role.objects.all()}

    def _as(self, role_code):
        user = User.objects.create_user(email=f'acl-{role_code}@test', password='x')
        if role_code:
            user.role = self.roles[role_code]
            user.save(update_fields=['role'])
        self.client.force_login(user)
        return user

    # ── the switch itself ────────────────────────────────────────────────────
    def test_the_access_control_row_exists_and_is_seeded_to_student(self):
        """If this row goes missing, `/learn/` silently reverts to ungated —
        visible to every worker again."""
        from accounts.models import SidebarItemRule
        rule = SidebarItemRule.objects.filter(url_name='learning:index').first()
        self.assertIsNotNone(rule, 'the learning Access-Control row is missing')
        self.assertEqual(rule.section, 'Main')
        self.assertEqual(rule.label, 'Learn')
        self.assertIn('student', {r.code for r in rule.allowed_roles.all()})

    def test_student_role_holds_no_business_permissions(self):
        """A student must be able to read courses and touch nothing else."""
        self.assertEqual(self.roles['student'].permissions.count(), 0)
        self.assertTrue(self.roles['student'].is_system,
                        'system role → cannot be deleted out from under students')

    # ── who gets in ──────────────────────────────────────────────────────────
    def test_student_can_read_the_courses(self):
        self._as('student')
        for url in ('/learn/', '/learn/sql/', '/learn/sql/14-indexes/',
                    '/learn/interview/'):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_super_admin_always_gets_in_even_though_unlisted(self):
        """Deliberately NOT in allowed_roles — the service layer bypasses, so an
        admin can never lock themselves out of a page they administer."""
        from accounts.models import SidebarItemRule
        rule = SidebarItemRule.objects.get(url_name='learning:index')
        self.assertNotIn('super_admin', {r.code for r in rule.allowed_roles.all()})
        self._as('super_admin')
        self.assertEqual(self.client.get('/learn/').status_code, 200)

    # ── who is kept out ──────────────────────────────────────────────────────
    def test_worker_cannot_reach_the_courses(self):
        """302 → the project's standard "no access" answer: a message plus a
        redirect to a dashboard the user CAN reach (SidebarAccessMiddleware)."""
        self._as('worker')
        resp = self.client.get('/learn/')
        self.assertEqual(resp.status_code, 302)
        self.assertNotIn('/learn/', resp.url)

    def test_a_blocked_role_cannot_reach_a_chapter_by_typing_the_url(self):
        """THE hole this design closes. A sidebar-only gate leaves every chapter,
        the interview bank and the revision pages reachable by direct URL."""
        self._as('worker')
        for url in ('/learn/sql/14-indexes/', '/learn/deployment/28-backups/',
                    '/learn/interview/', '/learn/revise/mistakes/',
                    '/learn/search/?q=lock', '/learn/sql/'):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302,
                             f'{url} is reachable by a blocked role')
            # and it must not bounce them back into /learn/ (redirect loop)
            self.assertNotIn('/learn/', resp.url, url)

    def test_a_blocked_role_cannot_write_progress_either(self):
        """The POST endpoints must share the gate — otherwise they leak which
        chapters exist to a role that cannot read them."""
        self._as('worker')
        for url in ('/learn/sql/14-indexes/complete/',
                    '/learn/sql/14-indexes/bookmark/',
                    '/learn/sql/14-indexes/beat/'):
            self.assertEqual(self.client.post(url).status_code, 302, url)
        # an AJAX caller gets a clean 403 instead — a redirect would corrupt fetch()
        resp = self.client.post('/learn/sql/14-indexes/beat/',
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 403)

    def test_a_role_less_user_is_kept_out(self):
        self._as(None)
        self.assertEqual(self.client.get('/learn/').status_code, 302)

    def test_ticking_a_role_in_the_access_control_page_grants_the_courses(self):
        """The owner's actual workflow: tick a role on the Sidebar Access page and
        that role gets the courses — no code change, no deploy.

        Pins the whole loop (form POST → service → M2M → gate), not just the
        seeded state. Without this, the seeded row could be right while the UI
        that edits it is broken, and the owner would tick `manager` and see
        nothing happen.
        """
        from accounts.models import SidebarItemRule
        from accounts.services.permission_service import can_access_url_name

        learn = SidebarItemRule.objects.get(url_name='learning:index')
        manager = User.objects.create_user(email='tick-mgr@test', password='x')
        manager.role = self.roles['manager']
        manager.save(update_fields=['role'])
        self.assertFalse(can_access_url_name(manager, 'learning:index'),
                         'manager should start without course access')

        # The page posts EVERY rule's checkboxes at once — a rule absent from the
        # POST is CLEARED (sidebar_service.save_sidebar_rules docstring), so build
        # the full payload the way the real form does.
        self._as('super_admin')
        data = {}
        for rule in SidebarItemRule.objects.all():
            role_ids = [str(r.id) for r in rule.allowed_roles.all()]
            if rule.id == learn.id:
                role_ids.append(str(self.roles['manager'].id))
            data[f'roles_{rule.id}'] = role_ids
            data[f'skills_{rule.id}'] = [str(s.id) for s in rule.allowed_skills.all()]
        resp = self.client.post(reverse('inventory:sidebar-access'), data)
        self.assertIn(resp.status_code, (200, 302))

        self.assertTrue(can_access_url_name(manager, 'learning:index'),
                        'ticking manager in Access Control did not grant access')
        self.client.force_login(manager)
        self.assertEqual(
            self.client.get('/learn/sql/14-indexes/').status_code, 200,
            'manager was granted the menu item but still cannot open a chapter')

    def test_menu_link_and_url_access_never_disagree(self):
        """Rule 6: hiding the menu item must also block the URL. If these two ever
        diverge, someone sees a link that 404s — or worse, reaches a page whose
        link was hidden from them."""
        from accounts.services.permission_service import (
            build_menu_for, can_access_url_name,
        )
        for code in ('super_admin', 'manager', 'worker', 'accountant', 'student'):
            user = User.objects.create_user(email=f'agree-{code}@test', password='x')
            user.role = self.roles[code]
            user.save(update_fields=['role'])
            in_menu = 'learning:index' in {
                i['url_name'] for s in build_menu_for(user) for i in s['items']}
            can_open = can_access_url_name(user, 'learning:index')
            self.assertEqual(in_menu, can_open,
                             f'{code}: menu says {in_menu}, URL gate says {can_open}')


class SearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _learner('search@test')

    def test_finds_a_term_and_ranks_by_hit_count(self):
        r = services.search('index')
        self.assertGreater(r['total'], 5)
        hits = [x['hits'] for x in r['results']]
        self.assertEqual(hits, sorted(hits, reverse=True), 'must rank by hits')

    def test_snippet_marks_the_term_and_escapes_html(self):
        r = services.search('advisory lock')
        snippet = str(r['results'][0]['snippet'])
        self.assertIn('<mark>', snippet)
        # A chapter containing "<table>" text must never inject a real tag.
        r2 = services.search('SELECT')
        for item in r2['results']:
            self.assertNotIn('<script', str(item['snippet']).lower())

    def test_short_and_empty_queries_are_handled(self):
        self.assertTrue(services.search('a')['too_short'])
        self.assertFalse(services.search('')['too_short'])
        self.assertEqual(services.search('')['results'], [])

    def test_nonsense_query_returns_nothing_gracefully(self):
        r = services.search('zzzqqqxxnotarealterm')
        self.assertEqual(r['total'], 0)
        self.assertEqual(r['results'], [])

    def test_search_page_renders_and_requires_login(self):
        self.assertEqual(self.client.get(reverse('learning:search')).status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('learning:search')).status_code, 200)
        resp = self.client.get(reverse('learning:search'), {'q': 'deadlock'})
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(resp.context['total'], 0)

    def test_reload_clears_every_cache(self):
        """If a cache survives reload_courses(), editing a .md would not show up
        on one of the generated pages — a silent staleness bug."""
        services.search('index'); services.harvest_section('Cheat Sheet')
        services.chapters_for('sql'); services.interview_questions()
        services.reload_courses()
        for fn in (services._corpus, services.harvest_section,
                   services.chapters_for, services.interview_questions):
            self.assertEqual(fn.cache_info().currsize, 0, fn.__name__)


class DashboardAndTimeTests(TestCase):
    """The follow-up requirement: a personalised, isolated student layer.

    Key design pin: the dashboard is DERIVED from LessonProgress, so it cannot
    drift from it. Only time-spent and explicit marks are stored.
    """

    @classmethod
    def setUpTestData(cls):
        cls.a = _learner('dash-a@test')
        cls.b = _learner('dash-b@test')

    def test_dashboard_is_empty_for_a_new_learner(self):
        from learning import progress_service
        d = progress_service.dashboard(self.a)
        self.assertEqual(d['active'], [])
        self.assertEqual(d['completed'], [])
        self.assertIsNone(d['recommended'])

    def test_reading_time_accumulates_and_is_clamped(self):
        from learning.models import LessonProgress
        self.client.force_login(self.a)
        self.client.get(reverse('learning:chapter', args=['sql', '07-joins']))
        url = reverse('learning:heartbeat', args=['sql', '07-joins'])
        self.assertEqual(self.client.post(url, {'s': '30', 'p': '40'}).status_code, 204)
        self.client.post(url, {'s': '99999', 'p': '80'})     # abuse attempt
        row = LessonProgress.objects.get(user=self.a, chapter_slug='07-joins')
        self.assertEqual(row.seconds_spent, 150, '30 + clamped 120')
        self.assertEqual(row.scroll_percent, 80)

    def test_scroll_depth_never_goes_backwards(self):
        from learning.models import LessonProgress
        self.client.force_login(self.a)
        self.client.get(reverse('learning:chapter', args=['sql', '07-joins']))
        url = reverse('learning:heartbeat', args=['sql', '07-joins'])
        self.client.post(url, {'s': '5', 'p': '90'})
        self.client.post(url, {'s': '5', 'p': '10'})   # scrolled back up
        row = LessonProgress.objects.get(user=self.a, chapter_slug='07-joins')
        self.assertEqual(row.scroll_percent, 90, 'furthest point is kept')

    def test_heartbeat_on_an_unopened_chapter_creates_nothing(self):
        from learning.models import LessonProgress
        self.client.force_login(self.a)
        self.client.post(reverse('learning:heartbeat', args=['sql', '09-subqueries-and-ctes']),
                         {'s': '30'})
        self.assertFalse(LessonProgress.objects.filter(
            user=self.a, chapter_slug='09-subqueries-and-ctes').exists())

    def test_three_states_are_distinguishable(self):
        from learning import progress_service
        self.client.force_login(self.a)
        self.client.get(reverse('learning:chapter', args=['sql', '05-select-basics']))
        self.client.post(reverse('learning:toggle-complete', args=['sql', '07-joins']),
                         {'done': '1'})
        states = progress_service.chapter_states(self.a, 'sql')
        self.assertEqual(states['07-joins'], 'done')
        self.assertEqual(states['05-select-basics'], 'reading')
        self.assertNotIn('04-null', states, 'never opened = absent = "new"')

    def test_active_completed_and_time_appear_on_the_dashboard(self):
        from learning import progress_service
        self.client.force_login(self.a)
        self.client.get(reverse('learning:chapter', args=['sql', '07-joins']))
        self.client.post(reverse('learning:heartbeat', args=['sql', '07-joins']), {'s': '60'})
        self.client.post(reverse('learning:toggle-complete', args=['sql', '07-joins']),
                         {'done': '1'})
        d = progress_service.dashboard(self.a)
        self.assertEqual(len(d['active']), 1)
        self.assertEqual(d['active'][0]['course'].slug, 'sql')
        self.assertEqual(d['active'][0]['remaining'], d['active'][0]['progress']['total'] - 1)
        self.assertEqual(d['stats']['learning_days'], 1)
        self.assertEqual(d['stats']['time_spent'], '1m')
        self.assertEqual(len(d['week']), 7)
        self.assertEqual(len(d['recent']), 1)

    def test_recommended_next_is_the_next_unfinished_chapter(self):
        from learning import progress_service
        self.client.force_login(self.a)
        refs = services.chapters_for('sql')
        self.client.post(reverse('learning:toggle-complete', args=['sql', refs[0].slug]),
                         {'done': '1'})
        rec = progress_service.recommended_next(self.a)
        self.assertEqual(rec['chapter'].slug, refs[1].slug)

    def test_dashboard_is_isolated_between_users(self):
        from learning import progress_service
        self.client.force_login(self.a)
        self.client.get(reverse('learning:chapter', args=['sql', '07-joins']))
        self.client.post(reverse('learning:heartbeat', args=['sql', '07-joins']), {'s': '60'})
        self.assertEqual(progress_service.dashboard(self.b)['stats']['seconds_spent'], 0)
        self.assertEqual(progress_service.dashboard(self.b)['recent'], [])

    def test_index_page_renders_the_dashboard(self):
        self.client.force_login(self.a)
        self.client.get(reverse('learning:chapter', args=['sql', '07-joins']))
        resp = self.client.get(reverse('learning:index'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('dash', resp.context)
        self.assertContains(resp, 'learning days')
