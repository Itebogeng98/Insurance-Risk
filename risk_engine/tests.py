import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from applicants.tests import create_complete_applicant
from accounts.models import UserProfile
from risk_engine.model_versions import activate_model_version
from risk_engine.models import ModelVersion


class RiskAssessmentViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='risk-owner', password='pass12345')
        self.other = User.objects.create_user(username='risk-other', password='pass12345')
        self.staff = User.objects.create_user(
            username='risk-staff',
            password='pass12345',
            is_staff=True,
        )
        self.owner_applicant = create_complete_applicant(
            self.owner,
            national_id='RISKOWN001',
            email='risk-owner@example.com',
        )
        self.other_applicant = create_complete_applicant(
            self.other,
            national_id='RISKOTH001',
            email='risk-other@example.com',
        )

    @patch('risk_engine.views.assess_applicant')
    def test_owner_can_assess_own_applicant(self, assess_applicant):
        self.client.force_login(self.owner)

        response = self.client.post(reverse('risk_engine:assess', args=[self.owner_applicant.pk]))

        self.assertEqual(response.status_code, 302)
        assess_applicant.assert_called_once_with(self.owner_applicant)

    @patch('risk_engine.views.assess_applicant')
    def test_user_cannot_assess_other_applicant(self, assess_applicant):
        self.client.force_login(self.owner)

        response = self.client.post(reverse('risk_engine:assess', args=[self.other_applicant.pk]))

        self.assertEqual(response.status_code, 404)
        assess_applicant.assert_not_called()

    @patch('risk_engine.views.assess_applicant')
    def test_staff_can_assess_any_applicant(self, assess_applicant):
        self.client.force_login(self.staff)

        response = self.client.post(reverse('risk_engine:assess', args=[self.other_applicant.pk]))

        self.assertEqual(response.status_code, 302)
        assess_applicant.assert_called_once_with(self.other_applicant)

    @patch('risk_engine.views.assess_applicant')
    def test_applicant_role_cannot_run_assessment(self, assess_applicant):
        applicant_user = get_user_model().objects.create_user(
            username='risk-applicant',
            password='pass12345',
            email='risk-owner@example.com',
        )
        applicant_user.profile.role = UserProfile.Role.CUSTOMER
        applicant_user.profile.save(update_fields=['role'])
        self.owner_applicant.account = applicant_user
        self.owner_applicant.save(update_fields=['account'])
        self.client.force_login(applicant_user)

        response = self.client.post(reverse('risk_engine:assess', args=[self.owner_applicant.pk]))

        self.assertRedirects(response, reverse('applicants:detail', args=[self.owner_applicant.pk]))
        assess_applicant.assert_not_called()


class ModelVersionActivationTests(TestCase):
    def test_activation_copies_artifact_to_runtime_model_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            model_dir = base_dir / 'risk_engine' / 'ml_models'
            model_dir.mkdir(parents=True)
            source = model_dir / 'gb-test.joblib'
            target = model_dir / 'risk_model.joblib'
            source.write_bytes(b'new-model')
            target.write_bytes(b'old-model')

            selected = ModelVersion.objects.create(
                version_tag='gb-test',
                artifact_path='risk_engine/ml_models/gb-test.joblib',
                is_active=False,
            )
            previous = ModelVersion.objects.create(
                version_tag='gb-old',
                artifact_path='risk_engine/ml_models/gb-old.joblib',
                is_active=True,
            )

            with override_settings(BASE_DIR=base_dir, MODEL_DIR=model_dir):
                activate_model_version(selected)

            selected.refresh_from_db()
            previous.refresh_from_db()
            self.assertEqual(target.read_bytes(), b'new-model')
            self.assertTrue(selected.is_active)
            self.assertFalse(previous.is_active)
