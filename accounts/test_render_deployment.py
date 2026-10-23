import io
import os
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import OperationalError
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from accounts.models import UserProfile
from risk_engine.model_versions import activate_model_version
from risk_engine.models import ModelVersion, TrainingDataset
from risk_engine.training import queue_training


class RenderDeploymentTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            'site-admin', 'admin@example.test', 'Strong-admin-pass-982!',
        )

    def test_health_checks_database_without_authentication(self):
        response = self.client.get('/healthz/', secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})
        self.assertEqual(response.cookies, {})

    def test_health_does_not_disclose_database_errors(self):
        with patch('config.health.connection.cursor', side_effect=OperationalError('secret host')):
            response = self.client.get('/healthz/', secure=True)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b'secret', response.content)

    @override_settings(TRAINING_ENABLED=False, MODEL_ACTIVATION_ENABLED=False)
    def test_disabled_training_blocks_every_entry_point(self):
        with self.assertRaisesMessage(ValidationError, 'unavailable'):
            queue_training(None, self.admin)
        self.client.force_login(self.admin)
        response = self.client.post('/api/v1/datasets', {}, secure=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn('unavailable', response.json()['errors'][0])
        self.client.post(reverse('risk_engine:model_management'), {'action': 'upload'}, secure=True)
        self.assertFalse(TrainingDataset.objects.exists())
        page = self.client.get(reverse('risk_engine:model_management'), secure=True)
        self.assertContains(page, 'training are unavailable')
        self.assertNotContains(page, 'name="dataset"')
        request = RequestFactory().get('/admin/')
        request.user = self.admin
        registered = admin.site._registry[TrainingDataset]
        self.assertFalse(registered.has_add_permission(request))
        self.assertFalse(registered.has_change_permission(request))
        with self.assertRaisesMessage(ValueError, 'unavailable'):
            activate_model_version(ModelVersion())

    def bootstrap(self, **env):
        with patch.dict(os.environ, env, clear=True):
            call_command('bootstrap_render_admin', stdout=io.StringIO())

    def test_bootstrap_is_optional(self):
        self.bootstrap()
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_bootstrap_creates_admin_once_without_resetting_password(self):
        env = {
            'BOOTSTRAP_ADMIN_USERNAME': 'initial-admin',
            'BOOTSTRAP_ADMIN_EMAIL': 'initial@example.test',
            'BOOTSTRAP_ADMIN_PASSWORD': 'Unique-host-password-397!',
        }
        self.bootstrap(**env)
        user = get_user_model().objects.get(username='initial-admin')
        self.assertTrue(user.is_superuser and user.is_staff)
        self.assertEqual(user.profile.role, UserProfile.Role.ADMINISTRATOR)
        self.assertTrue(user.check_password(env['BOOTSTRAP_ADMIN_PASSWORD']))
        self.bootstrap(**{**env, 'BOOTSTRAP_ADMIN_PASSWORD': 'Changed-password-397!'})
        user.refresh_from_db()
        self.assertTrue(user.check_password(env['BOOTSTRAP_ADMIN_PASSWORD']))

    def test_bootstrap_cannot_promote_an_existing_account(self):
        user = get_user_model().objects.create_user('existing')
        with self.assertRaisesMessage(CommandError, 'non-superuser'):
            self.bootstrap(BOOTSTRAP_ADMIN_USERNAME='existing')
        user.refresh_from_db()
        self.assertFalse(user.is_superuser)

    def test_bootstrap_rejects_weak_password_without_creating_user(self):
        with self.assertRaises(CommandError):
            self.bootstrap(
                BOOTSTRAP_ADMIN_USERNAME='weak-admin',
                BOOTSTRAP_ADMIN_EMAIL='admin@example.test',
                BOOTSTRAP_ADMIN_PASSWORD='123',
            )
        self.assertFalse(get_user_model().objects.filter(username='weak-admin').exists())
