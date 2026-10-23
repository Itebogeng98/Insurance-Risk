import io
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import UserProfile
from applicants.permissions import visible_applicants_for
from applicants.tests import create_complete_applicant
from etl.kaggle import load_prudential_applicants
from risk_engine.api import _make_jwt
from risk_engine.models import ModelVersion, TrainingDataset
from risk_engine.training import queue_training
from risk_engine.model_versions import activate_model_version


def prudential_csv():
    rows = []
    for index in range(60):
        rows.append({
            'Ins_Age': 0.3 + index / 200, 'Ht': 0.5, 'Wt': 0.4,
            'BMI': 0.4, 'Employment_Info_1': 0.3, 'Employment_Info_2': 2,
            'Employment_Info_6': 0.2, 'InsuredInfo_1': 1,
            'Medical_History_1': 2, 'Response': [1, 4, 8][index % 3],
        })
    return pd.DataFrame(rows).to_csv(index=False).encode()


class AccessSecurityTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='owner', password='testpassword')
        self.applicant = create_complete_applicant(self.owner)
        self.user = get_user_model().objects.create_user(username='viewer', email=self.applicant.email)
        self.user.profile.role = UserProfile.Role.CUSTOMER
        self.user.profile.save()

    def test_email_match_does_not_grant_access(self):
        self.assertFalse(visible_applicants_for(self.user).exists())
        self.applicant.account = self.user
        self.applicant.save(update_fields=['account'])
        self.user.email = 'changed@example.com'
        self.user.save()
        self.assertEqual(list(visible_applicants_for(self.user)), [self.applicant])

    def test_session_write_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(reverse('api_create_applicant'), {}, content_type='application/json').status_code, 403)

    def test_valid_bearer_does_not_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse('api_create_applicant'), {}, content_type='application/json',
                               HTTP_AUTHORIZATION='Bearer ' + _make_jwt(self.owner))
        self.assertEqual(response.status_code, 400)  # Form validation, not a CSRF rejection.

    def test_session_with_csrf_reaches_view_and_login_without_csrf_is_denied(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse('api_login'), {}, content_type='application/json').status_code, 403)
        client.get(reverse('accounts:login'))
        token = client.cookies['csrftoken'].value
        client.force_login(self.owner)
        response = client.post(reverse('api_create_applicant'), {}, content_type='application/json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 400)

    def test_inactive_token_rejected(self):
        token = _make_jwt(self.owner)
        self.owner.is_active = False
        self.owner.save()
        response = self.client.post(reverse('api_create_applicant'), {}, content_type='application/json',
                                    HTTP_AUTHORIZATION='Bearer ' + token)
        self.assertEqual(response.status_code, 401)

    def test_admin_registration_creates_no_account(self):
        response = self.client.post(reverse('api_register'), {
            'username': 'forbidden', 'email': 'new@example.com',
            'password': 'StrongPass123!', 'role': 'ADMINISTRATOR',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(get_user_model().objects.filter(username='forbidden').exists())

    def test_weak_password_and_staff_registration_rejected(self):
        for role, password in [('CUSTOMER', '123'), ('UNDERWRITER', 'StrongPass123!')]:
            response = self.client.post(reverse('api_register'), {
                'username': 'invalid', 'email': 'new@example.com', 'password': password, 'role': role,
            }, content_type='application/json')
            self.assertEqual(response.status_code, 400)
        self.assertFalse(get_user_model().objects.filter(username='invalid').exists())


class TrainingWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='trainer')

    def test_response_changes_only_label(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.csv'
            frame = pd.read_csv(io.BytesIO(prudential_csv()))
            frame.to_csv(path, index=False)
            first = load_prudential_applicants(path)
            frame['Response'] = 8
            frame.to_csv(path, index=False)
            second = load_prudential_applicants(path)
            pd.testing.assert_frame_equal(first.drop(columns='risk_category'), second.drop(columns='risk_category'))

    def test_invalid_upload_creates_no_job(self):
        with self.assertRaises(ValidationError):
            queue_training(SimpleUploadedFile('data.csv', b'bad\n1\n'), self.user)
        self.assertFalse(TrainingDataset.objects.exists())

    @override_settings(REQUIRE_VALIDATED_MODEL=True, MODEL_MIN_ACCURACY=0.85, MODEL_MIN_MACRO_F1=0.80)
    def test_production_rejects_legacy_and_underperforming_models(self):
        for schema, accuracy, f1 in [(1, 0.99, 0.99), (2, 0.608, 0.514)]:
            version = ModelVersion.objects.create(
                version_tag=f'blocked-{schema}', training_schema=schema,
                accuracy=accuracy, macro_f1=f1, input_contract_verified=True,
            )
            with self.assertRaises(ValueError):
                activate_model_version(version)
            version.refresh_from_db()
            self.assertFalse(version.is_active)

    @override_settings(REQUIRE_VALIDATED_MODEL=True, MODEL_MIN_ACCURACY=0.85, MODEL_MIN_MACRO_F1=0.80)
    def test_high_scores_do_not_override_unverified_input_mapping(self):
        version = ModelVersion.objects.create(
            version_tag='unverified-inputs', training_schema=2, accuracy=0.99, macro_f1=0.99,
        )
        with self.assertRaisesMessage(ValueError, 'training inputs'):
            activate_model_version(version)

    def test_worker_trains_uploaded_data_without_synthetic_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            with override_settings(MEDIA_ROOT=directory, MODEL_DIR=Path(directory) / 'models'):
                dataset = queue_training(SimpleUploadedFile('data.csv', prudential_csv()), self.user)
                self.assertEqual(dataset.status, 'QUEUED')
                self.assertFalse(ModelVersion.objects.exists())
                with patch('risk_engine.management.commands.train_risk_model.generate_synthetic_applicants',
                           side_effect=AssertionError('Must use uploaded rows')):
                    call_command('process_training_jobs', once=True, stdout=io.StringIO())
                dataset.refresh_from_db()
                self.assertEqual(dataset.status, 'COMPLETE', dataset.error_message)
                version = ModelVersion.objects.get(version_tag=dataset.model_version)
                self.assertEqual(version.training_schema, 2)
                self.assertFalse(version.is_active)
                self.assertTrue(Path(version.artifact_path).exists())

    def test_failed_training_preserves_active_model(self):
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            dataset = queue_training(SimpleUploadedFile('data.csv', prudential_csv()), self.user)
            active = ModelVersion.objects.create(version_tag='existing', is_active=True)
            with patch('risk_engine.management.commands.process_training_jobs.call_command', side_effect=RuntimeError('failure')):
                with self.assertLogs('risk_engine.management.commands.process_training_jobs', level='ERROR'):
                    call_command('process_training_jobs', once=True)
            dataset.refresh_from_db()
            active.refresh_from_db()
            self.assertEqual(dataset.status, 'FAILED')
            self.assertTrue(active.is_active)
