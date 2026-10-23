"""Legacy demonstration adapter; mappings are not verified for live underwriting.

See evaluation/MAPPING_AUDIT.md. Use risk_engine.evaluation for native data research.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import numpy as np
import pandas as pd

KAGGLE_TRAIN_PATH = Path(__file__).resolve().parent / 'raw_data' / 'train.csv'


def _date_of_birth_from_age(age: pd.Series) -> list[datetime.date]:
    today = datetime.date.today()
    return [today.replace(year=today.year - int(value)) for value in age.clip(18, 75)]


def _risk_category_from_response(response: pd.Series) -> pd.Series:
    # Prudential Response is ordinal from 1 to 8. Lower values represent less
    # favorable underwriting outcomes, so they are mapped to higher risk here.
    return pd.cut(
        response,
        bins=[0, 2, 5, 8],
        labels=['HIGH', 'MEDIUM', 'LOW'],
        include_lowest=True,
    ).astype(str)


def load_prudential_applicants(
    csv_path: str | Path = KAGGLE_TRAIN_PATH,
    *,
    limit: int | None = None,
    seed: int = 42,
) -> pd.DataFrame:
    """Return Kaggle rows transformed into the same shape as synthetic applicants.

    The Prudential dataset does not contain direct equivalents for every project
    field. Missing concepts such as vehicle history are filled with neutral
    defaults, while available medical, BMI, employment and insurance-history
    signals are mapped into the closest local feature.
    """
    path = Path(csv_path)
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)
    if limit is not None and limit < len(df):
        df = df.sample(n=limit, random_state=seed)
    df = df.reset_index(drop=True)

    numeric = df.select_dtypes(include=[np.number]).copy()
    med_keywords = [column for column in df.columns if column.startswith('Medical_Keyword_')]
    med_keyword_count = df[med_keywords].sum(axis=1) if med_keywords else pd.Series(0, index=df.index)

    age = (18 + df['Ins_Age'].fillna(df['Ins_Age'].median()) * 57).round().astype(int)
    height_cm = (140 + df['Ht'].fillna(df['Ht'].median()) * 80).round(1)
    weight_kg = (40 + df['Wt'].fillna(df['Wt'].median()) * 180).round(1)
    bmi = df['BMI'].fillna(df['BMI'].median())
    employment_info = df['Employment_Info_1'].fillna(df['Employment_Info_1'].median()).clip(lower=0)
    monthly_income = (1500 + employment_info * 160000 / 12).round(2)
    response = df['Response'].astype(int)

    # Unsupported financial and vehicle fields use label-independent defaults.
    spending_ratio = 0.75
    monthly_expenses = (monthly_income * spending_ratio).round(2)
    monthly_savings = (monthly_income - monthly_expenses).clip(lower=0).round(2)

    transformed = pd.DataFrame({
        'date_of_birth': _date_of_birth_from_age(age),
        'gender': np.where(df['InsuredInfo_1'].fillna(1).astype(int) % 2 == 0, 'F', 'M'),
        'height_cm': height_cm,
        'weight_kg': weight_kg,
        'has_chronic_illness': (med_keyword_count > med_keyword_count.quantile(0.75)),
        'has_family_history_of_illness': df.get('Family_Hist_1', pd.Series(1, index=df.index)).fillna(1).astype(int) > 1,
        'smoker': df.get('Medical_Keyword_15', pd.Series(0, index=df.index)).fillna(0).astype(bool),
        'alcohol_consumption': np.where(
            df['Medical_History_1'].fillna(0) > df['Medical_History_1'].quantile(0.90),
            'HEAVY',
            np.where(df['Medical_History_1'].fillna(0) > df['Medical_History_1'].quantile(0.65), 'MODERATE', 'OCCASIONAL'),
        ),
        'occupation_risk_level': np.where(
            df['Employment_Info_2'].fillna(0).astype(int) >= 10,
            'HIGH',
            np.where(df['Employment_Info_2'].fillna(0).astype(int) >= 5, 'MEDIUM', 'LOW'),
        ),
        'exercise_days_per_week': np.where(bmi > bmi.quantile(0.75), 1, np.where(bmi < bmi.quantile(0.25), 4, 3)),
        'employment_status': np.where(employment_info <= 0.001, 'UNEMPLOYED', 'EMPLOYED'),
        'monthly_income': monthly_income,
        'years_employed': (df['Employment_Info_6'].fillna(0).clip(lower=0, upper=1) * 40).round(1),
        'has_vehicle_insurance': True,
        'years_licensed': (age - 18).clip(lower=0),
        'number_of_accidents': 0,
        'number_of_claims': 0,
        'traffic_violations': 0,
        'monthly_expenses': monthly_expenses,
        'monthly_savings': monthly_savings,
        'total_debt': 0,
        'credit_score': 660,
        'risk_category': _risk_category_from_response(response),
        'source_dataset': 'kaggle_prudential',
    })

    for column in transformed.select_dtypes(include=[np.number]).columns:
        transformed[column] = transformed[column].replace([np.inf, -np.inf], np.nan).fillna(transformed[column].median())
    return transformed
