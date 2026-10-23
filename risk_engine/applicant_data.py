"""Validated, measured applicant records for supervised training."""
import datetime

import numpy as np
import pandas as pd
from django.core.exceptions import ValidationError

from .features import BOOLEAN_FEATURES, CATEGORICAL_FEATURES, RAW_NUMERIC_COLUMNS, build_feature_frame

APPLICANT_COLUMNS = [
    'record_id', 'observation_date', 'date_of_birth', 'height_cm', 'weight_kg',
    *RAW_NUMERIC_COLUMNS, *BOOLEAN_FEATURES, *CATEGORICAL_FEATURES,
    'label_source', 'risk_category',
]
CATEGORY_VALUES = {
    'gender': {'M', 'F', 'O'},
    'alcohol_consumption': {'NONE', 'OCCASIONAL', 'MODERATE', 'HEAVY'},
    'occupation_risk_level': {'LOW', 'MEDIUM', 'HIGH'},
    'employment_status': {'EMPLOYED', 'SELF_EMPLOYED', 'UNEMPLOYED', 'RETIRED'},
}
NUMERIC_BOUNDS = {
    'height_cm': (100, 230), 'weight_kg': (35, 250),
    'monthly_income': (0, 9999999999.99), 'monthly_expenses': (0, 9999999999.99),
    'monthly_savings': (0, 9999999999.99), 'total_debt': (0, 9999999999.99),
    'years_employed': (0, 60), 'years_licensed': (0, 58),
    'number_of_accidents': (0, 50), 'number_of_claims': (0, 50),
    'traffic_violations': (0, 100), 'exercise_days_per_week': (0, 7),
    'credit_score': (300, 850),
}
INTEGER_COLUMNS = {'years_licensed', 'number_of_accidents', 'number_of_claims',
                   'traffic_violations', 'exercise_days_per_week', 'credit_score'}


def _reject(mask, message):
    if mask.any():
        rows = ', '.join(str(int(i) + 2) for i in mask[mask].index[:5])
        raise ValidationError(f'{message} CSV row(s): {rows}.')


def read_applicant_csv(source):
    try:
        frame = pd.read_csv(source, dtype=str, keep_default_na=False)
    except (ValueError, UnicodeError) as exc:
        raise ValidationError('Upload a readable UTF-8 CSV file.') from exc
    missing = set(APPLICANT_COLUMNS) - set(frame)
    extra = set(frame) - set(APPLICANT_COLUMNS)
    if missing or extra:
        raise ValidationError(f'Applicant schema mismatch. Missing: {", ".join(sorted(missing)) or "none"}; '
                              f'unexpected: {", ".join(sorted(extra)) or "none"}.')
    if not 30 <= len(frame) <= 200000:
        raise ValidationError('Provide between 30 and 200,000 labelled applicant rows.')
    for column in frame:
        frame[column] = frame[column].str.strip()
        if column != 'credit_score':
            _reject(frame[column].eq(''), f'{column} is required.')
    _reject(frame['record_id'].duplicated(keep=False), 'record_id must be unique; use one record per person.')
    for column in ('observation_date', 'date_of_birth'):
        dates = pd.to_datetime(frame[column], format='%Y-%m-%d', errors='coerce')
        _reject(dates.isna() | ~frame[column].str.fullmatch(r'\d{4}-\d{2}-\d{2}'), f'{column} requires YYYY-MM-DD.')
        frame[column] = dates.dt.date
    _reject(frame['observation_date'] > datetime.date.today(), 'Observation date cannot be in the future.')
    for column, (minimum, maximum) in NUMERIC_BOUNDS.items():
        values = pd.to_numeric(frame[column], errors='coerce')
        optional = frame[column].eq('') if column == 'credit_score' else pd.Series(False, index=frame.index)
        invalid = (~np.isfinite(values) | ~values.between(minimum, maximum)) & ~optional
        if column in INTEGER_COLUMNS:
            invalid |= (values.mod(1).ne(0) & ~optional)
        _reject(invalid, f'{column} must be {"an integer" if column in INTEGER_COLUMNS else "numeric"} between {minimum} and {maximum}.')
        frame[column] = values
    for column in BOOLEAN_FEATURES:
        values = frame[column].str.lower().map({'true': True, 'false': False, '1': True, '0': False})
        _reject(values.isna(), f'{column} must be true, false, 1 or 0.')
        frame[column] = values.astype(bool)
    for column, values in CATEGORY_VALUES.items():
        _reject(~frame[column].isin(values), f'{column} must be one of {", ".join(sorted(values))}.')
    _reject(~frame['label_source'].eq('HUMAN_UNDERWRITING'), 'Labels must come from HUMAN_UNDERWRITING, not model predictions.')
    _reject(~frame['risk_category'].isin(['HIGH', 'MEDIUM', 'LOW']), 'risk_category must be HIGH, MEDIUM or LOW.')
    if (frame['risk_category'].value_counts().reindex(['HIGH', 'MEDIUM', 'LOW'], fill_value=0) < 5).any():
        raise ValidationError('Provide at least five independently labelled records per risk category.')
    _reject(frame['number_of_claims'] > frame['number_of_accidents'], 'Claims cannot exceed accidents.')
    _reject(frame['monthly_expenses'] > frame['monthly_income'] * 3, 'Expenses cannot exceed three times income.')
    _reject(frame['monthly_savings'] > frame['monthly_income'], 'Savings cannot exceed income.')
    _reject(frame['employment_status'].eq('UNEMPLOYED') & frame['monthly_income'].ne(0), 'Unemployed records must have zero monthly income.')
    features = build_feature_frame(frame)
    _reject(~features['age'].between(18, 75), 'Age at observation must be between 18 and 75.')
    _reject(~features['bmi'].between(10, 60), 'BMI must be between 10 and 60.')
    _reject(features.duplicated(keep=False), 'Duplicate predictor records require review before training.')
    frame['source_dataset'] = 'labelled_applicant_records'
    return frame
