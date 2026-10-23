import datetime
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joblib
import pandas as pd
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from applicants.tests import create_complete_applicant
from risk_engine.applicant_data import APPLICANT_COLUMNS, read_applicant_csv
from risk_engine.features import build_feature_frame
from risk_engine.models import ModelVersion
from risk_engine.scoring import _applicant_to_row
from risk_engine.training import queue_training


def applicant_rows():
    # Test fixtures only; never installed in the application database.
    return pd.DataFrame([{
        'record_id': f'test-{i}', 'observation_date': '2020-01-01', 'date_of_birth': '1985-01-01',
        'height_cm': 170, 'weight_kg': 75, 'monthly_income': 20000 + i,
        'years_employed': 5, 'years_licensed': 10, 'number_of_accidents': 0,
        'number_of_claims': 0, 'traffic_violations': 0, 'monthly_expenses': 10000,
        'monthly_savings': 2000, 'total_debt': 3000, 'credit_score': '',
        'exercise_days_per_week': 3, 'smoker': False, 'has_chronic_illness': False,
        'has_family_history_of_illness': False, 'has_vehicle_insurance': True,
        'gender': 'M', 'alcohol_consumption': 'NONE', 'occupation_risk_level': 'LOW',
        'employment_status': 'EMPLOYED', 'label_source': 'HUMAN_UNDERWRITING',
        'risk_category': ['HIGH', 'MEDIUM', 'LOW'][i % 3],
    } for i in range(60)])


def csv_bytes(frame):
    return frame.to_csv(index=False).encode('utf-8')


class ApplicantTrainingDataTests(TestCase):
    def test_age_uses_observation_date_and_unknown_credit_stays_missing(self):
        frame = read_applicant_csv(io.BytesIO(csv_bytes(applicant_rows())))
        features = build_feature_frame(frame)
        self.assertTrue(features['age'].eq(35).all())
        self.assertTrue(features['credit_score'].isna().all())
        self.assertNotIn('record_id', features)
        self.assertNotIn('risk_category', features)
        self.assertNotIn('label_source', features)

    def test_bad_values_are_rejected_with_row_numbers(self):
        for column, value in [
            ('height_cm', 'nan'), ('weight_kg', 'infinity'), ('smoker', 'yes'),
            ('number_of_accidents', 0.5), ('observation_date', '2100-01-01'),
            ('date_of_birth', '2019-01-01'), ('gender', 'unknown'),
            ('monthly_savings', 999999), ('number_of_claims', 1),
            ('credit_score', 900), ('risk_category', 'OTHER'), ('label_source', 'MODEL'),
        ]:
            with self.subTest(column=column):
                frame = applicant_rows()
                frame[column] = frame[column].astype(object)
                frame.loc[0, column] = value
                with self.assertRaisesMessage(ValidationError, 'CSV row(s): 2'):
                    read_applicant_csv(io.BytesIO(csv_bytes(frame)))

    def test_duplicates_unknown_columns_and_single_class_rejected(self):
        frames = []
        duplicate_id = applicant_rows()
        duplicate_id.loc[1, 'record_id'] = duplicate_id.loc[0, 'record_id']
        frames.append(duplicate_id)
        duplicate_features = applicant_rows()
        duplicate_features.loc[1, 'monthly_income'] = duplicate_features.loc[0, 'monthly_income']
        frames.append(duplicate_features)
        extra = applicant_rows()
        extra['email'] = 'not-allowed@example.com'
        frames.append(extra)
        single_class = applicant_rows()
        single_class['risk_category'] = 'LOW'
        frames.append(single_class)
        for frame in frames:
            with self.assertRaises(ValidationError):
                read_applicant_csv(io.BytesIO(csv_bytes(frame)))

    def test_template_is_empty_and_administrator_only(self):
        user = get_user_model().objects.create_user(username='template-reader')
        self.client.force_login(user)
        url = reverse('risk_engine:applicant_training_template')
        self.assertEqual(self.client.get(url).status_code, 403)
        user.is_staff = True
        user.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        lines = response.content.decode().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].split(','), APPLICANT_COLUMNS)

    def test_worker_uses_actual_fields_and_model_accepts_live_features(self):
        user = get_user_model().objects.create_user(username='applicant-trainer')
        with tempfile.TemporaryDirectory() as directory, override_settings(
            MEDIA_ROOT=directory, MODEL_DIR=Path(directory) / 'models',
        ):
            dataset = queue_training(SimpleUploadedFile('applicants.csv', csv_bytes(applicant_rows())), user)
            with patch('risk_engine.management.commands.train_risk_model.load_prudential_applicants', side_effect=AssertionError('No Kaggle mix')):
                with patch('risk_engine.management.commands.train_risk_model.label_training_data', side_effect=AssertionError('No invented labels')):
                    call_command('process_training_jobs', once=True, stdout=io.StringIO())
            dataset.refresh_from_db()
            self.assertEqual(dataset.status, 'COMPLETE', dataset.error_message)
            version = ModelVersion.objects.get(version_tag=dataset.model_version)
            self.assertEqual(version.training_schema, 3)
            self.assertFalse(version.input_contract_verified)
            self.assertFalse(version.is_active)
            evidence = json.loads(Path(version.artifact_path).with_suffix('.json').read_text())
            self.assertEqual(evidence['source_rows'], 60)
            self.assertEqual(evidence['input_format'], 'applicant')
            applicant = create_complete_applicant(user, credit_score=None)
            live_features = build_feature_frame(pd.DataFrame([_applicant_to_row(applicant)]))
            model = joblib.load(version.artifact_path)
            self.assertEqual(model.predict_proba(live_features).shape, (1, 3))
