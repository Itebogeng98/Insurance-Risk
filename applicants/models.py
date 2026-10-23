import datetime
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models


class Applicant(models.Model):
    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=Gender.choices)
    national_id = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{13}$',
                message='Identity number must contain exactly 13 numeric digits.',
            )
        ],
    )
    email = models.EmailField()
    phone_number = models.CharField(
        max_length=30,
        validators=[
            RegexValidator(
                regex=r'^\+?\d[\d\s().-]{7,18}$',
                message='Enter a valid phone number with 8 to 19 digits.',
            )
        ],
    )
    address = models.TextField()
    consent_given = models.BooleanField(default=True)
    account = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='applicant_record', limit_choices_to={'profile__role': 'CUSTOMER'},
        help_text='Assign only after verifying the account holder owns this applicant record.',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='applicants',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.first_name} {self.last_name}'

    def clean(self) -> None:
        super().clean()
        errors = {}
        today = datetime.date.today()
        if self.date_of_birth:
            age = today.year - self.date_of_birth.year
            if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
                age -= 1
            if age < 18 or age > 75:
                errors['date_of_birth'] = 'Applicant age must be between 18 and 75 years.'
        for field_name in ('first_name', 'last_name'):
            value = getattr(self, field_name, '')
            if value and not value.replace(' ', '').replace('-', '').replace("'", '').isalpha():
                errors[field_name] = 'Use letters, spaces, hyphens or apostrophes only.'
        if not self.consent_given:
            errors['consent_given'] = 'Applicant consent must be recorded before saving.'
        if errors:
            raise ValidationError(errors)


class MedicalHistory(models.Model):
    applicant = models.OneToOneField(
        Applicant, on_delete=models.CASCADE, related_name='medical_history'
    )
    height_cm = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[MinValueValidator(Decimal('100.0')), MaxValueValidator(Decimal('230.0'))],
    )
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[MinValueValidator(Decimal('35.0')), MaxValueValidator(Decimal('250.0'))],
    )
    blood_pressure = models.CharField(
        max_length=7,
        validators=[
            RegexValidator(
                regex=r'^\d{2,3}/\d{2,3}$',
                message='Blood pressure must use systolic/diastolic format, e.g. 120/80.',
            )
        ],
    )
    has_chronic_illness = models.BooleanField(default=False)
    chronic_illness_details = models.TextField(blank=True)
    has_family_history_of_illness = models.BooleanField(default=False)
    family_history_details = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    past_surgeries = models.TextField(blank=True)

    @property
    def bmi(self) -> Decimal:
        height_m = self.height_cm / Decimal('100')
        return round(self.weight_kg / (height_m * height_m), 1)

    def __str__(self) -> str:
        return f'Medical history for {self.applicant}'

    def clean(self) -> None:
        super().clean()
        errors = {}
        if self.height_cm and self.weight_kg:
            bmi = self.bmi
            if bmi < Decimal('10') or bmi > Decimal('60'):
                errors['weight_kg'] = 'Height and weight produce a BMI outside the allowed 10 to 60 range.'
        if self.blood_pressure:
            try:
                systolic, diastolic = [int(part) for part in self.blood_pressure.split('/')]
            except ValueError:
                errors['blood_pressure'] = 'Blood pressure must use systolic/diastolic format, e.g. 120/80.'
            else:
                if systolic < 70 or systolic > 250 or diastolic < 40 or diastolic > 150:
                    errors['blood_pressure'] = 'Blood pressure values are outside a realistic underwriting range.'
                if diastolic >= systolic:
                    errors['blood_pressure'] = 'Diastolic pressure must be lower than systolic pressure.'
        if self.has_chronic_illness and not self.chronic_illness_details.strip():
            errors['chronic_illness_details'] = 'Provide details when chronic illness is selected.'
        if self.has_family_history_of_illness and not self.family_history_details.strip():
            errors['family_history_details'] = 'Provide details when family history is selected.'
        if errors:
            raise ValidationError(errors)


