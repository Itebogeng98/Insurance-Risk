"""Read-only native Kaggle inference, separate from applicant assessments."""

import hashlib
import json
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
from django.conf import settings


def bundle_directory():
    return settings.BASE_DIR / 'risk_engine' / 'ml_models' / 'kaggle_native'


def model_evidence():
    root = bundle_directory()
    if not (root / 'model.joblib').is_file() or not (root / 'evaluation.json').is_file():
        return None
    return json.loads((root / 'evaluation.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def load_bundle(checksum):
    path = bundle_directory() / 'model.joblib'
    if hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
        raise ValueError('Kaggle model artifact does not match its build evidence.')
    bundle = joblib.load(path)
    if bundle.get('input_contract') != 'prudential-native-v1':
        raise ValueError('Unsupported Kaggle input contract.')
    return bundle


def predict_native(uploaded, evidence):
    if uploaded is None or not uploaded.name.lower().endswith('.csv'):
        raise ValueError('Choose a native Prudential CSV file.')
    if uploaded.size > 2 * 1024 * 1024:
        raise ValueError('Upload at most 2 MB and 100 records per request.')
    frame = pd.read_csv(uploaded, dtype=str, nrows=101)
    if not 1 <= len(frame) <= 100:
        raise ValueError('Provide between 1 and 100 native Kaggle records.')
    bundle = load_bundle(evidence['artifact_sha256'])
    columns = bundle['feature_columns']
    missing = set(columns) - set(frame)
    extra = set(frame) - set(columns) - {'Id', 'Response'}
    if missing or extra:
        raise ValueError('CSV columns must match the native Kaggle predictors. Id and Response are optional and ignored.')
    predictors = frame[columns].copy()
    nominal = set(bundle['nominal_columns'])
    for column in columns:
        if column not in nominal:
            predictors[column] = pd.to_numeric(predictors[column], errors='raise')
            if np.isinf(predictors[column].to_numpy(dtype=float)).any():
                raise ValueError(f'{column} cannot contain infinity.')
        else:
            predictors[column] = predictors[column].where(predictors[column].notna(), np.nan)
    model = bundle['pipeline']
    probabilities = model.predict_proba(predictors)
    return [
        {'row': index + 1, 'category': str(model.classes_[values.argmax()]),
         'probability': float(values.max()),
         'high': float(values[list(model.classes_).index('HIGH')]),
         'medium': float(values[list(model.classes_).index('MEDIUM')]),
         'low': float(values[list(model.classes_).index('LOW')])}
        for index, values in enumerate(probabilities)
    ]
