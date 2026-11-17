"""Opt-in, one-time fictional application history for the final presentation."""

import datetime
import os
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import AuditLog
from applicants.models import (
    Applicant, LifestyleHabits, MedicalHistory, Salary,
    SpendingBehaviour, VehicleInsuranceHistory,
)
from applicants.permissions import is_administrator


BATCH = 'presentation-2026-11-17-v1'
COUNT = 36
START = datetime.datetime(2026, 8, 17, tzinfo=ZoneInfo('Africa/Johannesburg'))
END = datetime.datetime(2026, 11, 17, tzinfo=ZoneInfo('Africa/Johannesburg'))


def save_validated(instance):
    instance.full_clean()
    instance.save()
    return instance


class Command(BaseCommand):
    help = 'Import 36 labelled synthetic profiles only when explicitly enabled by the host operator.'

    def handle(self, *args, **options):
        enabled = os.environ.get('PRESENTATION_DATA_BATCH', '').strip()
        if not enabled:
            return
        if enabled != BATCH:
            raise CommandError('Unrecognised PRESENTATION_DATA_BATCH; no data imported.')
        username = os.environ.get('PRESENTATION_DATA_OWNER', '').strip()
        if not username:
            raise CommandError('Set PRESENTATION_DATA_OWNER to an existing administrator username.')
        if timezone.now() < END:
            raise CommandError('This batch cannot create future-dated demonstration records.')

        with transaction.atomic():
            try:
                # Serialise repeat deployments against the same owner.
                owner = get_user_model().objects.select_for_update().get(username=username)
            except get_user_model().DoesNotExist as exc:
                raise CommandError('Presentation owner does not exist; no data imported.') from exc
            if not owner.is_active or not is_administrator(owner):
                raise CommandError('Presentation owner must be an active Administrator.')
            if AuditLog.objects.filter(object_type='PresentationDataBatch', object_id=BATCH).exists():
                self.stdout.write('Presentation batch already imported; existing records left unchanged.')
                return

            identifiers = [f'000000001{i:04d}' for i in range(1, COUNT + 1)]
            if Applicant.objects.filter(national_id__in=identifiers).exists():
                raise CommandError('Demo identifier collision; no records changed. Do not delete existing data.')

            ids = []
            for index, national_id in enumerate(identifiers):
                suffix = chr(65 + index // 26) + chr(65 + index % 26)
                date = START + (END - START) * index / (COUNT - 1)
                income = Decimal(12000 + (index % 12) * 2500)
                applicant = save_validated(Applicant(
                    first_name='Demo', last_name=f'Applicant {suffix}',
                    date_of_birth=datetime.date(1975 + index % 25, 1 + index % 12, 10),
                    gender=('M', 'F', 'O')[index % 3], national_id=national_id,
                    email=f'presentation.{index + 1:02d}@example.invalid',
                    phone_number='0000000000',
                    address=(f'SYNTHETIC DEMONSTRATION ONLY | {BATCH}\n'
                             'Fictional identity, contact, consent and financial/health data.\n'
                             'Historical application date is simulated, not actual collection time.'),
                    consent_given=True, created_by=owner,
                ))
                save_validated(MedicalHistory(
                    applicant=applicant, height_cm=Decimal(160 + index % 25),
                    weight_kg=Decimal(60 + index % 40),
                    blood_pressure=('115/75', '125/80', '140/90')[index % 3],
                    has_chronic_illness=index % 4 == 0,
                    chronic_illness_details='Fictional hypertension history.' if index % 4 == 0 else '',
                ))
                save_validated(LifestyleHabits(
                    applicant=applicant, smoker=index % 5 == 0,
                    alcohol_consumption=('NONE', 'OCCASIONAL', 'MODERATE')[index % 3],
                    exercise_days_per_week=index % 6,
                    occupation=('Office worker', 'Technician', 'Construction worker')[index % 3],
                    occupation_risk_level=('LOW', 'MEDIUM', 'HIGH')[index % 3],
                ))
                save_validated(Salary(
                    applicant=applicant, employment_status='EMPLOYED',
                    employer_name='Fictional Demo Employer', monthly_income=income,
                    years_employed=Decimal(1 + index % 8),
                ))
                save_validated(VehicleInsuranceHistory(
                    applicant=applicant, has_vehicle_insurance=True,
                    previous_insurer='Fictional Demo Insurer', years_licensed=5 + index % 5,
                    number_of_accidents=index % 4, number_of_claims=index % 4,
                    traffic_violations=index % 3,
                ))
                save_validated(SpendingBehaviour(
                    applicant=applicant, monthly_expenses=income * Decimal('0.65'),
                    monthly_savings=income * Decimal('0.15'),
                    total_debt=Decimal(index % 10 * 5000), credit_score=480 + index % 12 * 25,
                ))
                # Only the new fictional application date is historical. Preserve
                # actual updated_at and audit timestamps as import-time evidence.
                Applicant.objects.filter(pk=applicant.pk).update(created_at=date)
                ids.append(str(applicant.pk))

            AuditLog.objects.create(
                user=None, action=AuditLog.Action.DATA_CHANGE,
                object_type='PresentationDataBatch', object_id=BATCH,
                detail=(f'Host operator imported {COUNT} synthetic demo profiles owned by user '
                        f'{owner.pk}. Simulated dates: 2026-08-17 to 2026-11-17. '
                        f'Applicant IDs: {", ".join(ids)}. No risk assessments generated; '
                        'consent is fictional. Audit timestamp is the actual import time.'),
            )
        self.stdout.write(self.style.SUCCESS('Imported 36 synthetic presentation applications.'))
        self.stdout.write('Remove PRESENTATION_DATA_BATCH and PRESENTATION_DATA_OWNER now.')
