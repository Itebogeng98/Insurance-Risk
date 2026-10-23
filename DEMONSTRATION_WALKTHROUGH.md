# Academic Demonstration Walkthrough

This is an experimental academic application, not a validated underwriting service.
Keep `ACADEMIC_DEMO=True` (the default) so the interface and PDF exports identify it.
No sample users or applicant records were added to the working database by the
automated walkthrough. All test fixtures and temporary trained models were isolated.

## Local Preparation

Open http://127.0.0.1:8000 and use three separate browser profiles or sign out between
roles. Use a fictional applicant labelled as demonstration data; do not use real
medical, financial or identification information for screenshots.

If the app or worker is stopped, run these in separate terminals from this folder:

```powershell
venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
venv\Scripts\python.exe manage.py process_training_jobs
```

Use the existing administrator account. If none exists, create one interactively
with `venv\Scripts\python.exe manage.py createsuperuser`. Do not publish passwords.
An Administrator profile alone does not grant Django admin access: the setup
administrator must also have staff status and the appropriate Django permissions.
Use the superuser only for administration, not for the Underwriter demonstration.

## Demonstration Order

1. Register the Applicant through `/accounts/register/`. It must not offer staff roles.
   Before linking a record, the Applicant has no access to someone else's records.
2. Register a separate staff candidate account. As the setup administrator, open
   `/admin/accounts/userprofile/` and assign that account the Underwriter role.
3. Sign in as Underwriter. Open `/applicants/create/`, submit an incomplete first step,
   capture the validation errors, then complete all six steps for the fictional record.
4. As administrator, open the record under `/admin/applicants/applicant/`, verify the
   intended account and select it in the Account field. Save the record. Email alone
   must not grant access.
5. As Underwriter, run an assessment with the existing local demonstration model.
   Capture the experimental banner, result, confidence and rule-based indicators.
   These indicators are heuristic scores, not model feature attribution.
6. Export the report and PDF. The PDF must identify the result as an academic
   demonstration. Web reports show the latest result; the assessment-specific API
   PDF shows the requested historical result.
7. As Applicant, open the linked record and report. The Run Risk Assessment action
   and model-management access must be unavailable. Changing email must not change
   which record the account can access.
8. As administrator, open `/risk/models/`. Download the empty Applicant CSV template.
   Submit an invalid CSV and show that it creates no training job. Use genuine
   labelled records only for the applicant-data path. A permitted Kaggle file may
   demonstrate the experimental queued-training path; its candidate is not approved.
9. Inspect `/admin/accounts/auditlog/` for assessment and report-access events.
   Capture only entries suitable for sharing, without private account information.

## Evidence and Limits

The automated journey uses actual Django views, admin forms, a temporary trained
classifier and ReportLab PDF generation. The complete six-step wizard save is
covered by a separate regression test. This is not a substitute for browser visual
inspection, user acceptance testing, load testing or backup restoration testing.
The full automated suite passed **66 tests** after these changes.

Current native Kaggle benchmark: 75.06% accuracy and 0.6718 macro F1. It does not
meet the 85% / 0.80 targets and cannot consume the live applicant-form features.
The earlier adapter result is a separate 60.8% / 0.514 experiment. Do not present
legacy model-registry values or synthetic-test scores as current validation evidence.

## Hosting

Local demonstration is available; no public or private external host has been
provisioned by this walkthrough. For a hosted demonstration, choose a host/domain,
restrict access to the evaluator and complete the staging checks in DEPLOYMENT.md.
Production model gates remain enabled in `config.production`; this walkthrough
does not weaken them to make an experimental model appear production-ready.
