# ISJ107V Assignment 3: Consolidated Final Answers

> **Academic walkthrough:** 66 automated tests pass. The three-role journey covers
> registration, administrator role assignment and account linking, real test-model
> scoring, read-only Applicant access and PDF export. Assessment-specific API PDFs
> now preserve the requested result. Experimental notices and rule-based indicator
> labels are included. Follow DEMONSTRATION_WALKTHROUGH.md and the updated screenshot
> checklist; browser UAT, external hosting and screenshots still require evidence.

> **Applicant-data workflow:** A labelled CSV matching live form inputs is now
> supported, with strict validation, observation-date age, background training and
> per-model evidence. An administrator can download an empty template. 61 automated
> tests pass. No real labelled applicant dataset has been supplied or approved;
> this does not change the research-only status of the Kaggle benchmark.

> **Native-feature benchmark (2026-10-17):** Accuracy 75.06%, macro F1 0.6718 on
> an internal test partition. This is separate from the applicant-form model,
> cannot be activated for live scoring, and misses production targets. The mapping
> audit found unsupported conversions. See evaluation/RESULTS.md for current evidence.

> **Current evidence:** Read the Deployment Audit Update at the end before using
> the historical metrics below. The corrected model scores 0.608 accuracy and
> 0.514 macro F1 and does not meet production acceptance criteria.

Student: Mc Makwela  
Module: ISJ107V  
Project: Integrated Life Insurance Risk Assessment System using Artificial Intelligence and Machine Learning  
Date: 30 September 2026  
Version: 1.0

This document consolidates the Assignment 3 PDF questions and the current implemented project evidence. Values that can be verified from the codebase and latest test/training runs are filled in. Items that still require your own records or screenshots are clearly marked as **USER EVIDENCE REQUIRED**.

## Question 1: Final Project Baseline [6]

### 1.1 Project Title, Purpose, Users, Emerging Technology and Executive Summary

**Project title:** Integrated Life Insurance Risk Assessment System using Artificial Intelligence and Machine Learning (ILIRAS).

**System purpose:**  
ILIRAS supports life insurance underwriting by consolidating applicant personal, medical, lifestyle, vehicle insurance, salary and spending data into one profile. The system uses a trained machine learning classifier to classify the applicant as Low, Medium or High risk and returns a numeric risk score, confidence value, top contributing factors, lifestyle recommendations and an underwriting report.

**Intended users:**

| User | Role in the system |
|---|---|
| Applicant | Views their own risk score, explanation and recommendations. |
| Underwriter | Captures applicant data, runs risk assessments and reviews reports. |
| Administrator | Manages users, roles, audit logs, datasets and model versions. |

**Selected emerging technology:**  
Artificial Intelligence / Machine Learning. The implemented solution uses a supervised Scikit-learn classifier for multi-class risk classification with explainability through stored feature contributions.

**Executive summary:**  
The final system is a Django-based underwriting support application. It provides registration and login, role-based applicant visibility, a guided applicant capture wizard, validation rules, ML-based risk classification, confidence reporting, manual-review flagging, top-three contributing factors, lifestyle recommendations, PDF underwriting reports, audit logging and REST-style API endpoints. The latest model evaluation used **20,000 generated applicant records** plus **20,000 transformed Kaggle/Prudential records** and produced accuracy of **0.935**, macro F1-score of **0.920**, and p95 inference latency of **5.74 ms**, meeting the approved emerging-technology targets.

### 1.2 Final Aim, Objectives, Scope and Approved Changes

**Final aim:**  
To design, implement and evaluate an integrated, AI-driven life insurance risk assessment system that produces fast, consistent and explainable risk classifications from consolidated applicant data.

