import datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from risk_engine.models import RiskAssessment
from risk_engine.recommendations import build_lifestyle_recommendations
from accounts.models import UserProfile

from .models import (
    Applicant,
    LifestyleHabits,
    MedicalHistory,
    Salary,
    SpendingBehaviour,
    VehicleInsuranceHistory,
)
from .forms import (
    ApplicantForm,
    MedicalHistoryForm,
    SalaryForm,
    SpendingBehaviourForm,
    VehicleInsuranceHistoryForm,
)


def create_complete_applicant(created_by, **overrides):
    applicant = Applicant.objects.create(
        first_name=overrides.get('first_name', 'Test'),
        last_name=overrides.get('last_name', 'Applicant'),
        date_of_birth=overrides.get('date_of_birth', datetime.date(1985, 1, 1)),
        gender=overrides.get('gender', Applicant.Gender.MALE),
        national_id=overrides.get('national_id', f'ID{Applicant.objects.count() + 1:04d}'),
        email=overrides.get('email', 'test@example.com'),
        phone_number=overrides.get('phone_number', '0123456789'),
        address=overrides.get('address', '1 Test Street'),
        consent_given=overrides.get('consent_given', True),
        created_by=created_by,
    )
    MedicalHistory.objects.create(
        applicant=applicant,
        height_cm=Decimal(overrides.get('height_cm', '170.0')),
        weight_kg=Decimal(overrides.get('weight_kg', '90.0')),
        blood_pressure=overrides.get('blood_pressure', '120/80'),
        has_chronic_illness=overrides.get('has_chronic_illness', False),
        has_family_history_of_illness=overrides.get('has_family_history_of_illness', False),
    )
    LifestyleHabits.objects.create(
        applicant=applicant,
        smoker=overrides.get('smoker', False),
        alcohol_consumption=overrides.get(
            'alcohol_consumption',
            LifestyleHabits.AlcoholConsumption.NONE,
        ),
        exercise_days_per_week=overrides.get('exercise_days_per_week', 3),
        occupation='Office worker',
        occupation_risk_level=overrides.get(
            'occupation_risk_level',
            LifestyleHabits.OccupationRiskLevel.LOW,
        ),
    )
    Salary.objects.create(
        applicant=applicant,
        employment_status=Salary.EmploymentStatus.EMPLOYED,
        employer_name='Example Ltd',
        monthly_income=Decimal(overrides.get('monthly_income', '20000.00')),
        years_employed=Decimal('5.0'),
    )
    VehicleInsuranceHistory.objects.create(
        applicant=applicant,
        has_vehicle_insurance=overrides.get('has_vehicle_insurance', True),
        years_licensed=10,
        number_of_accidents=overrides.get('number_of_accidents', 0),
        number_of_claims=0,
        traffic_violations=overrides.get('traffic_violations', 0),
    )
    SpendingBehaviour.objects.create(
        applicant=applicant,
        monthly_expenses=Decimal(overrides.get('monthly_expenses', '12000.00')),
        monthly_savings=Decimal(overrides.get('monthly_savings', '3000.00')),
        total_debt=Decimal(overrides.get('total_debt', '10000.00')),
        credit_score=overrides.get('credit_score', 700),
    )
    return applicant


class ApplicantAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='owner', password='pass12345')
        self.other = User.objects.create_user(username='other', password='pass12345')
        self.staff = User.objects.create_user(
            username='staff',
            password='pass12345',
            is_staff=True,
        )
        self.owner_applicant = create_complete_applicant(
            self.owner,
            first_name='Owner',
            national_id='OWNER001',
            email='owner@example.com',
        )
        self.other_applicant = create_complete_applicant(
            self.other,
            first_name='Other',
            national_id='OTHER001',
            email='other@example.com',
        )

    def test_normal_user_only_sees_own_applicants(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('applicants:list'))

        self.assertContains(response, 'OWNER001')
        self.assertNotContains(response, 'OTHER001')

    def test_normal_user_cannot_view_other_applicant_detail(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('applicants:detail', args=[self.other_applicant.pk]))

        self.assertEqual(response.status_code, 404)

    def test_staff_can_view_all_applicants(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('applicants:list'))

        self.assertContains(response, 'OWNER001')
        self.assertContains(response, 'OTHER001')

    def test_detail_includes_recommendations(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('applicants:detail', args=[self.owner_applicant.pk]))

        self.assertContains(response, 'Lifestyle Improvement Recommendations')

    def test_applicant_role_only_sees_explicitly_linked_records(self):
        applicant_user = get_user_model().objects.create_user(
            username='applicant-role',
            password='pass12345',
            email='owner@example.com',
        )
        applicant_user.profile.role = UserProfile.Role.CUSTOMER
        applicant_user.profile.save(update_fields=['role'])

        self.owner_applicant.account = applicant_user
        self.owner_applicant.save(update_fields=['account'])

        self.client.force_login(applicant_user)
        response = self.client.get(reverse('applicants:list'))

        self.assertContains(response, 'OWNER001')
        self.assertNotContains(response, 'OTHER001')
        self.assertNotContains(response, 'New Applicant')

    def test_applicant_role_cannot_create_applicant_profiles(self):
        applicant_user = get_user_model().objects.create_user(
            username='blocked-applicant',
            password='pass12345',
            email='owner@example.com',
        )
        applicant_user.profile.role = UserProfile.Role.CUSTOMER
        applicant_user.profile.save(update_fields=['role'])

        self.client.force_login(applicant_user)
        response = self.client.get(reverse('applicants:create'))

        self.assertRedirects(response, reverse('applicants:list'))


class ApplicantCreateWizardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='wizard-user',
            password='pass12345',
        )
        self.client.force_login(self.user)

    def test_applicant_create_wizard_saves_complete_profile(self):
        step_posts = [
            {
                'applicant-first_name': 'Wizard',
                'applicant-last_name': 'Applicant',
                'applicant-date_of_birth': '1990-01-01',
                'applicant-gender': Applicant.Gender.FEMALE,
                'applicant-national_id': '9001015009087',
                'applicant-email': 'wizard@example.com',
                'applicant-phone_number': '0123456789',
                'applicant-address': '10 Wizard Street',
                'applicant-consent_given': 'on',
            },
            {
                'medical-height_cm': '168.0',
                'medical-weight_kg': '70.0',
                'medical-blood_pressure': '120/80',
                'medical-chronic_illness_details': '',
                'medical-family_history_details': '',
                'medical-current_medications': '',
                'medical-past_surgeries': '',
            },
            {
                'lifestyle-alcohol_consumption': LifestyleHabits.AlcoholConsumption.OCCASIONAL,
                'lifestyle-exercise_days_per_week': '3',
                'lifestyle-occupation': 'Analyst',
                'lifestyle-occupation_risk_level': LifestyleHabits.OccupationRiskLevel.LOW,
            },
            {
                'salary-employment_status': Salary.EmploymentStatus.EMPLOYED,
                'salary-employer_name': 'Assure Risk',
                'salary-monthly_income': '25000.00',
                'salary-years_employed': '4.0',
            },
            {
                'vehicle-has_vehicle_insurance': 'on',
                'vehicle-years_licensed': '8',
                'vehicle-number_of_accidents': '0',
                'vehicle-number_of_claims': '0',
                'vehicle-traffic_violations': '0',
                'vehicle-previous_insurer': 'Example Insurer',
            },
            {
                'spending-monthly_expenses': '12000.00',
                'spending-monthly_savings': '5000.00',
                'spending-total_debt': '10000.00',
                'spending-credit_score': '720',
            },
        ]

        for index, post_data in enumerate(step_posts, start=1):
            response = self.client.post(f'{reverse("applicants:create")}?step={index}', post_data)

        applicant = Applicant.objects.get(national_id='9001015009087')
        self.assertRedirects(response, reverse('applicants:detail', args=[applicant.pk]))
        self.assertEqual(applicant.created_by, self.user)
        self.assertTrue(hasattr(applicant, 'medical_history'))
        self.assertTrue(hasattr(applicant, 'lifestyle_habits'))
        self.assertTrue(hasattr(applicant, 'salary'))
        self.assertTrue(hasattr(applicant, 'vehicle_insurance_history'))
        self.assertTrue(hasattr(applicant, 'spending_behaviour'))

    def test_wizard_prevents_skipping_required_previous_steps(self):
        response = self.client.get(f'{reverse("applicants:create")}?step=3')

        self.assertRedirects(response, f'{reverse("applicants:create")}?step=1')


