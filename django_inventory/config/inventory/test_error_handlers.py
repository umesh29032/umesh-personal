"""P0-2: branded error handlers (403/404/500) + denial-path behavior.

Verifies, under DEBUG=False (the production condition the handlers fire in):
  • 404 → branded templates/404.html
  • view-mixin denial (PermissionDenied) → branded templates/403.html
  • middleware AJAX denial → clean JSON 403 (NOT an HTML page)
  • unauthenticated access → redirect to login (LoginRequired), not a 403/500
  • 500 template renders standalone with an EMPTY context (RC-7 bulletproofness)
  • handler403/404/500 are explicitly registered to the default views
"""
from django.template.loader import render_to_string
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from inventory.models import Role

import config.urls as root_urls


@override_settings(DEBUG=False)
class ErrorHandlerTests(TestCase):
    def setUp(self):
        self.worker = User.objects.create_user(email='eh-w@test', password='x')
        self.worker.role = Role.objects.get(code='worker')
        self.worker.save()

    def test_404_uses_branded_template(self):
        resp = self.client.get('/this-path-does-not-exist-xyz/')
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed(resp, '404.html')
        self.assertIn(b'Page not found', resp.content)

    def test_view_mixin_denial_uses_branded_403(self):
        # Payroll is _ManagementOnly and has NO SidebarItemRule, so the middleware
        # passes through and the view mixin raises PermissionDenied → handler403.
        self.client.force_login(self.worker)
        resp = self.client.get(reverse('expense:payroll-overview'))
        self.assertEqual(resp.status_code, 403)
        self.assertTemplateUsed(resp, '403.html')
        self.assertIn(b"don't have access", resp.content)

    def test_middleware_ajax_denial_is_json_not_html(self):
        # access-control IS a managed (SidebarItemRule) url → middleware gate.
        # An AJAX request must get a clean JSON 403, never the HTML page.
        self.client.force_login(self.worker)
        resp = self.client.get(
            reverse('inventory:access-control'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertNotIn(b'<html', resp.content)

    def test_unauthenticated_redirects_to_login(self):
        resp = self.client.get(reverse('expense:payroll-overview'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/app/', resp['Location'])

    def test_500_template_renders_standalone(self):
        # server_error renders with an EMPTY context — prove the template needs
        # nothing from the request/DB/context-processors (RC-7).
        html = render_to_string('500.html')
        self.assertIn('Something went wrong', html)
        self.assertIn('Error 500', html)

    def test_handlers_are_registered(self):
        self.assertEqual(root_urls.handler403, 'django.views.defaults.permission_denied')
        self.assertEqual(root_urls.handler404, 'django.views.defaults.page_not_found')
        self.assertEqual(root_urls.handler500, 'django.views.defaults.server_error')