| ID | Objective | Final result |
|---|---|---|
| OBJ-01 | Consolidate applicant data sources into one application data layer and support dataset import/training. | The implemented system consolidates applicant personal, medical, lifestyle, salary, vehicle and spending data in Django models. The final training run used **20,000 generated applicant records** plus **20,000 transformed Kaggle/Prudential records** from `etl/raw_data/train.csv`. |
| OBJ-02 | Deploy a multi-class model with accuracy >= 0.85 and macro F1 >= 0.80. | Achieved: accuracy **0.935**, macro F1 **0.920**. |
| OBJ-03 | Reduce assessment time to under 5 minutes. | The implemented workflow supports this through a six-step wizard and one-click risk assessment. **USER EVIDENCE REQUIRED:** record your own timed assessments, ideally 20 assessments. |
| OBJ-04 | Provide explainable predictions. | Achieved through `RiskAssessment`, `FeatureContribution`, confidence and manual-review status. |
| OBJ-05 | Provide auditability and role-based access. | Achieved through authentication, `UserProfile`, applicant visibility controls and `AuditLog`. |

**Scope:**

| In scope | Out of scope |
|---|---|
| Individual life insurance risk assessment | Premium billing |
| Applicant capture and validation | Payment processing |
| ML risk classification and explanation | Fully automated policy issuing |
| PDF underwriting reports | Native mobile application |
| Role-based access and audit logs | Live medical aid, credit bureau or traffic authority integrations |
| Dataset upload, training and model version records | Production insurer deployment |

**Changes since Assignment 2:**

| Area | Final implementation |
|---|---|
| Database | Project supports the current configured relational database and optional MySQL configuration through `DB_ENGINE=mysql`. |
| PDF reporting | Report generation is available through the reports module. |
| API | REST-style JSON endpoints exist under `/api/v1/...`; login returns a bearer token for API calls. |
| Model | The final model uses Scikit-learn classification and achieved the required quality metrics. |
| Dataset | Training uses generated applicant records plus transformed Kaggle/Prudential rows from `etl/raw_data/train.csv`. |

### 1.3 Document Control

| Field | Value |
|---|---|
| Document title | ISJ107V Assignment 3 - ILIRAS Final Project Documentation and UML Design |
| Version | 1.0 |
| Date | 30 September 2026 |
| Author | Mc Makwela |
| Status | Final draft |

**Revision history:**

| Version | Date | Author | Description |
|---|---|---|---|
| 0.1 | **USER EVIDENCE REQUIRED:** Assignment 1 submission date | Mc Makwela | Assignment 1 project proposal. |
| 0.2 | 19 September 2026 | Mc Makwela | Assignment 2 formal proposal and specification. |
| 1.0 | 30 September 2026 | Mc Makwela | Assignment 3 final documentation and UML design. |

**Glossary:**

| Term | Meaning |
|---|---|
| ILIRAS | Integrated Life Insurance Risk Assessment System. |
| ML | Machine Learning. |
| Risk score | Numeric score between 0 and 100. |
| Risk class | Low, Medium or High risk category. |
| Confidence | Probability or confidence value linked to the predicted risk class. |
| Feature contribution | Ranked factor influencing the risk result. |
| POPIA | Protection of Personal Information Act. |
| AuditLog | Stored audit trail of security and data-access events. |
| p95 | 95th percentile measurement. |

**Referenced artefacts:**

| Ref | Artefact | Location |
|---|---|---|
| A-01 | Assignment 1 proposal | Submitted on EC. |
| A-02 | Assignment 2 specification | Submitted on EC. |
| A-03 | Source repository | **USER EVIDENCE REQUIRED:** GitHub URL and release tag. |
| A-04 | Training command | `risk_engine/management/commands/train_risk_model.py` |
| A-05 | ML pipeline | `risk_engine/pipeline.py`, `risk_engine/features.py`, `risk_engine/risk_rules.py` |
| A-06 | Tests | `applicants/tests.py`, `risk_engine/tests.py` |
| A-07 | Raw reference dataset | `etl/raw_data/train.csv` |

## Question 2: Requirements and Traceability [8]

### 2.1 Final Requirements

