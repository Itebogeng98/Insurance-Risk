from __future__ import annotations

import datetime
import pathlib
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache

import joblib
import pandas as pd
from django.conf import settings

from applicants.models import Applicant

from .features import build_feature_frame
from .models import FeatureContribution, ModelVersion, Recommendation, RiskAssessment
from .recommendations import build_lifestyle_recommendations
from .risk_rules import RISK_CATEGORY_THRESHOLDS, categorize_risk_score, compute_age

MODEL_PATH = pathlib.Path(settings.BASE_DIR) / 'risk_engine' / 'ml_models' / 'risk_model.joblib'

REQUIRED_RELATIONS = (
    'medical_history',
    'lifestyle_habits',
    'salary',
    'vehicle_insurance_history',
    'spending_behaviour',
)


class ModelNotTrainedError(RuntimeError):
    pass


class IncompleteApplicantProfileError(ValueError):
    pass


@dataclass(frozen=True)
class RiskAssessmentResult:
    risk_score: float
    risk_category: str
    confidence: float
    top_factors: tuple[dict, ...]


def _load_model():
    model_path = _active_model_path()
    if not model_path.exists():
        raise ModelNotTrainedError(
            f'No trained model found at {model_path}. Run "manage.py train_risk_model" first.'
        )
    return _load_artifact(str(model_path), model_path.stat().st_mtime_ns)


@lru_cache(maxsize=2)
def _load_artifact(path, modified_ns):
    return joblib.load(path)


_load_model.cache_clear = _load_artifact.cache_clear


def _active_model_version() -> ModelVersion | None:
    return ModelVersion.objects.filter(is_active=True).first()


def _active_model_path() -> pathlib.Path:
    active = _active_model_version()
    from .model_versions import validate_production_model
    try:
        validate_production_model(active)
    except ValueError as exc:
        raise ModelNotTrainedError(str(exc)) from exc
    if active:
        path = pathlib.Path(active.artifact_path)
        if not path.is_absolute():
            path = pathlib.Path(settings.BASE_DIR) / path
        return path
    return MODEL_PATH


def _applicant_to_row(applicant: Applicant) -> dict:
    missing = [name for name in REQUIRED_RELATIONS if not hasattr(applicant, name)]
    if missing:
        raise IncompleteApplicantProfileError(
            f'Applicant {applicant.pk} is missing: {", ".join(missing)}'
        )

    medical = applicant.medical_history
    lifestyle = applicant.lifestyle_habits
    salary = applicant.salary
    vehicle = applicant.vehicle_insurance_history
    spending = applicant.spending_behaviour

    return {
        'date_of_birth': applicant.date_of_birth,
        'gender': applicant.gender,
        'height_cm': medical.height_cm,
        'weight_kg': medical.weight_kg,
        'has_chronic_illness': medical.has_chronic_illness,
        'has_family_history_of_illness': medical.has_family_history_of_illness,
        'smoker': lifestyle.smoker,
        'alcohol_consumption': lifestyle.alcohol_consumption,
        'occupation_risk_level': lifestyle.occupation_risk_level,
        'exercise_days_per_week': lifestyle.exercise_days_per_week,
        'employment_status': salary.employment_status,
        'monthly_income': float(salary.monthly_income),
        'years_employed': float(salary.years_employed),
        'has_vehicle_insurance': vehicle.has_vehicle_insurance,
        'years_licensed': vehicle.years_licensed,
        'number_of_accidents': vehicle.number_of_accidents,
        'number_of_claims': vehicle.number_of_claims,
        'traffic_violations': vehicle.traffic_violations,
        'monthly_expenses': float(spending.monthly_expenses),
        'monthly_savings': float(spending.monthly_savings),
        'total_debt': float(spending.total_debt),
        'credit_score': spending.credit_score if spending.credit_score is not None else float('nan'),
    }


def _risk_confidence(score: float) -> float:
    category = categorize_risk_score(score)
    low_threshold = RISK_CATEGORY_THRESHOLDS['LOW']
    high_threshold = RISK_CATEGORY_THRESHOLDS['MEDIUM']
    if category == RiskAssessment.RiskCategory.LOW:
        distance = low_threshold - score
    elif category == RiskAssessment.RiskCategory.MEDIUM:
        distance = min(score - low_threshold, high_threshold - score)
    else:
        distance = score - high_threshold
    return round(max(0.55, min(0.98, 0.55 + abs(distance) / high_threshold * 0.43)), 3)


