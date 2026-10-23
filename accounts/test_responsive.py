"""Opt-in browser checks using an isolated test database, never live applicants.

Run with RUN_BROWSER_TESTS=1 and --settings=config.test_settings.
Requires Playwright and its Chromium browser installed locally.
"""

import os
from pathlib import Path
from unittest import skipUnless

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client, override_settings
from django.urls import reverse

from accounts.models import UserProfile
from applicants.tests import create_complete_applicant
from applicants.views import APPLICANT_WIZARD_SESSION_KEY, APPLICANT_WIZARD_STEPS
from risk_engine.models import FeatureContribution, ModelVersion, RiskAssessment


@skipUnless(os.environ.get('RUN_BROWSER_TESTS') == '1', 'Opt-in Playwright layout checks')
@override_settings(DEBUG=True, SECURE_SSL_REDIRECT=False, SESSION_COOKIE_SECURE=False,
                   CSRF_COOKIE_SECURE=False, ALLOWED_HOSTS=['localhost', 'testserver'])
class ResponsiveBrowserTests(StaticLiveServerTestCase):
    def test_pages_and_navigation_across_viewports(self):
        from playwright.sync_api import expect, sync_playwright

        User = get_user_model()
        admin = User.objects.create_superuser('responsive-admin', 'admin@example.test', 'test-only-password')
        underwriter = User.objects.create_user('underwriter-' + 'longname' * 8)
        applicant_user = User.objects.create_user('responsive-applicant')
        applicant_user.profile.role = UserProfile.Role.CUSTOMER
        applicant_user.profile.save()
        applicant = create_complete_applicant(
            underwriter, first_name='Alexandra', last_name='Longsurname' * 5,
            email='longcontactaddress' * 3 + '@example.test', address='Longaddress' * 30,
        )
        applicant.account = applicant_user
        applicant.save()
        for number in range(2):
            assessment = RiskAssessment.objects.create(
                applicant=applicant, risk_score=42, risk_category='MEDIUM', confidence='.72',
                model_version='test-layout-version-' + 'longidentifier' * 5,
            )
            FeatureContribution.objects.create(
                assessment=assessment, rank=1, feature='test',
                label='Long factor label for responsive inspection', contribution=5,
            )
        ModelVersion.objects.create(version_tag='layout-only-' + 'version' * 8, artifact_path='test-only.joblib')

        output = Path(settings.BASE_DIR) / 'artifacts' / 'responsive'
        output.mkdir(parents=True, exist_ok=True)
        errors = []
        checked = 0
        sessions = {}
        for user in (admin, underwriter, applicant_user):
            self.client = Client()
            self.client.force_login(user)
            session = self.client.session
            session[APPLICANT_WIZARD_SESSION_KEY] = {
                step['key']: {} for step in APPLICANT_WIZARD_STEPS
            }
            session.save()
            sessions[user.pk] = session.session_key
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            for role, user in [('public', None), ('administrator', admin),
                               ('underwriter', underwriter), ('applicant', applicant_user)]:
                context = browser.new_context()
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                if user:
                    context.add_cookies([{
                        'name': settings.SESSION_COOKIE_NAME, 'value': sessions[user.pk],
                        'url': self.live_server_url,
                    }])
                    paths = [reverse('accounts:dashboard'), reverse('applicants:list'),
                             reverse('applicants:detail', args=[applicant.pk]),
                             reverse('reports:underwriting', args=[applicant.pk]),
                             reverse('accounts:profile'), reverse('accounts:password_change')]
                    if role != 'applicant':
                        paths += [reverse('applicants:create') + f'?step={n}' for n in range(1, 7)]
                    if role == 'administrator':
                        paths += [reverse('risk_engine:model_management')]
                else:
                    paths = ['/', reverse('accounts:login'), reverse('accounts:register'),
                             reverse('accounts:privacy'), reverse('accounts:terms'), reverse('accounts:paia')]

                for width, height in [(320, 568), (390, 844), (768, 1024), (844, 390),
                                      (1024, 768), (1280, 800), (1440, 900)]:
                    page.set_viewport_size({'width': width, 'height': height})
                    for index, path in enumerate(paths):
                        with self.subTest(role=role, width=width, path=path):
                            response = page.goto(self.live_server_url + path)
                            self.assertEqual(response.status, 200)
                            page.wait_for_function("getComputedStyle(document.body).getPropertyValue('--bs-body-font-size').trim() === '1rem'")
                            page.evaluate('document.fonts.ready')
                            sizes = page.evaluate('''() => ({
                                viewport: document.documentElement.clientWidth,
                                page: document.documentElement.scrollWidth,
                                body: document.body.scrollWidth
                            })''')
                            if max(sizes['page'], sizes['body']) > sizes['viewport'] + 1:
                                page.screenshot(path=str(output / f'overflow-{role}-{index}-{width}.png'), full_page=True)
                                sizes['elements'] = page.locator('body *').evaluate_all('''nodes => nodes.filter(node => {
                                    const r = node.getBoundingClientRect();
                                    return r.width && r.right > innerWidth + 1 && !node.closest('.offcanvas');
                                }).map(node => [node.tagName, node.className]).slice(0, 20)''')
                            self.assertLessEqual(max(sizes['page'], sizes['body']), sizes['viewport'] + 1, sizes)
                            clipped = page.locator('.card-body, .metric-tile, .wizard-sidebar, .page-heading, .profile-meta').evaluate_all('''nodes => nodes.filter(
                                node => node.clientWidth && node.scrollWidth > node.clientWidth + 1
                            ).map(node => node.className)''')
                            self.assertEqual(clipped, [], f'Clipped containers: {clipped}')
                            scrollable = page.locator('.table-responsive').evaluate_all('''nodes => nodes.every(node => {
                                if (node.scrollWidth <= node.clientWidth) return true;
                                node.scrollLeft = 20;
                                const moved = node.scrollLeft > 0;
                                node.scrollLeft = 0;
                                return moved && node.tabIndex === 0;
                            })''')
                            self.assertTrue(scrollable, 'Wide tables must remain scrollable and keyboard accessible')
                            if width in (390, 1440) and (role in ('public', 'administrator') or index == 0):
                                page.screenshot(path=str(output / f'{role}-{index}-{width}.png'), full_page=True)
                            checked += 1

                    if user and width < 1200:
                        page.get_by_role('button', name='Open navigation').click()
                        drawer = page.locator('#mobileSidebar')
                        page.wait_for_function("document.querySelector('#mobileSidebar').classList.contains('show')")
                        expect(drawer.locator(f'a[href="{reverse("accounts:profile")}"]')).to_be_visible()
                        self.assertEqual(drawer.locator(f'a[href="{reverse("applicants:create")}"]').count(), int(role != 'applicant'))
                        page.keyboard.press('Escape')
                        page.wait_for_function("!document.querySelector('#mobileSidebar').classList.contains('show')")
                        page.get_by_role('button', name='Account menu').click()
                        self.assertTrue(page.get_by_role('button', name='Logout').is_visible())
                        page.keyboard.press('Escape')
                    elif not user and width < 1200:
                        page.goto(self.live_server_url + '/')
                        page.get_by_role('button', name='Toggle navigation').click()
                        expect(page.locator('#publicNavigation')).to_be_visible()
                        page.locator('#publicNavigation a[href="/#services"]').click()
                        expect(page.locator('#publicNavigation')).to_be_hidden()
                context.close()
            self.assertEqual(errors, [])
            print(f'Responsive checks completed: {checked} page/viewport combinations; screenshots in {output}')
            browser.close()