| ID | Priority | Requirement | Acceptance criterion | Status |
|---|---|---|---|---|
| FR-01 | Must | Register and authenticate users. | Valid login succeeds; invalid login is rejected and audit logged. | Pass |
| FR-02 | Must | Capture applicant personal details. | A complete form creates an `Applicant`. | Pass |
| FR-03 | Must | Capture medical history. | Medical record is linked to applicant. | Pass |
| FR-04 | Must | Validate every field. | Invalid ID, age, BMI, credit score or spending values are rejected. | Pass |
| FR-05 | Must | Capture lifestyle, vehicle, salary and spending data. | Related profile records are stored. | Pass |
| FR-06 | Must | Predict risk class and score. | Complete applicant produces a stored `RiskAssessment`. | Pass |
| FR-07 | Must | Display three contributing factors. | Three ranked `FeatureContribution` records are stored/displayed. | Pass |
| FR-08 | Should | Generate and export underwriting report. | Report and PDF routes return applicant and risk information. | Pass |
| FR-09 | Should | Generate lifestyle recommendations. | Recommendations are generated and shown. | Pass |
| FR-10 | Could | Admin uploads dataset and retrains model. | Dataset upload/training route and model version records exist. | Pass/Partial, depending on whether rollback UI screenshot is included. |

| ID | Category | Requirement | Acceptance criterion | Status |
|---|---|---|---|---|
| NFR-01 | Usability | New underwriter can complete workflow after short training. | Guided wizard supports unaided completion. | Needs UAT evidence |
| NFR-02 | Reliability | Same model version gives consistent results for same input. | Active model artefact is loaded and version recorded. | Pass |
| NFR-03 | Performance | Assessment response and ML inference must be fast. | ML p95 inference below 50 ms. | Pass |
| NFR-04 | Security | Password hashing, RBAC and audit logging. | Django auth, roles and `AuditLog` exist. | Pass |
| NFR-05 | Maintainability | Modules separated by responsibility. | Apps are separated into `accounts`, `applicants`, `risk_engine`, `reports`, `etl`. | Pass |

### 2.2 Traceability Matrix

| Requirement | UML reference | Module | Test/evidence | Status |
|---|---|---|---|---|
| FR-01 | UC-01 Register/Login | `accounts` | Login/register views; audit log | Pass |
| FR-02 | UC-02 Capture Applicant | `applicants` | `ApplicantCreateWizardTests` | Pass |
| FR-03 | UC-03 Medical Profile | `applicants.models.MedicalHistory` | Wizard test | Pass |
| FR-04 | UC-04 Validate Data | `applicants.forms` | `ApplicantFormValidationTests` | Pass |
| FR-05 | UC-05 Capture Full Profile | `applicants.views` | Wizard saves all related records | Pass |
| FR-06 | UC-06 Assess Risk | `risk_engine.scoring`, `risk_engine.views` | `RiskAssessmentViewTests` | Pass |
| FR-07 | UC-07 Explain Prediction | `FeatureContribution` | Detail/report templates | Pass |
| FR-08 | UC-08 Export PDF | `reports.views` | `ReportTests.test_pdf_export_returns_pdf_response` | Pass |
| FR-09 | UC-09 Recommendations | `risk_engine.recommendations` | `RecommendationTests` | Pass |
| FR-10 | UC-10 Dataset/Retrain | `risk_engine.api`, `ModelVersion`, admin/model page | Training command and model version record | Pass/Partial |
| NFR-03 | Deployment/Performance | `train_risk_model.py` | p95 inference 5.74 ms | Pass |
| NFR-04 | Security model | `accounts.models`, `applicants.permissions` | access tests and audit model | Pass |

### 2.3 Emerging-Technology Requirements

| ID | Requirement | Evidence | Status |
|---|---|---|---|
| ETR-01 | Accuracy >= 0.85 and macro F1 >= 0.80. | Accuracy **0.935**, macro F1 **0.920**. | Pass |
| ETR-02 | Prediction output within 50 ms p95 and includes explanation. | p95 **5.74 ms**; output includes class, score, confidence, model version and top factors. | Pass |
| ETR-03 | Retraining and versioning. | `TrainingDataset` and `ModelVersion` records exist; training command creates model version records. | Pass/Partial depending on rollback demonstration evidence. |

## Question 3: Final Design as Implemented [16]

