from __future__ import annotations

from applicants.models import Applicant


def build_lifestyle_recommendations(applicant: Applicant) -> list[str]:
    recommendations: list[str] = []

    medical = getattr(applicant, 'medical_history', None)
    lifestyle = getattr(applicant, 'lifestyle_habits', None)
    salary = getattr(applicant, 'salary', None)
    vehicle = getattr(applicant, 'vehicle_insurance_history', None)
    spending = getattr(applicant, 'spending_behaviour', None)

    if lifestyle:
        if lifestyle.smoker:
            recommendations.append('Join a smoking cessation programme to reduce long-term health risk.')
        if lifestyle.alcohol_consumption == lifestyle.AlcoholConsumption.HEAVY:
            recommendations.append('Reduce alcohol intake and consider a health screening for alcohol-related risks.')
        elif lifestyle.alcohol_consumption == lifestyle.AlcoholConsumption.MODERATE:
            recommendations.append('Keep alcohol intake moderate and avoid frequent binge drinking.')
        if lifestyle.exercise_days_per_week < 3:
            recommendations.append('Increase physical activity to at least three days per week.')
        if lifestyle.occupation_risk_level == lifestyle.OccupationRiskLevel.HIGH:
            recommendations.append('Use workplace safety measures and keep occupational risk documentation updated.')

    if medical:
        bmi = float(medical.bmi)
        if bmi >= 30:
            recommendations.append('Work with a health professional on a BMI and weight-management plan.')
        elif bmi >= 25:
            recommendations.append('Improve diet and exercise habits to bring BMI closer to a healthy range.')
        if medical.has_chronic_illness:
            recommendations.append('Maintain regular medical check-ups and follow prescribed treatment plans.')
        if medical.has_family_history_of_illness:
            recommendations.append('Schedule preventive screenings related to known family medical history.')

    if vehicle:
        if vehicle.number_of_accidents or vehicle.traffic_violations:
            recommendations.append('Complete defensive-driving training and reduce traffic violations.')
        if not vehicle.has_vehicle_insurance:
            recommendations.append('Maintain active vehicle insurance to reduce financial exposure.')

    if spending and salary:
        monthly_income = max(float(salary.monthly_income), 1.0)
        savings_rate = float(spending.monthly_savings) / monthly_income
        debt_to_annual_income = float(spending.total_debt) / (monthly_income * 12)
        if savings_rate < 0.1:
            recommendations.append('Build monthly savings toward at least 10 percent of income.')
        if debt_to_annual_income > 0.5:
            recommendations.append('Reduce debt exposure before taking on additional financial commitments.')
        if spending.credit_score and spending.credit_score < 670:
            recommendations.append('Improve credit behaviour by paying accounts on time and reducing outstanding balances.')

    if not recommendations:
        recommendations.append('Maintain current healthy lifestyle, financial, and insurance habits.')

    return recommendations
