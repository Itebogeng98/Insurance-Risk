# Assignment 5: final presentation priorities

Reviewed 17 November 2026 against the supplied seven-page Assignment 5 brief
and current project source. This is advice and an evidence checklist, not a claim
that the deployed system has been verified. No tests were run.

## What the rubric requires

The final presentation is worth 40% of the module, marked out of 50. Submit final
slides, editable UML and an accessible repository through MyTUTor before the
presentation. Prepare a local/offline fallback with evidence that it works.

Timing conflict: the instructions specify 12-15 minutes plus approximately five
minutes of questions; Q5.1 refers to an allocated five minutes. Confirm with the
lecturer. Pending clarification, prepare five minutes of explanation and eight
minutes of demonstration, with questions afterwards. Do not reuse the old
Assignment 4 timing without adapting it.

| Section | Marks | What to show | Current priority |
| --- | --- | --- | --- |
| Q1 Context and scope | 6 | Problem, aim, users, final requirements, stack, incomplete items | Name Applicant, Underwriter and Administrator; distinguish completed features from unverified deployment behaviour. |
| Q2 Functional system | 16 | End-to-end workflow, validation recovery, working ML, persistence, access controls | Highest priority. Historical demo applications do not replace a working assessment demonstration. |
| Q3 UML | 10 | Use case, class, sequence or activity, component AND deployment views, traceability | Reuse editable PlantUML in docs/assignment4/uml only after checking it matches the final workflow. A combined component/deployment figure must explain both views. |
| Q4 Evaluation | 8 | Functional/integration/system/UAT outcomes, quantitative metrics, benefit, ethics, limitation | Current pass/fail/unresolved counts are not established here. Do not turn source inspection into a test pass. |
| Q5 Delivery and mastery | 10 | Clear delivery, fallback, evidence-backed answers, personal contribution | Rehearse transitions and prepare concise answers about permissions, model inputs and deployment. |

## Priority order before the presentation

1. Confirm normal Administrator login as mcmakwela. An account name alone does
   not prove its deployed role or that its password works.
2. Import the 36 synthetic profiles using deploy/PRESENTATION_DATA.md. State
   aloud that their application dates and personal data are simulated.
3. Establish whether a genuine assessment can execute on the deployed system.
   config/render.py disables model training and activation. The production model
   gate requires verified live inputs and threshold metrics. Do not disable the
   gate merely to make the presentation appear successful.
4. Capture evidence of the exact workflow you can demonstrate. If ML is blocked,
   identify it as incomplete and show the real offline evaluation separately.
   This is a marking risk for Q2.2, not something extra demo records solve.
5. Prepare separate role sessions and an existing verified Applicant account
   link. The imported records have no Applicant account links and belong to the
   administrator, so an Underwriter's scoped list will not show this batch.
6. Prepare a local fallback and check it yourself if you retain the instruction
   that the coding agent must not run tests. Screenshots or a recording are
   supplementary evidence, not proof of a tested offline deployment.
7. Submit the final slides, UML source files and repository. Do not submit the
   previous draft unchanged with unknown student number or unsupported claims.

## Suggested 13-minute structure

| Time | Content |
| --- | --- |
| 0:00-1:00 | Project title, problem, intended users and benefit. |
| 1:00-2:00 | Scope, requirements, stack and ML purpose; disclose incomplete items. |
| 2:00-3:30 | Selected UML: actors, key relationships, request flow and deployment. |
| 3:30-5:00 | Evaluation evidence, privacy, limitation and personal contribution. |
| 5:00-6:00 | Administrator login and synthetic historical applications. |
| 6:00-8:30 | Capture a profile; trigger and correct one validation error. |
| 8:30-9:30 | Save, navigate away and reopen to demonstrate persistence. |
| 9:30-11:00 | Execute genuine inference if available; explain output or honest blocking condition. |
| 11:00-12:00 | Open/download the actual report; do not imply an unscored report contains ML results. |
| 12:00-13:00 | Show role isolation using prepared sessions and close with limitation/future work. |

## Evaluation evidence to prepare

For Q4.1 record actual passed, failed and unresolved counts separately for
functional, integration, system and user acceptance checks. If not executed,
write "not executed"; do not report zero failures as if the checks passed.
The prior no-tests instruction remains in force for agent work.

For Q4.2 aim to show two system/quality measures plus an ML metric, for example:

- Median and slowest observed response time over a stated number of actual
  requests, including whether Render cold-start time was included.
- Observed workflow completion or validation-check success rate, with the
  numerator, denominator, conditions and date recorded.
- Stored offline Kaggle accuracy and macro-F1 from evaluation/kaggle_native.json.
  These are benchmark metrics, not current production quality or response time.

The stored benchmark reports approximately 75.06% accuracy and 0.6718 macro-F1.
It labels itself non-deployable and incompatible with live applicant inputs.
Explain its source, split and limitations; do not use old leakage-affected
accuracy claims or imply that synthetic demo records were Kaggle data.

## Requirement-to-evidence worksheet

| Requirement | Source feature | Suggested evidence | Current evidence status |
| --- | --- | --- | --- |
| Role isolation | applicants/permissions.py | Applicant sees only linked record; Underwriter sees own; Administrator sees all | Source inspected; live demonstration pending. |
| Validated capture | applicants/models.py and forms.py | Invalid input rejected then corrected | Current live result pending. |
| Persistence | Applicant and five related models | Saved profile remains after navigation/login | Current live result pending. |
| Historical sample data | seed_presentation_data command | Demo list and real import audit entry | Prepared; not imported by agent. |
| Emerging technology | risk_engine/scoring.py and model_versions.py | Real input, executed model and persisted output | Current hosted success not established. |
| PDF output | reports module | Open actual generated report | Current live result pending. |

## Technical answers to rehearse

- Why three roles? Separate self-service visibility, underwriting work and
  system administration. UI hiding alone is insufficient; query scoping and
  server-side permissions enforce access.
- Where does Kaggle fit? Dataset-based offline evaluation. It is not currently a
  live prediction API, and the stored benchmark is not deployable on form inputs.
- Why these historical records? Clearly fictional fixtures for demonstrating
  navigation and date-based history, not evidence of real customer activity.
- What is the main ethical concern? Sensitive health/financial information,
  consent, access restrictions and the risk of treating experimental predictions
  as insurance decisions. Never display secrets or real customer data on slides.
- What did you personally contribute? Describe only work you actually performed,
  your decisions, what you learned and any assistance as required by course rules.
- Main limitation and enhancement? Explain the verified gap in compatible,
  validated hosted inference; propose properly validated input-aligned modelling
  and durable model deployment, not simply lowering thresholds.