### 3.1 High-Level Architecture

Use the architecture diagram already embedded in the completed DOCX, but ensure labels match the implementation:

- Users: Applicant, Underwriter, Administrator.
- Interface: browser-based Django templates plus `/api/v1` JSON endpoints.
- Services: Accounts, Applicant Capture Wizard, Risk Controller, Risk Prediction Service, Report Generator, Audit Logger.
- Data stores: relational database, uploaded datasets, `risk_model.joblib`, versioned model artefacts.
- External data: Kaggle/Prudential `train.csv` is transformed into the project feature schema for model training; live external APIs are out of scope.

### 3.2 Use-Case Diagram and Core Use Case

The completed DOCX answers this section. Replace the note `[confirm no use case was added or removed]` with:

> The implemented use cases remain aligned with the approved Assignment 2 scope. The final implementation adds supporting model-version and audit-management screens, but these support the existing Administrator use case and do not change the core system boundary.

**Detailed use case: UC-04 Predict Insurance Risk**

| Field | Description |
|---|---|
| Actor | Underwriter |
| Preconditions | User is authenticated; applicant exists; profile sections are complete; active model exists. |
| Trigger | Underwriter selects Run Risk Assessment. |
| Normal flow | Load applicant, validate complete profile, build features, call ML model, compute score/confidence, store `RiskAssessment`, store top three factors, store recommendations, audit the action, display result. |
| Alternative flows | Incomplete profile returns an error; missing model returns service unavailable; low confidence sets manual review status; unauthorized access returns 404/403. |
| Postcondition | Assessment, explanation and audit record are stored. |

### 3.3 Class Diagram

The class diagram should include:

`User`, `UserProfile`, `AuditLog`, `Applicant`, `MedicalHistory`, `LifestyleHabits`, `Salary`, `VehicleInsuranceHistory`, `SpendingBehaviour`, `RiskAssessment`, `FeatureContribution`, `Recommendation`, `TrainingDataset`, `ModelVersion`.

Important multiplicities:

- `User 1..1 UserProfile`
- `User 1..* Applicant`
- `Applicant 1..1 MedicalHistory`
- `Applicant 1..1 LifestyleHabits`
- `Applicant 1..1 Salary`
- `Applicant 1..1 VehicleInsuranceHistory`
- `Applicant 1..1 SpendingBehaviour`
- `Applicant 1..* RiskAssessment`
- `RiskAssessment 1..3 FeatureContribution`
- `RiskAssessment 0..* Recommendation`
- `TrainingDataset 0..* ModelVersion` conceptually through training/version metadata

### 3.4 Sequence Diagram

Replace the note `[confirm it still matches the code]` with:

> The sequence diagram matches the implemented flow in `risk_engine.views.assess_applicant_view()` and `risk_engine.scoring.assess_applicant()`: the UI posts the applicant ID, the view checks applicant visibility, the scoring service loads the active model, features are generated, prediction and explanation are produced, records are saved, an audit log is written and the user is redirected to the applicant detail page.

### 3.5 Activity Diagram

The completed DOCX answers this section. Ensure it includes:

- Login decision.
- Applicant capture and validation.
- Complete-profile decision.
- Prediction/model-available decision.
- Manual-review branch for low confidence.
- PDF export branch.
- Error completion states.

### 3.6 Component and Deployment Diagrams

The completed DOCX answers this section. Ensure the component diagram uses the actual module names:

`accounts`, `applicants`, `risk_engine`, `reports`, `etl`, `config`, `templates`, `static`.

The deployment diagram may show the intended production environment:

- Browser client.
- Django/Gunicorn app container.
- Celery worker.
- Redis broker/cache.
- Relational database.
- Nginx reverse proxy.
- Static/media storage.
- Model artefact storage.

## Question 4: Implemented Solution Documentation [10]

### 4.1 Technology Stack, Structure and Screenshots

