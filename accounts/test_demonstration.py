import io
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import AuditLog
from applicants.models import Applicant
from applicants.tests import create_complete_applicant
from risk_engine.models import RiskAssessment, TrainingDataset
from risk_engine.scoring import _load_model


def form_payload(form):
    payload = {}
    for field in form:
        value = field.value()
        if value is True:
            payload[field.html_name] = 'on'
        elif value is not False:
            payload[field.html_name] = '' if value is None else str(value)
    return payload


class DemonstrationJourneyTests(TestCase):
    def test_three_role_journey_with_real_scoring_and_export(self):
        applicant_client, staff_client, admin_client = Client(), Client(), Client()
        response = applicant_client.post(reverse('accounts:register'), {
            'username': 'demo-applicant', 'email': 'demo@example.com', 'role': 'CUSTOMER',
            'password1': 'DemoTest-Only-932!', 'password2': 'DemoTest-Only-932!',
        })
        self.assertEqual(response.status_code, 302)
        applicant_user = get_user_model().objects.get(username='demo-applicant')
        underwriter = get_user_model().objects.create_user(username='demo-underwriter', password='test-password')
        underwriter.profile.role = 'CUSTOMER'
        underwriter.profile.save()
        admin = get_user_model().objects.create_superuser('demo-admin', 'admin@example.com', 'test-password')
        admin_client.force_login(admin)
        response = admin_client.post(reverse('admin:accounts_userprofile_change', args=[underwriter.profile.pk]), {
            'user': underwriter.pk, 'role': 'UNDERWRITER', '_save': 'Save',
        })
        self.assertEqual(response.status_code, 302)
        underwriter.profile.refresh_from_db()
        self.assertEqual(underwriter.profile.role, 'UNDERWRITER')
        staff_client.force_login(underwriter)
        # The complete six-step wizard save is covered separately in applicants.tests.
        response = staff_client.post(reverse('applicants:create') + '?step=1', {})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Applicant.objects.exists())
        applicant = create_complete_applicant(
            underwriter, national_id='9001015009087', has_vehicle_insurance=False,
        )
        detail = reverse('applicants:detail', args=[applicant.pk])
        self.assertEqual(applicant_client.get(detail).status_code, 404)
        change_url = reverse('admin:applicants_applicant_change', args=[applicant.pk])
        response = admin_client.get(change_url)
        payload = form_payload(response.context['adminform'].form)
        for inline in response.context['inline_admin_formsets']:
            payload.update(form_payload(inline.formset.management_form))
            for form in inline.formset.forms:
                payload.update(form_payload(form))
        payload.update({'account': applicant_user.pk, '_save': 'Save'})
        response = admin_client.post(change_url, payload)
        self.assertEqual(response.status_code, 302, response.context['adminform'].form.errors if response.status_code == 200 else '')
        self.assertEqual(applicant_client.get(detail).status_code, 200)

        with tempfile.TemporaryDirectory() as directory, override_settings(MODEL_DIR=Path(directory)):
            try:
                call_command('train_risk_model', rows=200, no_kaggle=True, activate=True, stdout=io.StringIO())
                response = staff_client.post(reverse('risk_engine:assess', args=[applicant.pk]))
                self.assertEqual(response.status_code, 302)
                assessment = RiskAssessment.objects.get(applicant=applicant)
                self.assertTrue(assessment.feature_contributions.exists())
                self.assertContains(applicant_client.get(detail), 'Academic demonstration')
                self.assertNotContains(applicant_client.get(detail), 'Run Risk Assessment')
                applicant_client.post(reverse('risk_engine:assess', args=[applicant.pk]))
                self.assertEqual(RiskAssessment.objects.count(), 1)
                for client in (applicant_client, staff_client, admin_client):
                    self.assertEqual(client.get(reverse('reports:underwriting', args=[applicant.pk])).status_code, 200)
                    pdf = client.get(reverse('reports:underwriting_pdf', args=[applicant.pk]))
                    self.assertTrue(pdf.content.startswith(b'%PDF-'))
            finally:
                _load_model.cache_clear()

        models_url = reverse('risk_engine:model_management')
        self.assertEqual(applicant_client.get(models_url).status_code, 302)
        self.assertEqual(staff_client.get(models_url).status_code, 302)
        self.assertEqual(admin_client.get(models_url).status_code, 200)
        response = admin_client.post(models_url, {'action': 'upload', 'dataset': SimpleUploadedFile('invalid.csv', b'bad\n1\n')}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TrainingDataset.objects.exists())
        self.assertTrue(AuditLog.objects.filter(action='RISK_ASSESSMENT').exists())