class LifestyleHabits(models.Model):
    class AlcoholConsumption(models.TextChoices):
        NONE = 'NONE', 'None'
        OCCASIONAL = 'OCCASIONAL', 'Occasional'
        MODERATE = 'MODERATE', 'Moderate'
        HEAVY = 'HEAVY', 'Heavy'

    class OccupationRiskLevel(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'

    applicant = models.OneToOneField(
        Applicant, on_delete=models.CASCADE, related_name='lifestyle_habits'
    )
    smoker = models.BooleanField(default=False)
    alcohol_consumption = models.CharField(
        max_length=10, choices=AlcoholConsumption.choices, default=AlcoholConsumption.NONE
    )
    exercise_days_per_week = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(7)]
    )
    occupation = models.CharField(max_length=100)
    occupation_risk_level = models.CharField(
        max_length=10, choices=OccupationRiskLevel.choices, default=OccupationRiskLevel.LOW
    )

    def __str__(self) -> str:
        return f'Lifestyle habits for {self.applicant}'

    def clean(self) -> None:
        super().clean()
        if not self.occupation.strip():
            raise ValidationError({'occupation': 'Occupation is required.'})


class Salary(models.Model):
    class EmploymentStatus(models.TextChoices):
        EMPLOYED = 'EMPLOYED', 'Employed'
        SELF_EMPLOYED = 'SELF_EMPLOYED', 'Self-employed'
        UNEMPLOYED = 'UNEMPLOYED', 'Unemployed'
        RETIRED = 'RETIRED', 'Retired'

    applicant = models.OneToOneField(
        Applicant, on_delete=models.CASCADE, related_name='salary'
    )
    employment_status = models.CharField(max_length=15, choices=EmploymentStatus.choices)
    employer_name = models.CharField(max_length=150, blank=True)
    monthly_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    years_employed = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=0,
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('60.0'))],
    )

    def __str__(self) -> str:
        return f'Salary details for {self.applicant}'

    def clean(self) -> None:
        super().clean()
        errors = {}
        if self.employment_status in (
            self.EmploymentStatus.EMPLOYED,
            self.EmploymentStatus.SELF_EMPLOYED,
        ) and not self.employer_name.strip():
            errors['employer_name'] = 'Employer or business name is required for employed applicants.'
        if self.employment_status == self.EmploymentStatus.UNEMPLOYED and self.monthly_income and self.monthly_income > 0:
            errors['monthly_income'] = 'Monthly income must be 0 for unemployed applicants.'
        if errors:
            raise ValidationError(errors)


class VehicleInsuranceHistory(models.Model):
    applicant = models.OneToOneField(
        Applicant, on_delete=models.CASCADE, related_name='vehicle_insurance_history'
    )
    has_vehicle_insurance = models.BooleanField(default=False)
    years_licensed = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(58)])
    number_of_accidents = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(50)])
    number_of_claims = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(50)])
    traffic_violations = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)])
    previous_insurer = models.CharField(max_length=150, blank=True)

    def __str__(self) -> str:
        return f'Vehicle insurance history for {self.applicant}'

    def clean(self) -> None:
        super().clean()
        errors = {}
        if self.number_of_claims > self.number_of_accidents:
            errors['number_of_claims'] = 'Claims cannot exceed recorded accidents.'
        if self.has_vehicle_insurance and not self.previous_insurer.strip():
            errors['previous_insurer'] = 'Previous insurer is required when vehicle insurance is selected.'
        if not self.has_vehicle_insurance and self.previous_insurer.strip():
            errors['previous_insurer'] = 'Leave previous insurer blank if the applicant has no vehicle insurance.'
        if errors:
            raise ValidationError(errors)


class SpendingBehaviour(models.Model):
    applicant = models.OneToOneField(
        Applicant, on_delete=models.CASCADE, related_name='spending_behaviour'
    )
    monthly_expenses = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    monthly_savings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    total_debt = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    credit_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(300), MaxValueValidator(850)],
    )

    def __str__(self) -> str:
        return f'Spending behaviour for {self.applicant}'

    def clean(self) -> None:
        super().clean()
        errors = {}
        salary = None
        if self.applicant_id:
            salary = getattr(self.applicant, 'salary', None)
        if salary and self.monthly_expenses > salary.monthly_income * 3:
            errors['monthly_expenses'] = 'Monthly expenditure may not exceed salary by more than 200%.'
        if salary and self.monthly_savings > salary.monthly_income:
            errors['monthly_savings'] = 'Monthly savings cannot exceed monthly income.'
        if errors:
            raise ValidationError(errors)