| Layer | Technology |
|---|---|
| UI | HTML5, CSS3, Django templates, Bootstrap-style UI |
| Application | Python, Django 5.2 |
| API | Django JSON endpoints under `/api/v1`; DRF installed for API support |
| Database | Relational database; current local config supports PostgreSQL and optional MySQL through `DB_ENGINE=mysql` |
| Machine learning | Scikit-learn, Pandas, NumPy, joblib |
| PDF reporting | Report generation in `reports` |
| Background/deployment support | Celery/Redis dependencies added; training command available |
| Testing | Django `TestCase`, SQLite test settings |

**Actual project structure:**

| Folder/module | Responsibility |
|---|---|
| `accounts` | Authentication, roles, audit logs, dashboard. |
| `applicants` | Applicant models, forms, wizard, permissions. |
| `risk_engine` | ML features, scoring, API, model versions, training commands. |
| `reports` | Underwriting report and PDF export. |
| `etl` | Synthetic data generation, Kaggle/Prudential transformation and CSV applicant import. |
| `config` | Settings, URLs, WSGI/ASGI, Celery app. |
| `templates`, `static` | Shared layout and styling. |

**Screenshots still required:**

| Figure | Screenshot required |
|---|---|
| Figure 4.1 | Login screen. |
| Figure 4.2 | Applicant capture form showing validation error. |
| Figure 4.3 | Risk result page showing score, confidence, top factors and recommendations. |
| Figure 4.4 | Administrator/model-management page showing dataset upload and model versions. |

### 4.2 Database / Dataset

**Main data entities:**

| Entity | Purpose |
|---|---|
| User/UserProfile | Authentication and role management. |
| AuditLog | Records login, access, changes, reports, assessments and training events. |
| Applicant | Main applicant identity/contact/demographic record. |
| MedicalHistory | Height, weight, BMI, blood pressure, chronic/family history. |
| LifestyleHabits | Smoking, alcohol, exercise and occupation risk. |
| Salary | Employment and income. |
| VehicleInsuranceHistory | Driving and vehicle-claim history. |
| SpendingBehaviour | Expenses, savings, debt and credit score. |
| RiskAssessment | Risk score, class, confidence, model version and manual-review flag. |
| FeatureContribution | Top contributing factors. |
| Recommendation | Stored lifestyle recommendations linked to assessment. |
| TrainingDataset | Uploaded/retraining dataset metadata. |
| ModelVersion | Version tag, training date, metrics, artefact path and active flag. |

**Dataset statement:**  
The final training pipeline uses two data sources. First, it generates project-shaped synthetic applicant records from `etl.synthetic.generate_synthetic_applicants()`. Second, it loads the Prudential/Kaggle life insurance dataset from `etl/raw_data/train.csv` and transforms its age, BMI, medical, employment, insurance-history and response fields into the project feature schema through `etl.kaggle.load_prudential_applicants()`. The final measured run used **20,000 synthetic rows** and **20,000 Kaggle/Prudential rows**. Kaggle `Response` values are mapped into Low, Medium and High risk classes for supervised training.

**Validation rules:**

| Field | Rule |
|---|---|
| National ID | 13 numeric digits, unique. |
| Date of birth | Age 18 to 75. |
| Consent | Must be recorded before saving. |
| BMI | 10 to 60. |
| Blood pressure | `systolic/diastolic` format when entered. |
| Credit score | 300 to 850. |
| Exercise days | 0 to 7. |
| Expenses | May not exceed salary by more than 200%. |
| Risk assessment | Requires all profile sections. |

**Privacy controls:**  
Django password hashing, authenticated access, role-based visibility, audit logs, CSRF protection and secure cookie settings for production. Independent penetration testing has **not** been performed unless you have evidence otherwise.

**Backup approach:**  
For production, back up the relational database nightly, back up uploaded datasets and model artefacts, encrypt backups, store off-site copies and test restoration regularly.

### 4.3 Main API / Integration Interface

