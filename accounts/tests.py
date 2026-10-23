from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import UserProfile


class HomeRoutingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='home-user',
            password='pass12345',
        )

    def test_logged_out_home_shows_landing_page(self):
        response = self.client.get(reverse('landing'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Assure Risk')
        self.assertContains(response, 'Life insurance risk assessment without scattered spreadsheets')
        self.assertContains(response, 'Open Workspace')

    def test_public_legal_pages_load(self):
        for route_name, expected in (
            ('accounts:privacy', 'Privacy Policy'),
            ('accounts:terms', 'Terms of Use'),
            ('accounts:paia', 'PAIA'),
        ):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected)

    def test_logged_in_home_redirects_to_dashboard(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('landing'))

        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('accounts:dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response['Location'])

    def test_dashboard_loads_for_authenticated_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('accounts:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Total applicants')


class ProfileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='profile-user',
            password='pass12345',
            email='old@example.com',
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response['Location'])

    def test_user_can_view_profile(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('accounts:profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Profile')
        self.assertContains(response, 'old@example.com')

    def test_user_can_update_profile(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('accounts:profile'),
            {
                'first_name': 'Mc',
                'last_name': 'Makwela',
                'email': 'new@example.com',
            },
        )

        self.assertRedirects(response, reverse('accounts:profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Mc')
        self.assertEqual(self.user.last_name, 'Makwela')
        self.assertEqual(self.user.email, 'new@example.com')


class RegistrationTests(TestCase):
    def test_registration_page_shows_public_role_choices_only(self):
        response = self.client.get(reverse('accounts:register'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Applicant')
        self.assertNotContains(response, '<option value="UNDERWRITER"')
        self.assertNotContains(response, 'Administrator')

    def test_user_can_register_as_applicant(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'username': 'applicant-user',
                'email': 'applicant@example.com',
                'role': UserProfile.Role.CUSTOMER,
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )

        self.assertRedirects(response, reverse('accounts:dashboard'))
        user = get_user_model().objects.get(username='applicant-user')
        self.assertEqual(user.profile.role, UserProfile.Role.CUSTOMER)
        self.assertEqual(user.profile.get_role_display(), 'Applicant')

    def test_user_cannot_self_register_as_administrator_role(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'username': 'administrator-user',
                'email': 'administrator@example.com',
                'role': UserProfile.Role.ADMINISTRATOR,
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(username='administrator-user').exists())
        self.assertContains(response, 'Select a valid choice')
