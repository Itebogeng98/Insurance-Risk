"""Shared feature extraction used identically at training time and prediction time."""

from __future__ import annotations

import pandas as pd

from .risk_rules import compute_age, compute_bmi

RAW_NUMERIC_COLUMNS = [
    'monthly_income',
    'years_employed',
    'years_licensed',
    'number_of_accidents',
    'number_of_claims',
    'traffic_violations',
    'monthly_expenses',
    'monthly_savings',
    'total_debt',
    'credit_score',
    'exercise_days_per_week',
]
NUMERIC_FEATURES = ['age', 'bmi'] + RAW_NUMERIC_COLUMNS
BOOLEAN_FEATURES = [
    'smoker',
    'has_chronic_illness',
    'has_family_history_of_illness',
    'has_vehicle_insurance',
]
CATEGORICAL_FEATURES = ['gender', 'alcohol_consumption', 'occupation_risk_level', 'employment_status']

FEATURE_COLUMNS = NUMERIC_FEATURES + BOOLEAN_FEATURES + CATEGORICAL_FEATURES


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    features = pd.DataFrame(index=df.index)
    if 'observation_date' in df:
        features['age'] = df.apply(lambda row: compute_age(row['date_of_birth'], row['observation_date']), axis=1)
    else:
        features['age'] = df['date_of_birth'].apply(compute_age)
    features['bmi'] = df.apply(lambda row: compute_bmi(row['height_cm'], row['weight_kg']), axis=1)
    for column in RAW_NUMERIC_COLUMNS:
        features[column] = df[column]
    for column in BOOLEAN_FEATURES:
        features[column] = df[column].astype(int)
    for column in CATEGORICAL_FEATURES:
        features[column] = df[column]
    return features[FEATURE_COLUMNS]
