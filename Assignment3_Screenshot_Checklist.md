# Assignment 3 Screenshot Checklist

Follow DEMONSTRATION_WALKTHROUGH.md. Capture screenshots yourself after completing
the relevant workflow; screenshots, UAT participant feedback and load-test evidence
have not been fabricated or marked complete by the automated tests.

## Required Figures

| Figure | Role / page | Required evidence |
| --- | --- | --- |
| 4.1 | Public, `/accounts/login/` and `/accounts/register/` | Branding, sign-in and Applicant-only public registration. |
| 4.2 | Underwriter, `/applicants/create/?step=1` | Actual validation error for an incomplete or invalid form. |
| 4.3 | Underwriter, `/applicants/<id>/` | Experimental banner, score, category, confidence and rule-based indicators. |
| 4.4 | Administrator, `/risk/models/` | Upload form, empty CSV template link, version list and production-approval status. |
| 5.1 | Underwriter, `/applicants/<id>/` | Completed profile and Run Risk Assessment action before assessment. |
| 5.2 | Linked Applicant, `/reports/applicants/<id>/` and PDF | Readable report; PDF academic-demonstration notice. |

## Role and Security Evidence

| Evidence | Capture |
| --- | --- |
| Staff assignment | Administrator assigning Underwriter in user profiles. |
| Explicit account link | Administrator assigning the fictional record's Account field. |
| Applicant restrictions | Linked record visible, assessment action absent, model-management access denied. |
| Invalid dataset | Actual validation message; no new training job created. |
| Audit trail | Assessment and report-access entries, without private information. |

## Test and Model Evidence

- Run `venv\Scripts\python.exe manage.py test --settings=config.test_settings` and
  capture the actual count and OK result. Do not reuse the obsolete 33-test claim.
- Use `evaluation/kaggle_native.json` and `evaluation/RESULTS.md`: native benchmark
  accuracy **75.06%**, macro F1 **0.6718**, below required targets.
- Keep the native benchmark separate from the earlier adapter's **60.8% / 0.514**.
- Do not claim historical **0.935 / 0.920** metrics as current validated performance.
- Dataset format support is implemented, but no real applicant dataset has been
  supplied and approved. An empty template is not training evidence.

## Presentation

- Use one fictional applicant marked as demonstration data, with no real personal details.
- Keep the academic-demonstration notice visible in result screenshots and reports.
- Do not expose passwords, tokens, unrelated records or private desktop information.
- Caption heuristic indicators accurately; they are not SHAP values or causal explanations.
- Record browser/device, date, actual outcome and any failures during your walkthrough.
- Keep user acceptance, load testing, external hosting and backup restoration marked
  pending until performed and supported by evidence.