def _factor_contributions(row: dict) -> tuple[dict, ...]:
    annual_income = max(float(row['monthly_income']) * 12, 1.0)
    debt_to_income = float(row['total_debt']) / annual_income
    savings_rate = float(row['monthly_savings']) / max(float(row['monthly_income']), 1.0)
    age = compute_age(row['date_of_birth'])

    factors = [
        ('smoker', 'Smoking status', 15 if row['smoker'] else 0),
        ('bmi', 'Body mass index', 10 if row['weight_kg'] / (row['height_cm'] / 100) ** 2 >= 30 else 5 if row['weight_kg'] / (row['height_cm'] / 100) ** 2 >= 25 else 0),
        ('has_chronic_illness', 'Chronic illness history', 15 if row['has_chronic_illness'] else 0),
        ('has_family_history_of_illness', 'Family medical history', 8 if row['has_family_history_of_illness'] else 0),
        ('alcohol_consumption', 'Alcohol consumption', {'HEAVY': 10, 'MODERATE': 5, 'OCCASIONAL': 2, 'NONE': 0}.get(row['alcohol_consumption'], 0)),
        ('occupation_risk_level', 'Occupation risk level', {'HIGH': 12, 'MEDIUM': 6, 'LOW': 0}.get(row['occupation_risk_level'], 0)),
        ('exercise_days_per_week', 'Exercise frequency', 6 if row['exercise_days_per_week'] <= 1 else -5 if row['exercise_days_per_week'] >= 5 else 0),
        ('age', 'Applicant age', 10 if age >= 60 else 5 if age >= 45 else 0),
        ('number_of_accidents', 'Driving accident history', min(row['number_of_accidents'] * 3, 12)),
        ('number_of_claims', 'Vehicle claims history', min(row['number_of_claims'] * 3, 12)),
        ('traffic_violations', 'Traffic violations', min(row['traffic_violations'] * 2, 8)),
        ('employment_status', 'Employment status', 6 if row['employment_status'] == 'UNEMPLOYED' else 0),
        ('debt_to_income', 'Debt-to-income exposure', 8 if debt_to_income > 0.5 else 0),
        ('monthly_savings', 'Savings rate', 5 if savings_rate < 0.1 else 0),
        ('credit_score', 'Credit score', 8 if row['credit_score'] < 580 else 4 if row['credit_score'] < 670 else 0),
    ]
    ranked = sorted(factors, key=lambda item: abs(float(item[2])), reverse=True)
    top = ranked[:3]
    if not any(abs(float(item[2])) for item in top):
        top = [
            ('overall_profile', 'Balanced applicant profile', 1),
            ('medical_profile', 'Stable medical profile', 1),
            ('financial_profile', 'Stable financial profile', 1),
        ]
    return tuple(
        {
            'feature': feature,
            'label': label,
            'contribution': round(float(contribution), 4),
            'rank': index,
        }
        for index, (feature, label, contribution) in enumerate(top, start=1)
    )


def score_applicant(applicant: Applicant) -> RiskAssessmentResult:
    model = _load_model()
    row = _applicant_to_row(applicant)
    # Older artifacts were fitted with a fixed fallback, not a learned imputer.
    if getattr(model, 'applicant_input_schema', 1) < 3 and pd.isna(row['credit_score']):
        row['credit_score'] = 650
    features = build_feature_frame(pd.DataFrame([row]))
    if hasattr(model, 'predict_proba'):
        classes = list(model.classes_)
        probabilities = model.predict_proba(features)[0]
        probability_by_class = dict(zip(classes, probabilities, strict=False))
        predicted_category = max(probability_by_class, key=probability_by_class.get)
        predicted_score = (
            probability_by_class.get('LOW', 0) * 15
            + probability_by_class.get('MEDIUM', 0) * 50
            + probability_by_class.get('HIGH', 0) * 85
        )
        confidence = round(float(probability_by_class[predicted_category]), 3)
    else:
        predicted_score = float(model.predict(features)[0])
        predicted_category = categorize_risk_score(predicted_score)
        confidence = _risk_confidence(predicted_score)
    predicted_score = max(0.0, min(100.0, predicted_score))
    rounded_score = round(predicted_score, 1)
    return RiskAssessmentResult(
        risk_score=rounded_score,
        risk_category=predicted_category,
        confidence=confidence,
        top_factors=_factor_contributions(row),
    )


def assess_applicant(applicant: Applicant) -> RiskAssessment:
    result = score_applicant(applicant)
    active_version = _active_model_version()
    model_path = _active_model_path()
    model_version = (
        active_version.version_tag
        if active_version
        else datetime.datetime.fromtimestamp(model_path.stat().st_mtime).isoformat()
    )
    assessment = RiskAssessment.objects.create(
        applicant=applicant,
        risk_score=Decimal(str(result.risk_score)),
        risk_category=result.risk_category,
        confidence=Decimal(str(result.confidence)),
        model_version=model_version,
        needs_manual_review=result.confidence < settings.CONFIDENCE_THRESHOLD,
    )
    FeatureContribution.objects.bulk_create(
        FeatureContribution(
            assessment=assessment,
            feature=factor['feature'],
            label=factor['label'],
            contribution=Decimal(str(factor['contribution'])),
            rank=factor['rank'],
        )
        for factor in result.top_factors
    )
    Recommendation.objects.bulk_create(
        Recommendation(
            assessment=assessment,
            category='Lifestyle',
            message=message,
        )
        for message in build_lifestyle_recommendations(applicant)
    )
    return assessment
