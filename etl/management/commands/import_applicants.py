import pandas as pd
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import IntegrityError, transaction

from applicants.models import (
    Applicant,
    LifestyleHabits,
    MedicalHistory,
    Salary,
    SpendingBehaviour,
    VehicleInsuranceHistory,
)

BOOLEAN_COLUMNS = [
    'has_chronic_illness',
    'has_family_history_of_illness',
    'smoker',
    'has_vehicle_insurance',
    'consent_given',
]

REQUIRED_COLUMNS = [
    'first_name', 'last_name', 'date_of_birth', 'gender', 'national_id',
    'email', 'phone_number', 'address', 'height_cm', 'weight_kg',
    'smoker', 'alcohol_consumption', 'exercise_days_per_week', 'occupation',
    'occupation_risk_level', 'employment_status', 'monthly_income',
    'years_employed', 'has_vehicle_insurance', 'years_licensed',
    'number_of_accidents', 'number_of_claims', 'traffic_violations',
    'monthly_expenses', 'monthly_savings', 'total_debt',
]


def _load_and_clean(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_columns:
        raise CommandError(f'CSV is missing required columns: {", ".join(missing_columns)}')

    df['date_of_birth'] = pd.to_datetime(df['date_of_birth']).dt.date
    if 'consent_given' not in df.columns:
        df['consent_given'] = True
    if 'blood_pressure' not in df.columns:
        df['blood_pressure'] = '120/80'
    for column in BOOLEAN_COLUMNS:
        df[column] = (
            df[column]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({'true': True, 'false': False, '1': True, '0': False, 'yes': True, 'no': False})
        )
    df = df.fillna({
        'chronic_illness_details': '',
        'family_history_details': '',
        'current_medications': '',
        'past_surgeries': '',
        'employer_name': '',
        'previous_insurer': '',
    })
    return df


class Command(BaseCommand):
    help = 'Bulk import validated applicant records from a CSV using the project applicant schema.'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('csv_path')
        parser.add_argument('--created-by', required=True, help='Username to attribute the import to')

    def handle(self, *args, **options) -> None:
        User = get_user_model()
        try:
            created_by = User.objects.get(username=options['created_by'])
        except User.DoesNotExist as exc:
            raise CommandError(f'No user named "{options["created_by"]}"') from exc

        df = _load_and_clean(options['csv_path'])

        created_count = 0
        skipped_count = 0
        error_count = 0

        for index, row in df.iterrows():
            if Applicant.objects.filter(national_id=row['national_id']).exists():
                skipped_count += 1
                continue

            try:
                with transaction.atomic():
                    applicant = Applicant.objects.create(
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        date_of_birth=row['date_of_birth'],
                        gender=row['gender'],
                        national_id=row['national_id'],
                        email=row['email'],
                        phone_number=row['phone_number'],
                        address=row['address'],
                        consent_given=row['consent_given'],
                        created_by=created_by,
                    )
                    applicant.full_clean()
                    applicant.save()
                    medical = MedicalHistory(
                        applicant=applicant,
                        height_cm=row['height_cm'],
                        weight_kg=row['weight_kg'],
                        blood_pressure=row.get('blood_pressure', '120/80'),
                        has_chronic_illness=row['has_chronic_illness'],
                        chronic_illness_details=row.get('chronic_illness_details', ''),
                        has_family_history_of_illness=row['has_family_history_of_illness'],
                        family_history_details=row.get('family_history_details', ''),
                        current_medications=row.get('current_medications', ''),
                        past_surgeries=row.get('past_surgeries', ''),
                    )
                    medical.full_clean()
                    medical.save()
                    lifestyle = LifestyleHabits(
                        applicant=applicant,
                        smoker=row['smoker'],
                        alcohol_consumption=row['alcohol_consumption'],
                        exercise_days_per_week=row['exercise_days_per_week'],
                        occupation=row['occupation'],
                        occupation_risk_level=row['occupation_risk_level'],
                    )
                    lifestyle.full_clean()
                    lifestyle.save()
                    salary = Salary(
                        applicant=applicant,
                        employment_status=row['employment_status'],
                        employer_name=row.get('employer_name', ''),
                        monthly_income=row['monthly_income'],
                        years_employed=row['years_employed'],
                    )
                    salary.full_clean()
                    salary.save()
                    vehicle = VehicleInsuranceHistory(
                        applicant=applicant,
                        has_vehicle_insurance=row['has_vehicle_insurance'],
                        years_licensed=row['years_licensed'],
                        number_of_accidents=row['number_of_accidents'],
                        number_of_claims=row['number_of_claims'],
                        traffic_violations=row['traffic_violations'],
                        previous_insurer=row.get('previous_insurer', ''),
                    )
                    vehicle.full_clean()
                    vehicle.save()
                    spending = SpendingBehaviour(
                        applicant=applicant,
                        monthly_expenses=row['monthly_expenses'],
                        monthly_savings=row['monthly_savings'],
                        total_debt=row['total_debt'],
                        credit_score=row.get('credit_score'),
                    )
                    spending.full_clean()
                    spending.save()
                created_count += 1
            except (IntegrityError, ValueError, KeyError, ValidationError) as exc:
                error_count += 1
                self.stderr.write(f'Row {index}: {exc}')

        self.stdout.write(self.style.SUCCESS(
            f'Imported {created_count} applicants. Skipped {skipped_count} duplicates. '
            f'{error_count} rows failed.'
        ))
