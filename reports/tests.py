from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from applicants.tests import create_complete_applicant
from risk_engine.models import RiskAssessment, Recommendation
from .views import _render_pdf


class ReportWorkflowTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='report-owner')
        self.other = get_user_model().objects.create_user(username='report-other')
        self.applicant = create_complete_applicant(self.owner)
        self.older = RiskAssessment.objects.create(
            applicant=self.applicant, risk_score=Decimal('20'), risk_category='LOW',
            confidence=Decimal('0.7'), model_version='historical-version',
        )
        self.latest = RiskAssessment.objects.create(
            applicant=self.applicant, risk_score=Decimal('80'), risk_category='HIGH',
            confidence=Decimal('0.8'), model_version='latest-version',
        )
        Recommendation.objects.create(assessment=self.older, category='Test', message='Historical recommendation')
        self.client.force_login(self.owner)

    def test_api_pdf_uses_requested_historical_assessment(self):
        with patch('risk_engine.api._render_pdf', return_value=b'%PDF-test') as renderer:
            response = self.client.get(reverse('api_report_pdf', args=[self.older.pk]))
        self.assertEqual(response.status_code, 200)
        text = renderer.call_args.args[0]
        self.assertIn('historical-version', text)
        self.assertIn('Historical recommendation', text)
        self.assertNotIn('latest-version', text)
        self.assertIn('ACADEMIC DEMONSTRATION', text)

    def test_web_and_api_generate_actual_pdf_bytes(self):
        for url in [reverse('reports:underwriting_pdf', args=[self.applicant.pk]),
                    reverse('api_report_pdf', args=[self.older.pk])]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertTrue(response.content.startswith(b'%PDF-'))
            self.assertGreater(len(response.content), 1000)

    def test_pdf_treats_text_as_text_not_markup(self):
        self.assertTrue(_render_pdf('Research <unclosed & notes\n' + 'Long report ' * 200, '').startswith(b'%PDF-'))

    def test_other_underwriter_cannot_read_reports(self):
        self.client.force_login(self.other)
        for url in [reverse('reports:underwriting', args=[self.applicant.pk]),
                    reverse('reports:underwriting_pdf', args=[self.applicant.pk]),
                    reverse('api_report_pdf', args=[self.older.pk])]:
            self.assertEqual(self.client.get(url).status_code, 404)