| Method | Endpoint | Auth | Output |
|---|---|---|---|
| POST | `/api/v1/auth/register` | Public | `201`, `userId` |
| POST | `/api/v1/auth/login` | Public | Bearer token, `userId` |
| POST | `/api/v1/applicants` | Bearer/session auth | `201`, `applicantId` |
| POST | `/api/v1/predict-risk` | Bearer/session auth | risk class, score, confidence, model version, manual-review flag, top factors, recommendations |
| GET | `/api/v1/assessments/{id}` | Bearer/session auth | Full assessment |
| GET | `/api/v1/reports/{id}` | Bearer/session auth | PDF report |
| POST | `/api/v1/datasets` | Administrator | Dataset ID, training job ID, model version |

**Error handling:**  
`400` invalid payload, `401` unauthenticated, `403` role not permitted, `404` hidden/missing record, `422` incomplete profile, `503` missing model.

### 4.4 Installation, Configuration and Deployment

**Local setup:**

1. Create/activate virtual environment.
2. Run `pip install -r requirements.txt`.
3. Create `.env` with `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.
4. Optional MySQL: set `DB_ENGINE=mysql`.
5. Run `python manage.py migrate`.
6. Run `python manage.py createsuperuser`.
7. Run `python manage.py train_risk_model --rows 20000` or alias `python manage.py train_model --rows 20000 --activate`.
8. Run `python manage.py runserver 127.0.0.1:8000`.

**Minimum hardware/software:**

| Component | Minimum |
|---|---|
| CPU | 2-core x86-64 |
| RAM | 4 GB |
| Storage | 20 GB free |
| Client | Current Chrome, Edge or Firefox |
| Server software | Python, Django dependencies, relational database |

## Question 5: Evaluation and Responsible Use [10]

### 5.1 Test Summary

| Level | Executed | Passed | Evidence |
|---|---:|---:|---|
| Unit | Included in 33-test Django suite | All passing | `ApplicantFormValidationTests`, `RecommendationTests` |
| Integration | Included in 33-test Django suite | All passing | `ApplicantCreateWizardTests`, `RiskAssessmentViewTests` |
| System | Included in 33-test Django suite | All passing | `ReportTests`, access-control tests |
| UAT | **USER EVIDENCE REQUIRED** | **USER EVIDENCE REQUIRED** | Timed user testing records |

Automated test command:

```bash
python manage.py test --settings=config.test_settings
```

Result: **33 tests run, all passed.**

Representative tests:

| ID | Level | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|
| UT-01 | Unit | BMI = 120 rejected. | Invalid BMI rejected by form validation. | Pass | `ApplicantFormValidationTests` / form validation |
| UT-02 | Unit | Risk score is between 0 and 100. | Scoring clamps result to 0-100 and returns score/category/confidence. | Pass | `risk_engine/scoring.py` |
| IT-01 | Integration | Complete profile can be assessed. | Owner can assess own applicant; assessment view redirects after scoring. | Pass | `RiskAssessmentViewTests` |
| IT-02 | Integration | Incomplete profile returns 422/no stored assessment. | API catches `IncompleteApplicantProfileError` and returns 422. | Pass by implementation; add API test if required. | `risk_engine/api.py` |
| TC-01 | System | Valid login accepted, invalid rejected and logged. | Implemented in `AccountLoginView` and API login. | Pass | `accounts/views.py`, `accounts/audit.py` |
| TC-08 | System | PDF endpoint returns PDF. | PDF response returned with `application/pdf`. | Pass | `ReportTests.test_pdf_export_returns_pdf_response` |
| UAT-01 | UAT | 8/10 users finish under 5 minutes and rate explanation >= 4/5. | **USER EVIDENCE REQUIRED** | Pending | UAT forms/timing sheet |

### 5.2 Quantitative Evaluation

| Metric | Target | Measured | Status |
|---|---:|---:|---|
| ML accuracy | >= 0.85 | 0.935 | Pass |
| ML macro F1 | >= 0.80 | 0.920 | Pass |
| ML p95 inference | <= 50 ms | 5.74 ms | Pass |
| Response time at 50 users | <= 3 s | **USER EVIDENCE REQUIRED** | Pending |
| SUS score | >= 70 | **USER EVIDENCE REQUIRED** | Pending |
| Unaided completion | >= 90% | **USER EVIDENCE REQUIRED** | Pending |

Confusion matrix, labels in order LOW, MEDIUM, HIGH:

| Actual \ Predicted | Low | Medium | High | Recall |
|---|---:|---:|---:|---:|
| Low | 4870 | 350 | 1 | 0.933 |
| Medium | 36 | 1587 | 24 | 0.964 |
| High | 0 | 107 | 1025 | 0.905 |

Per-class summary:

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Low | 0.993 | 0.933 | 0.962 | 5221 |
| Medium | 0.776 | 0.964 | 0.860 | 1647 |
| High | 0.976 | 0.905 | 0.940 | 1132 |

### 5.3 User Guide

1. Open the system URL.
2. Log in or register.
3. Select **New Applicant**.
4. Complete personal details and record consent.
5. Complete medical, lifestyle, salary, vehicle and spending sections.
6. Open the applicant profile.
7. Select **Run Risk Assessment**.
8. Review risk class, score, confidence, manual-review flag, top factors and recommendations.
9. Select **Report** to view the underwriting report.
10. Select **PDF** to export the report.

Screenshots still required:

- Figure 5.1: Applicant profile with all sections complete and Run Risk Assessment button.
- Figure 5.2: Result page with top-three factors and PDF export button.

Troubleshooting:

| Problem | Likely cause | Fix |
|---|---|---|
| Cannot log in | Wrong credentials | Retry or reset password. |
| Field error | Value outside validation range | Correct the field shown in red. |
| Incomplete profile | One section missing | Complete all wizard sections. |
| Model-not-trained error | Missing model artefact | Run `python manage.py train_risk_model --rows 20000`. |
| PDF fails | PDF dependency/config issue | Check server logs and installed dependencies. |
| Cannot see applicant | Permission/role restriction | Use correct owner/admin account. |

### 5.4 Limitations, Risks, Ethics, Maintenance and Improvements

**Limitations:**

1. Kaggle/Prudential data is transformed into the local feature schema, but some project fields such as vehicle history do not have direct Kaggle equivalents and are filled with neutral or derived values.
2. No live medical aid, credit bureau or traffic authority integrations.
3. The system supports underwriting decisions but does not issue policies or calculate premiums.
4. UAT, SUS and 50-user load testing still need user-generated evidence unless already performed separately.

**Risks and ethics:**

- Sensitive medical and financial information must be protected under POPIA.
- Automated risk classification may affect affordability and access to insurance, so human final sign-off remains necessary.
- Bias and model drift must be monitored before any production use.
- No independent penetration test has been completed unless you have external evidence.

**Maintenance needs:**

- Regular dependency updates.
- Backup and restore testing.
- Periodic model retraining.
- Audit-log review.
- Fairness checks by age/gender groups.
- Update tests when new features are added.

**Future improvements:**

1. Improve the Kaggle transformation by documenting each source-column mapping and validating it with domain experts.
2. Add SHAP-style per-applicant explanations and a fairness/drift monitoring dashboard.

## Remaining User Evidence Required

These are the only items that cannot be truthfully filled from the project files alone:

1. Assignment 1 submission date.
2. GitHub repository URL and release tag.
3. Timed UAT results: mean assessment time and number of assessments.
4. SUS score and unaided completion percentage.
5. 50-user response time/load test result.
6. Screenshots for Figures 4.1-4.4 and 5.1-5.2.
7. Confirmation of whether an independent penetration test was done.

# Deployment Audit Update (2026-10-17)

Historical metrics and completion claims below are superseded where inconsistent
with this update. Removing target leakage and retraining on 59,381 Kaggle records
produced accuracy 0.608, macro F1 0.514 and p95 inference 19.62 ms. The candidate
remains inactive and fails the 0.85 accuracy / 0.80 macro F1 production thresholds.
Do not present the previous 0.935 / 0.920 scores as validated results.
Dataset uploads now train from the actual uploaded Prudential CSV through a separate
worker. Public signup is Applicant-only; administrators assign staff roles and
verify explicit applicant-account links. See DEPLOYMENT.md for current procedures.
