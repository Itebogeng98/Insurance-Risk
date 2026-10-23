# Labelled Applicant Training Data

The administrator model page now offers an empty CSV template and accepts that
format through the existing queued training workflow. No sample applicants or
invented labels are included. The API upload endpoint accepts the same format.

## Required Columns

Use the template's exact header. Unexpected columns are rejected so identifiers,
names and other unrelated information cannot accidentally become predictors.

- `record_id`: non-identifying source key; unique, with one record per person.
- `observation_date`, `date_of_birth`: YYYY-MM-DD. Age is calculated at observation,
  not the date the model happens to be trained. Observation must not be in the future.
- `height_cm`, `weight_kg`: measured values in the named units.
- `monthly_income`, `monthly_expenses`, `monthly_savings`, `total_debt`: ZAR.
- `years_employed`, `years_licensed`: years.
- `number_of_accidents`, `number_of_claims`, `traffic_violations`: integer counts.
- `exercise_days_per_week`: integer 0-7.
- `credit_score`: integer 300-850, or blank if genuinely unknown.
- `smoker`, `has_chronic_illness`, `has_family_history_of_illness`,
  `has_vehicle_insurance`: true/false or 1/0.
- `gender`: M, F or O.
- `alcohol_consumption`: NONE, OCCASIONAL, MODERATE or HEAVY.
- `occupation_risk_level`: LOW, MEDIUM or HIGH.
- `employment_status`: EMPLOYED, SELF_EMPLOYED, UNEMPLOYED or RETIRED.
- `label_source`: HUMAN_UNDERWRITING.
- `risk_category`: LOW, MEDIUM or HIGH, from a documented human underwriting
  decision. Do not export this application's predictions as training truth.

Use consistent observation windows for accident/claim/violation counts and a
consistent credit-score provider. Record those definitions in the provenance
evidence; matching column names does not establish measurement equivalence.

## Validation and Training

Files must contain 30-200,000 rows, at least five per risk category, and be at most
50 MB through the upload interface. These are technical minimums, not statistical
adequacy criteria. Blank required fields, invalid enums, non-finite numbers,
implausible measurements and inconsistent finances are rejected with CSV row
numbers. Repeated source keys and identical feature rows are rejected for review.
Distinct keys cannot prove distinct people; the supplier must enforce that rule.

Training uses these rows directly and never generates labels or mixes Kaggle or
synthetic records into an applicant CSV run. Record keys, observation dates and
label-source text do not enter the classifier. Observation date is used only to
calculate age. Numeric missing-value imputation is fitted inside the training
pipeline. The fixed classifier uses a stratified 80/20 internal holdout; balancing
is applied only to the training partition.

Every candidate remains inactive. A JSON file beside its model artifact records
the source checksum, format, row counts, seed, metrics and feature names. Scores
from internal testing are not external validation or proof of suitability.

## Required Evidence Before Approval

The uploader's `HUMAN_UNDERWRITING` value is a declaration, not authentication.
Models remain `input_contract_verified=False` after schema validation. No public
or administrator screen can override that flag.

Before a reviewed integration may approve a model, establish source authorization,
measurement definitions and units, outcome definitions and label provenance,
one-record-per-person handling, population representativeness, and independent
performance evidence. All predictors must be available before the decision.

No suitable real labelled dataset has been supplied yet. This change provides the
ingestion/training path; it does not claim that the production model is validated.

## Local Commands

```powershell
venv\Scripts\python.exe manage.py process_training_jobs
venv\Scripts\python.exe manage.py train_risk_model --csv-path PATH_TO_LABELLED_CSV
```

The first command processes administrator uploads; the second trains a file
directly. Both leave candidates inactive unless explicit activation is requested,
and production gates still reject unverified inputs or below-target metrics.
