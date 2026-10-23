"""Rule-based risk labeling used to generate training labels for synthetic data.

Not used at prediction time - once risk_engine's model is trained, predictions
come from the fitted model, not these rules. Weights reflect standard
underwriting risk factors (smoking, BMI, driving history, debt-to-income, etc).
"""

from __future__ import annotations

import datetime

import numpy as np
import pandas as pd

RISK_CATEGORY_THRESHOLDS = {'LOW': 33, 'MEDIUM': 50}


def compute_age(date_of_birth: datetime.date, as_of: datetime.date | None = None) -> int:
    as_of = as_of or datetime.date.today()
    years = as_of.year - date_of_birth.year
    if (as_of.month, as_of.day) < (date_of_birth.month, date_of_birth.day):
        years -= 1
    return years


def compute_bmi(height_cm: float, weight_kg: float) -> float:
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)


def compute_raw_risk_score(df: pd.DataFrame) -> np.ndarray:
    age = df['date_of_birth'].apply(compute_age).to_numpy()
    bmi = (df['weight_kg'] / (df['height_cm'] / 100) ** 2).to_numpy()

    score = np.zeros(len(df))
    score += np.where(df['smoker'], 15, 0)
    score += np.where(bmi >= 30, 10, np.where(bmi >= 25, 5, 0))
    score += np.where(df['has_chronic_illness'], 15, 0)
    score += np.where(df['has_family_history_of_illness'], 8, 0)
    score += df['alcohol_consumption'].map(
        {'HEAVY': 10, 'MODERATE': 5, 'OCCASIONAL': 2, 'NONE': 0}
    ).to_numpy()
    score += df['occupation_risk_level'].map({'HIGH': 12, 'MEDIUM': 6, 'LOW': 0}).to_numpy()
    score += np.where(
        df['exercise_days_per_week'] <= 1, 6, np.where(df['exercise_days_per_week'] >= 5, -5, 0)
    )
    score += np.where(age >= 60, 10, np.where(age >= 45, 5, 0))
    score += np.minimum(df['number_of_accidents'].to_numpy() * 3, 12)
    score += np.minimum(df['number_of_claims'].to_numpy() * 3, 12)
    score += np.minimum(df['traffic_violations'].to_numpy() * 2, 8)
    score += np.where(df['employment_status'] == 'UNEMPLOYED', 6, 0)

    annual_income = np.maximum(df['monthly_income'].to_numpy() * 12, 1)
    debt_to_income = df['total_debt'].to_numpy() / annual_income
    score += np.where(debt_to_income > 0.5, 8, 0)

    savings_rate = df['monthly_savings'].to_numpy() / np.maximum(df['monthly_income'].to_numpy(), 1)
    score += np.where(savings_rate < 0.1, 5, 0)

    score += np.where(df['credit_score'] < 580, 8, np.where(df['credit_score'] < 670, 4, 0))

    return score


def categorize_risk_score(risk_score: float) -> str:
    if risk_score < RISK_CATEGORY_THRESHOLDS['LOW']:
        return 'LOW'
    if risk_score < RISK_CATEGORY_THRESHOLDS['MEDIUM']:
        return 'MEDIUM'
    return 'HIGH'


def label_training_data(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    raw_score = compute_raw_risk_score(df)
    noisy_score = np.clip(raw_score, 0, 100)
    labeled = df.copy()
    labeled['risk_score'] = noisy_score.round(1)
    labeled['risk_category'] = [categorize_risk_score(s) for s in noisy_score]
    return labeled
