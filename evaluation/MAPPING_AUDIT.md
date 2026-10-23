# Kaggle-to-Applicant Mapping Audit

Source: [Prudential competition data dictionary](https://www.kaggle.com/c/prudential-life-insurance-assessment/data/).

The dictionary identifies normalized measurements and anonymized variable groups.
It does not supply the semantic definitions or inverse normalization needed to
translate the existing application form into these features. A native Kaggle
benchmark therefore cannot be substituted for the application scoring model.

| Existing mapping in etl/kaggle.py | Finding | Decision |
| --- | --- | --- |
| Ins_Age -> 18 + value * 57 | Age is normalized; the chosen range is unverified. | Keep normalized age in offline benchmark. Do not claim conversion to actual age. |
| Ht/Wt -> centimetres/kilograms | The selected bounds are unverified; recomputed BMI differs from the provided normalized BMI. | Use Ht, Wt and BMI independently in the benchmark. |
| InsuredInfo_1 parity -> gender | A nominal code is not documented as gender. | Do not infer gender. |
| Medical_Keyword_15 -> smoking | Keyword identity is not documented. | Keep it as an anonymized binary feature only. |
| Medical_History_1 quantiles -> alcohol use | The source is a discrete medical-history code, not reported alcohol consumption. | Do not infer drinking behaviour. |
| Medical keyword count -> chronic illness | Number of keywords does not establish a diagnosis. | Do not infer a diagnosis. |
| Family_Hist_1 -> family illness | Nominal categories have no published clinical interpretation here. | Keep as nominal for research only. |
| Employment_Info -> income, occupation risk, years employed | Employment-related variables do not establish the chosen currency, units or categories. | Keep original variables; remove semantic claims. |
| BMI quantiles -> exercise days | BMI does not measure exercise frequency. | Do not infer exercise habits. |
| Vehicle, credit, debt and spending defaults | Constants are not observed applicant data, even after removing target leakage. | Exclude fabricated fields from the native benchmark. |
| Response -> three risk groups | This is a project-defined grouping of ordinal application outcomes. | Freeze the grouping for comparisons; do not describe it as calibrated clinical risk. |

## Experiment Protocol

- Use the original predictor columns; exclude Id and Response.
- Remove identical predictor rows before splitting to avoid duplicate overlap.
- Sort by ID and use a fixed seed, stratified 60% training / 20% validation / 20% test.
- Fit encoders and imputers on training rows only.
- Compare a majority baseline, balanced logistic regression and two predefined histogram gradient boosting models.
- Select by validation macro F1, then accuracy; refit on train + validation and evaluate the selected model once on test.
- Save source fingerprint, split fingerprints, configuration, metrics and confusion matrix.
- Do not register, activate or expose this research model to live scoring.

This is an internal holdout, not external validation: the dataset was already used
in previous project experiments. The old 0.608/0.514 run used different inputs and
partitions, so a higher new score is not a controlled measure of algorithm improvement.

## Production Decision

The old applicant-shaped Kaggle transformer remains a demonstration adapter for
compatibility, not a verified feature contract. Production approval requires a
dataset containing the actual form inputs and trustworthy outcomes, or a formally
documented alternative feature schema that can also be collected at prediction time.
Numeric accuracy/F1 thresholds alone do not establish suitability.

The current model registry records whether that input contract has been verified.
Existing and uploaded Prudential demonstration models are unverified. This flag
is not an editable administrator override: verified provenance must come from a
reviewed training integration. Native benchmark results never create model records.

An applicant-schema upload path is now implemented. See
[APPLICANT_DATA_CONTRACT.md](APPLICANT_DATA_CONTRACT.md) for the exact fields,
validation, template and provenance requirements. It uses supplied outcomes and
actual measurements without the Kaggle adapter. Candidates remain unverified
until provenance review; no real labelled dataset has been supplied yet.

## Reproduction

```powershell
venv\Scripts\python.exe manage.py evaluate_kaggle
```

Output: `evaluation/kaggle_native.json`. Existing output is not overwritten.
Any further tuning must use validation data, and repeatedly consulting the test
scores makes the test set part of development rather than independent evidence.