class ApplicantFormValidationTests(TestCase):
    def _form_data(self, **overrides):
        data = {
            'first_name': 'Date',
            'last_name': 'Tester',
            'date_of_birth': '1990-01-01',
            'gender': Applicant.Gender.MALE,
            'national_id': '9001015009088',
            'email': 'date@example.com',
            'phone_number': '0123456789',
            'address': '1 Date Street',
            'consent_given': 'on',
        }
        data.update(overrides)
        return data

    def test_date_of_birth_cannot_be_in_future(self):
        future = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

        form = ApplicantForm(data=self._form_data(date_of_birth=future))

        self.assertFalse(form.is_valid())
        self.assertIn('date_of_birth', form.errors)

    def test_date_of_birth_cannot_exceed_120_years(self):
        too_old = datetime.date(datetime.date.today().year - 121, 1, 1).isoformat()

        form = ApplicantForm(data=self._form_data(date_of_birth=too_old))

        self.assertFalse(form.is_valid())
        self.assertIn('date_of_birth', form.errors)

    def test_date_of_birth_widget_has_min_and_max(self):
        form = ApplicantForm()

        self.assertIn('min', form.fields['date_of_birth'].widget.attrs)
        self.assertIn('max', form.fields['date_of_birth'].widget.attrs)

    def test_national_id_requires_thirteen_digits(self):
        form = ApplicantForm(data=self._form_data(national_id='ABC123'))

        self.assertFalse(form.is_valid())
        self.assertIn('national_id', form.errors)

    def test_consent_is_required(self):
        data = self._form_data()
        data.pop('consent_given')

        form = ApplicantForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('consent_given', form.errors)

    def test_email_must_be_unique_case_insensitive(self):
        user = get_user_model().objects.create_user(username='form-owner', password='pass12345')
        create_complete_applicant(user, email='date@example.com')

        form = ApplicantForm(data=self._form_data(email='DATE@example.com'))

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class ProfileSectionFormValidationTests(TestCase):
    def test_medical_history_rejects_invalid_blood_pressure(self):
        form = MedicalHistoryForm(data={
            'height_cm': '170',
            'weight_kg': '75',
            'blood_pressure': '80/120',
            'has_chronic_illness': '',
            'chronic_illness_details': '',
            'has_family_history_of_illness': '',
            'family_history_details': '',
            'current_medications': '',
            'past_surgeries': '',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('blood_pressure', form.errors)

    def test_medical_history_requires_chronic_illness_details(self):
        form = MedicalHistoryForm(data={
            'height_cm': '170',
            'weight_kg': '75',
            'blood_pressure': '120/80',
            'has_chronic_illness': 'on',
            'chronic_illness_details': '',
            'has_family_history_of_illness': '',
            'family_history_details': '',
            'current_medications': '',
            'past_surgeries': '',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('chronic_illness_details', form.errors)

    def test_salary_requires_employer_for_employed_applicants(self):
        form = SalaryForm(data={
            'employment_status': Salary.EmploymentStatus.EMPLOYED,
            'employer_name': '',
            'monthly_income': '25000.00',
            'years_employed': '4',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('employer_name', form.errors)

    def test_vehicle_claims_cannot_exceed_accidents(self):
        form = VehicleInsuranceHistoryForm(data={
            'has_vehicle_insurance': 'on',
            'years_licensed': '8',
            'number_of_accidents': '1',
            'number_of_claims': '2',
            'traffic_violations': '0',
            'previous_insurer': 'Example Insurer',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('number_of_claims', form.errors)

    def test_vehicle_previous_insurer_required_when_insured(self):
        form = VehicleInsuranceHistoryForm(data={
            'has_vehicle_insurance': 'on',
            'years_licensed': '8',
            'number_of_accidents': '0',
            'number_of_claims': '0',
            'traffic_violations': '0',
            'previous_insurer': '',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('previous_insurer', form.errors)

    def test_spending_behaviour_rejects_invalid_credit_score(self):
        form = SpendingBehaviourForm(data={
            'monthly_expenses': '12000.00',
            'monthly_savings': '4000.00',
            'total_debt': '10000.00',
            'credit_score': '900',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('credit_score', form.errors)


class RecommendationTests(TestCase):
    def test_high_risk_habits_generate_targeted_recommendations(self):
        User = get_user_model()
        user = User.objects.create_user(username='advisor', password='pass12345')
        applicant = create_complete_applicant(
            user,
            smoker=True,
            alcohol_consumption=LifestyleHabits.AlcoholConsumption.HEAVY,
            exercise_days_per_week=1,
            height_cm='170.0',
            weight_kg='100.0',
            monthly_savings='500.00',
            total_debt='150000.00',
            credit_score=600,
        )

        recommendations = build_lifestyle_recommendations(applicant)

        self.assertTrue(any('smoking cessation' in item for item in recommendations))
        self.assertTrue(any('alcohol' in item for item in recommendations))
        self.assertTrue(any('BMI' in item for item in recommendations))
        self.assertTrue(any('savings' in item for item in recommendations))


class ReportTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='reporter', password='pass12345')
        self.other = User.objects.create_user(username='blocked', password='pass12345')
        self.applicant = create_complete_applicant(self.owner, national_id='REPORT001')
        self.other_applicant = create_complete_applicant(self.other, national_id='BLOCKED001')
        RiskAssessment.objects.create(
            applicant=self.applicant,
            risk_score=Decimal('42.0'),
            risk_category=RiskAssessment.RiskCategory.MEDIUM,
            model_version='test-model',
        )

    def test_underwriting_report_displays_assessment_and_recommendations(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('reports:underwriting', args=[self.applicant.pk]))

        self.assertContains(response, 'Underwriting Report')
        self.assertContains(response, '42.0')
        self.assertContains(response, 'Lifestyle Improvement Recommendations')

    @patch('reports.views._render_pdf', return_value=b'%PDF-test')
    def test_pdf_export_returns_pdf_response(self, render_pdf):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('reports:underwriting_pdf', args=[self.applicant.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('underwriting-report', response['Content-Disposition'])
        self.assertEqual(response.content, b'%PDF-test')
        render_pdf.assert_called_once()

    def test_report_denies_applicants_hidden_from_user(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('reports:underwriting', args=[self.other_applicant.pk]))

        self.assertEqual(response.status_code, 404)
