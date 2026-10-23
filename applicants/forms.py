import datetime
import re
from decimal import Decimal

from django import forms

from config.form_utils import add_bootstrap_classes

from .models import (
    Applicant,
    LifestyleHabits,
    MedicalHistory,
    Salary,
    SpendingBehaviour,
    VehicleInsuranceHistory,
)


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)
        for field in self.fields.values():
            if field.required:
                field.widget.attrs['required'] = True


def _clean_title(value: str) -> str:
    return ' '.join(value.strip().split()).title()


class ApplicantForm(BootstrapModelForm):
    class Meta:
        model = Applicant
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender',
            'national_id', 'email', 'phone_number', 'address', 'consent_given',
        ]
        widgets = {'date_of_birth': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        today = datetime.date.today()
        self.fields['date_of_birth'].widget.attrs.update({
            'min': f'{today.year - 120}-01-01',
            'max': today.isoformat(),
            'placeholder': 'YYYY-MM-DD',
        })
        placeholders = {
            'first_name': 'e.g. Mc',
            'last_name': 'e.g. Makwela',
            'national_id': 'e.g. 8501015800088',
            'email': 'applicant@example.com',
            'phone_number': '+27 82 123 4567',
            'address': 'Street address, city, province',
        }
        for name, placeholder in placeholders.items():
            self.fields[name].widget.attrs['placeholder'] = placeholder
        self.fields['national_id'].widget.attrs.update({'maxlength': '13', 'inputmode': 'numeric'})
        self.fields['phone_number'].widget.attrs.update({'inputmode': 'tel'})
        self.fields['address'].widget.attrs.update({'rows': '3'})
        self.fields['consent_given'].help_text = (
            'Applicant consent is required before underwriting data is captured.'
        )

    def clean_consent_given(self):
        consent_given = self.cleaned_data['consent_given']
        if not consent_given:
            raise forms.ValidationError('Applicant consent must be recorded before saving.')
        return consent_given

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data['date_of_birth']
        today = datetime.date.today()
        if date_of_birth.year < 1000 or date_of_birth.year > 9999:
            raise forms.ValidationError('Enter a valid four-digit year.')
        if date_of_birth > today:
            raise forms.ValidationError('Date of birth cannot be in the future.')
        age = today.year - date_of_birth.year
        if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
            age -= 1
        if age < 18 or age > 75:
            raise forms.ValidationError('Applicant age must be between 18 and 75 years.')
        return date_of_birth

    def clean_first_name(self):
        value = _clean_title(self.cleaned_data['first_name'])
        if len(value) < 2:
            raise forms.ValidationError('First name must be at least 2 characters.')
        if not value.replace(' ', '').replace('-', '').replace("'", '').isalpha():
            raise forms.ValidationError('Use letters, spaces, hyphens or apostrophes only.')
        return value

    def clean_last_name(self):
        value = _clean_title(self.cleaned_data['last_name'])
        if len(value) < 2:
            raise forms.ValidationError('Last name must be at least 2 characters.')
        if not value.replace(' ', '').replace('-', '').replace("'", '').isalpha():
            raise forms.ValidationError('Use letters, spaces, hyphens or apostrophes only.')
        return value

    def clean_national_id(self):
        national_id = self.cleaned_data['national_id'].strip()
        if not national_id.isdigit() or len(national_id) != 13:
            raise forms.ValidationError('Identity number must contain exactly 13 numeric digits.')
        return national_id

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        existing = Applicant.objects.filter(email__iexact=email)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError('An applicant with this email address already exists.')
        return email

    def clean_phone_number(self):
        phone_number = ' '.join(self.cleaned_data['phone_number'].strip().split())
        digit_count = len(re.sub(r'\D', '', phone_number))
        if digit_count < 8 or digit_count > 19:
            raise forms.ValidationError('Enter a valid phone number with 8 to 19 digits.')
        return phone_number

    def clean_address(self):
        address = ' '.join(self.cleaned_data['address'].strip().split())
        if len(address) < 10:
            raise forms.ValidationError('Address must be specific enough for applicant records.')
        return address


class MedicalHistoryForm(BootstrapModelForm):
    class Meta:
        model = MedicalHistory
        exclude = ['applicant']

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['height_cm'].widget.attrs.update({'placeholder': 'e.g. 170', 'min': '100', 'max': '230', 'step': '0.1'})
        self.fields['weight_kg'].widget.attrs.update({'placeholder': 'e.g. 75', 'min': '35', 'max': '250', 'step': '0.1'})
        self.fields['blood_pressure'].widget.attrs['placeholder'] = 'e.g. 120/80'
        self.fields['chronic_illness_details'].widget.attrs['placeholder'] = 'Optional details'
        self.fields['family_history_details'].widget.attrs['placeholder'] = 'Optional details'
        self.fields['current_medications'].widget.attrs['placeholder'] = 'Medication names or none'
        self.fields['past_surgeries'].widget.attrs['placeholder'] = 'Surgery history or none'

    def clean(self):
        cleaned_data = super().clean()
        height_cm = cleaned_data.get('height_cm')
        weight_kg = cleaned_data.get('weight_kg')
        if height_cm and (height_cm < Decimal('100') or height_cm > Decimal('230')):
            self.add_error('height_cm', 'Height must be between 100 cm and 230 cm.')
        if weight_kg and (weight_kg < Decimal('35') or weight_kg > Decimal('250')):
            self.add_error('weight_kg', 'Weight must be between 35 kg and 250 kg.')
        if height_cm and weight_kg:
            height_m = height_cm / Decimal('100')
            bmi = weight_kg / (height_m * height_m)
            if bmi < Decimal('10') or bmi > Decimal('60'):
                raise forms.ValidationError('BMI must be between 10 and 60.')
        blood_pressure = cleaned_data.get('blood_pressure', '').strip()
        if blood_pressure:
            parts = blood_pressure.split('/')
            if len(parts) != 2 or not all(part.isdigit() for part in parts):
                self.add_error('blood_pressure', 'Blood pressure must use systolic/diastolic format, e.g. 120/80.')
            else:
                systolic, diastolic = [int(part) for part in parts]
                if systolic < 70 or systolic > 250 or diastolic < 40 or diastolic > 150:
                    self.add_error('blood_pressure', 'Blood pressure values are outside a realistic underwriting range.')
                elif diastolic >= systolic:
                    self.add_error('blood_pressure', 'Diastolic pressure must be lower than systolic pressure.')
        if cleaned_data.get('has_chronic_illness') and not cleaned_data.get('chronic_illness_details', '').strip():
            self.add_error('chronic_illness_details', 'Provide details when chronic illness is selected.')
        if cleaned_data.get('has_family_history_of_illness') and not cleaned_data.get('family_history_details', '').strip():
            self.add_error('family_history_details', 'Provide details when family history is selected.')
        return cleaned_data


class LifestyleHabitsForm(BootstrapModelForm):
    class Meta:
        model = LifestyleHabits
        exclude = ['applicant']

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['exercise_days_per_week'].widget.attrs.update({'placeholder': '0 to 7', 'min': '0', 'max': '7'})
        self.fields['occupation'].widget.attrs['placeholder'] = 'e.g. Software developer'

    def clean_occupation(self):
        occupation = ' '.join(self.cleaned_data['occupation'].strip().split()).title()
        if len(occupation) < 2:
            raise forms.ValidationError('Occupation is required.')
        return occupation


class SalaryForm(BootstrapModelForm):
    class Meta:
        model = Salary
        exclude = ['applicant']

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['employer_name'].widget.attrs['placeholder'] = 'Employer or company name'
        self.fields['monthly_income'].widget.attrs.update({'placeholder': 'Monthly income amount', 'min': '0', 'step': '0.01'})
        self.fields['years_employed'].widget.attrs.update({'placeholder': 'e.g. 3.5', 'min': '0', 'max': '60', 'step': '0.1'})

    def clean(self):
        cleaned_data = super().clean()
        employment_status = cleaned_data.get('employment_status')
        employer_name = cleaned_data.get('employer_name', '').strip()
        monthly_income = cleaned_data.get('monthly_income')
        years_employed = cleaned_data.get('years_employed')
        if employment_status in (
            Salary.EmploymentStatus.EMPLOYED,
            Salary.EmploymentStatus.SELF_EMPLOYED,
        ) and not employer_name:
            self.add_error('employer_name', 'Employer or business name is required for employed applicants.')
        if employment_status == Salary.EmploymentStatus.UNEMPLOYED and monthly_income and monthly_income > 0:
            self.add_error('monthly_income', 'Monthly income must be 0 for unemployed applicants.')
        if years_employed is not None and (years_employed < Decimal('0') or years_employed > Decimal('60')):
            self.add_error('years_employed', 'Years employed must be between 0 and 60.')
        if monthly_income is not None and monthly_income < 0:
            self.add_error('monthly_income', 'Monthly income cannot be negative.')
        cleaned_data['employer_name'] = employer_name
        return cleaned_data


class VehicleInsuranceHistoryForm(BootstrapModelForm):
    class Meta:
        model = VehicleInsuranceHistory
        exclude = ['applicant']

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['years_licensed'].widget.attrs.update({'placeholder': 'Years licensed', 'min': '0', 'max': '58'})
        self.fields['number_of_accidents'].widget.attrs.update({'placeholder': '0', 'min': '0', 'max': '50'})
        self.fields['number_of_claims'].widget.attrs.update({'placeholder': '0', 'min': '0', 'max': '50'})
        self.fields['traffic_violations'].widget.attrs.update({'placeholder': '0', 'min': '0', 'max': '100'})
        self.fields['previous_insurer'].widget.attrs['placeholder'] = 'Previous insurer if applicable'

    def clean(self):
        cleaned_data = super().clean()
        has_vehicle_insurance = cleaned_data.get('has_vehicle_insurance')
        previous_insurer = cleaned_data.get('previous_insurer', '').strip()
        number_of_accidents = cleaned_data.get('number_of_accidents') or 0
        number_of_claims = cleaned_data.get('number_of_claims') or 0
        if number_of_claims > number_of_accidents:
            self.add_error('number_of_claims', 'Claims cannot exceed recorded accidents.')
        if has_vehicle_insurance and not previous_insurer:
            self.add_error('previous_insurer', 'Previous insurer is required when vehicle insurance is selected.')
        if not has_vehicle_insurance and previous_insurer:
            self.add_error('previous_insurer', 'Leave previous insurer blank if the applicant has no vehicle insurance.')
        cleaned_data['previous_insurer'] = previous_insurer
        return cleaned_data


class SpendingBehaviourForm(BootstrapModelForm):
    class Meta:
        model = SpendingBehaviour
        exclude = ['applicant']

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['monthly_expenses'].widget.attrs.update({'placeholder': 'Monthly expenses amount', 'min': '0', 'step': '0.01'})
        self.fields['monthly_savings'].widget.attrs.update({'placeholder': 'Monthly savings amount', 'min': '0', 'step': '0.01'})
        self.fields['total_debt'].widget.attrs.update({'placeholder': 'Total outstanding debt', 'min': '0', 'step': '0.01'})
        self.fields['credit_score'].widget.attrs.update({'placeholder': '300 to 850', 'min': '300', 'max': '850'})

    def clean_credit_score(self):
        credit_score = self.cleaned_data.get('credit_score')
        if credit_score is not None and (credit_score < 300 or credit_score > 850):
            raise forms.ValidationError('Credit score must be between 300 and 850.')
        return credit_score

    def clean(self):
        cleaned_data = super().clean()
        for field_name in ('monthly_expenses', 'monthly_savings', 'total_debt'):
            value = cleaned_data.get(field_name)
            if value is not None and value < 0:
                self.add_error(field_name, 'Amount cannot be negative.')
        return cleaned_data
