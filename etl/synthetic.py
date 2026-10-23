"""Synthetic applicant data generation for local development and risk_engine training."""

from __future__ import annotations

import datetime

import numpy as np
import pandas as pd
from faker import Faker

ALCOHOL_CHOICES = ['NONE', 'OCCASIONAL', 'MODERATE', 'HEAVY']
ALCOHOL_WEIGHTS = [0.40, 0.35, 0.20, 0.05]

OCCUPATION_RISK_CHOICES = ['LOW', 'MEDIUM', 'HIGH']
OCCUPATION_RISK_WEIGHTS = [0.60, 0.30, 0.10]

EMPLOYMENT_STATUS_CHOICES = ['EMPLOYED', 'SELF_EMPLOYED', 'UNEMPLOYED', 'RETIRED']
EMPLOYMENT_STATUS_WEIGHTS = [0.70, 0.15, 0.05, 0.10]

GENDER_CHOICES = ['M', 'F', 'O']
GENDER_WEIGHTS = [0.48, 0.48, 0.04]


def _generate_ages(rng: np.random.Generator, n: int) -> np.ndarray:
    return rng.integers(18, 76, size=n)


def _generate_income(rng: np.random.Generator, employment_status: np.ndarray) -> np.ndarray:
    base = rng.lognormal(mean=8.2, sigma=0.4, size=len(employment_status))
    income = np.where(employment_status == 'UNEMPLOYED', rng.uniform(0, 500, len(employment_status)), base)
    income = np.where(employment_status == 'RETIRED', rng.uniform(800, 2500, len(employment_status)), income)
    return np.round(income, 2)


def generate_synthetic_applicants(n: int, seed: int | None = None) -> pd.DataFrame:
    """Generate a DataFrame of applicant-shaped records for local import checks and model training."""
    rng = np.random.default_rng(seed)
    faker = Faker()
    if seed is not None:
        Faker.seed(seed)

    ages = _generate_ages(rng, n)
    today = datetime.date.today()
    dates_of_birth = [today.replace(year=today.year - int(age)) for age in ages]

    gender = rng.choice(GENDER_CHOICES, size=n, p=GENDER_WEIGHTS)
    height_cm = np.clip(rng.normal(170, 10, n), 140, 210).round(1)
    weight_kg = np.clip(rng.normal(75, 15, n), 40, 150).round(1)
    systolic = np.clip(rng.normal(122, 14, n), 90, 180).round().astype(int)
    diastolic = np.clip(rng.normal(78, 9, n), 55, 115).round().astype(int)
    diastolic = np.minimum(diastolic, systolic - 10)

    has_chronic_illness = rng.random(n) < 0.15
    has_family_history = rng.random(n) < 0.25
    smoker = rng.random(n) < 0.20
    alcohol_consumption = rng.choice(ALCOHOL_CHOICES, size=n, p=ALCOHOL_WEIGHTS)
    exercise_days_per_week = np.clip(rng.poisson(2.5, n), 0, 7)

    occupation_risk_level = rng.choice(OCCUPATION_RISK_CHOICES, size=n, p=OCCUPATION_RISK_WEIGHTS)
    employment_status = rng.choice(EMPLOYMENT_STATUS_CHOICES, size=n, p=EMPLOYMENT_STATUS_WEIGHTS)
    monthly_income = _generate_income(rng, employment_status)
    max_years_employed = np.maximum(ages - 18, 0)
    years_employed = np.round(rng.uniform(0, 1, n) * np.minimum(max_years_employed, 40), 1)

    has_vehicle_insurance = rng.random(n) < 0.70
    max_years_licensed = np.maximum(ages - 17, 0)
    years_licensed = np.round(rng.uniform(0, 1, n) * max_years_licensed).astype(int)
    number_of_accidents = rng.poisson(years_licensed * 0.03 + 0.05)
    number_of_claims = np.minimum(number_of_accidents, rng.poisson(years_licensed * 0.02 + 0.03))
    traffic_violations = rng.poisson(0.2, n)

    expense_ratio = np.clip(rng.normal(0.65, 0.15, n), 0.2, 1.1)
    monthly_expenses = np.round(monthly_income * expense_ratio, 2)
    monthly_savings = np.round(np.maximum(monthly_income - monthly_expenses, 0), 2)
    total_debt = np.round(rng.lognormal(mean=7.5, sigma=1.0, size=n) * (monthly_income > 0), 2)
    credit_score = np.clip(rng.normal(650, 80, n), 300, 850).round().astype(int)

    rows = {
        'first_name': [faker.first_name() for _ in range(n)],
        'last_name': [faker.last_name() for _ in range(n)],
        'date_of_birth': dates_of_birth,
        'gender': gender,
        'national_id': [faker.unique.numerify('#############') for _ in range(n)],
        'email': [faker.unique.email() for _ in range(n)],
        'phone_number': [faker.numerify('+27 8# ### ####') for _ in range(n)],
        'address': [faker.address().replace('\n', ', ') for _ in range(n)],
        'consent_given': [True for _ in range(n)],
        'height_cm': height_cm,
        'weight_kg': weight_kg,
        'blood_pressure': [f'{sys}/{dia}' for sys, dia in zip(systolic, diastolic, strict=False)],
        'has_chronic_illness': has_chronic_illness,
        'chronic_illness_details': [
            faker.sentence() if flag else '' for flag in has_chronic_illness
        ],
        'has_family_history_of_illness': has_family_history,
        'family_history_details': [
            faker.sentence() if flag else '' for flag in has_family_history
        ],
        'current_medications': [
            faker.word() if flag else '' for flag in has_chronic_illness
        ],
        'past_surgeries': ['' for _ in range(n)],
        'smoker': smoker,
        'alcohol_consumption': alcohol_consumption,
        'exercise_days_per_week': exercise_days_per_week,
        'occupation': [faker.job() for _ in range(n)],
        'occupation_risk_level': occupation_risk_level,
        'employment_status': employment_status,
        'employer_name': [
            faker.company() if status in ('EMPLOYED', 'SELF_EMPLOYED') else ''
            for status in employment_status
        ],
        'monthly_income': monthly_income,
        'years_employed': years_employed,
        'has_vehicle_insurance': has_vehicle_insurance,
        'years_licensed': years_licensed,
        'number_of_accidents': number_of_accidents,
        'number_of_claims': number_of_claims,
        'traffic_violations': traffic_violations,
        'previous_insurer': [
            faker.company() if flag else '' for flag in has_vehicle_insurance
        ],
        'monthly_expenses': monthly_expenses,
        'monthly_savings': monthly_savings,
        'total_debt': total_debt,
        'credit_score': credit_score,
    }
    return pd.DataFrame(rows)
