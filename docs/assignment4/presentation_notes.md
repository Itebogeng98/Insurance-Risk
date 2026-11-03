# Assignment 4: Presentation and Live Demonstration Notes

Project: Integrated Life Insurance Risk Assessment System (Assure Risk).
Workspace: `C:\Double One Digital\Projects\Integrated Life Insurance Risk Assessment System`.
Student: Mc Makwela, subject to confirmation. Student number: REQUIRED.
Status: preparation draft. Do not describe unperformed tests or blocked scoring as successful evidence.

## Five-Minute Presentation

### Slide 1 | 0:00-0:40 | Problem and purpose

My project is Assure Risk, an integrated life insurance risk assessment system. It addresses fragmented applicant information and repeated manual review. Instead of keeping medical, financial and lifestyle information separately, the system stores a structured applicant record, validates it and supports report generation. The emerging technology is supervised machine learning. The prototype is decision support, not an automatic policy approval or insurance pricing service.

### Slide 2 | 0:40-1:25 | Users and workflow

There are three roles. Applicants register publicly and can view only the record explicitly linked to their account. Underwriters capture records and review the records they created. Administrators manage roles, verify account links and oversee records. Registration and application capture are different processes. The main workflow moves through six capture sections, validation, database persistence, assessment when a compatible model is available, and PDF export. Changing an email address does not transfer access to another person's record.

### Slide 3 | 1:25-2:10 | Architecture

The application uses Django modules for accounts, applicants, the risk engine, reports and data preparation. The Render configuration runs Gunicorn and Django with PostgreSQL, while WhiteNoise serves static files. ReportLab generates PDFs. Machine-learning inference is an in-process call to a loaded model, not a request to Kaggle. Local Kaggle evaluation is a separate research workflow that writes evaluation evidence. The diagram deliberately separates that environment from the hosted service.

### Slide 4 | 2:10-3:00 | Emerging technology

The applicant-shaped training pipeline imputes missing numeric values, scales numeric inputs, encodes categories and fits a gradient boosting classifier. During inference, probabilities produce a risk category, score and confidence. Low confidence triggers manual review. The stored indicators are rule-based and should not be confused with explanations of the classifier's internal reasoning. The current hosted configuration requires an approved input contract and passing metrics. It does not currently include an approved scoring artifact, so I must demonstrate the actual successful inference branch in a prepared compatible environment rather than claim that the blocked hosted path is successful.

### Slide 5 | 3:00-3:45 | Features and controls

The prototype includes account registration, role-based visibility, guided capture, input validation, database-backed profiles, report export and audit entries. Validation includes consent, adult age limits, identity format and relationships between financial or vehicle values. Security uses hashed passwords, session authentication, CSRF checks and ownership-filtered queries. Secrets remain outside Git. Capture saves the related records in a transaction. Further reliability work is needed to make the separate assessment-output writes atomic.

### Slide 6 | 3:45-4:25 | Recorded results

The recorded native Kaggle benchmark achieved 75.06 percent accuracy and a macro F1 of 0.6718 on 11,871 internal test records. These results miss the project targets of 85 percent accuracy and 0.80 macro F1. HIGH-class recall is only 56.06 percent. These are research results, not the accuracy of the live applicant form. The anonymised Kaggle input schema cannot be reliably reconstructed from our form. No new application tests were run while preparing this assignment, so the current evidence register identifies outcomes still needing confirmation.

### Slide 7 | 4:25-5:00 | Limits and next steps

The highest-priority improvement is obtaining authorised labelled data that matches the live inputs, followed by independent validation. Before assessment, I must also confirm administrator access, rehearse genuine model integration and record current test outcomes. I will use fictional data and have a local fallback ready. I will not remove approval safeguards or claim that a static metric table demonstrates a successful live AI workflow. The next part shows the implemented user journey and clearly identifies its present boundaries.

## Ten-Minute Demonstration Runbook

Do not spend the assessment debugging account creation, installing packages or training a large model.

| Time | Account / action | Observable evidence |
| --- | --- | --- |
| 0:00-1:00 | Identify environment; show prepared account roles | Correct site, existing verified accounts and expected navigation |
| 1:00-2:00 | Underwriter begins personal capture | Required fields and consent; show one intentional invalid value |
| 2:00-4:00 | Correct input; complete medical, lifestyle, salary, vehicle and spending | Validation feedback followed by successful final save |
| 4:00-5:00 | Reopen profile from Applicants/search | Saved data persists and is visible to its creator |
| 5:00-6:00 | Administrator verifies and links Account | Correct user attached to correct applicant record |
| 6:00-7:00 | Applicant opens own record | Read-only access; no Run Risk Assessment action; another record denied |
| 7:00-9:00 | Underwriter performs genuine inference in prepared compatible environment | Valid input, loaded model version, probabilities/output and persisted assessment |
| 9:00-10:00 | Open report and export PDF | Correct record, assessment date/model reference and readable report |

If the hosted environment still has no approved model, show its blocked state honestly. That demonstrates safe error handling, not successful emerging-technology integration. A separately prepared local demonstration must be clearly identified as local and experimental, never as the production-approved Kaggle model. Obtain lecturer guidance if a simulated training source is to be used. Do not switch off production safeguards for the presentation.

## Fictional Manual Capture Data

These values are a script for manual entry into an isolated demonstration environment. They have NOT been inserted into any database. The identity and phone values are artificial formatting examples, not verified government identities or contact details. Never send messages to them.

| Section | Values |
| --- | --- |
| Personal | First name: Demo; last name: Applicant; DOB: 1990-01-01; gender: Other; national ID: 0000000000001; email: demo.applicant@example.test; phone: 0000000000; address: 1 Fictional Demo Street; consent: checked |
| Medical | Height 170 cm; weight 75 kg; blood pressure 120/80; chronic illness: no; family history: no; optional medication/surgery descriptions blank |
| Lifestyle | Non-smoker; alcohol: None; exercise: 3 days/week; occupation: Office Worker; occupation risk: Low |
| Salary | Employment: Employed; employer: Fictional Demo Company; income: 20000; years employed: 5 |
| Vehicle | Insurance: no; insurer blank; years licensed: 10; accidents: 0; claims: 0; violations: 0 |
| Spending | Expenses: 12000; savings: 3000; debt: 10000; credit score: 700 |

For the invalid-input example, use claims = 1 with accidents = 0, then correct claims to 0. Do not predict a particular ML class from these example values: record the actual result from the model being demonstrated. A repeated rehearsal needs a fresh ID/email or a separate clean demo database to avoid duplicate errors. Do not delete production records to prepare a rehearsal.

## Account and Access Preparation

Prepare three distinct usernames and separate browser profiles or private sessions. Suggested labels are `presentation-applicant`, `presentation-underwriter` and `presentation-admin`; these are proposed names, NOT provisioned credentials. Create unique private passwords and disclose any required assessment access only through the lecturer's approved channel.

The Applicant starts with public registration. An existing authorised administrator assigns the Underwriter role and keeps staff/superuser flags off. Administration-site access requires staff status and suitable permissions; a role label alone is insufficient. Use the project's bootstrap procedure only for initial administrator creation. It does not reset existing passwords or promote an existing account. Resolve the reported hosted login problem before the session.

## Fallback Plan

1. Confirm the lecturer's presentation time and permitted fallback format.
2. Prepare the local application and its separate demonstration database/model before arriving. Confirm there are no real personal records in the demonstration.
3. Keep a dated screen recording and screenshots showing the complete successful workflow, including input, inference and persisted output, if the lecturer permits these as fallback evidence.
4. Keep the searchable report PDF, slide PDF, UML images and source files offline.
5. If internet access fails, state the problem and move to the prepared local environment. Do not pretend that a recording or local result came from the live Render instance.
6. If inference cannot be demonstrated, report the limitation and accept that Q2.2/Q5.2 remain incomplete. Stored benchmark metrics are not a substitute for integrated observable inference.

## Technical Questions and Defensible Answers

**Why three roles?** Applicant privacy, Underwriter capture/review responsibilities, and Administrator access management are separate. Querysets enforce record ownership rather than relying only on hiding buttons.

**Can an Applicant register as Administrator?** No. The public form offers only Applicant. An authorised administrator assigns privileged roles after identity verification.

**How is a record linked to an Applicant?** An Administrator sets the explicit one-to-one Account field after verification. Matching an email does not grant access.

**Why use a relational database?** Applicant sections, accounts and assessment history have explicit relationships and constraints. Transactions protect the six-section capture save. PostgreSQL is the supplied hosted configuration.

**What algorithm is actually used?** The applicant-form pipeline uses GradientBoostingClassifier. The separate native Kaggle benchmark selected a balanced histogram gradient boosting model. These are different models and must not be conflated.

**What does the score mean?** The code combines class probabilities using weights 15, 50 and 85 for LOW, MEDIUM and HIGH. This is a project risk summary, not a calibrated probability of death, a claim or policy approval.

**How do you explain predictions?** The application stores rule-based indicators and recommendations. It does not implement SHAP attribution. Do not claim the indicators explain exactly how the classifier made its decision.

**How did you avoid target leakage in the native benchmark?** Id and Response are excluded from predictor columns. Duplicate predictor rows are removed before splitting. Preprocessing is fitted inside the pipeline; validation is used for model selection. The test split is internal because the dataset had already been explored in previous work.

**Is Kaggle an API used by the live application?** No. Existing evaluation uses downloaded Prudential data. No current web-to-Kaggle synchronization or inference API exists.

**Why not deploy the highest-scoring benchmark?** The anonymised native predictors do not match the live form; its accuracy and macro F1 also miss the targets. Input compatibility and provenance matter as much as a numeric score.

**What remains unreliable?** Hosted model availability and administrator login need resolution. Assessment-related writes need one transaction for all-or-nothing persistence. Fresh regression evidence is pending; an old test still asserts a removed UI banner.

**What did you personally implement?** Answer from your actual contribution, not a memorised claim. Explain the code you understand, identify assistance and disclose AI use according to the lecturer's rules.

## Final Submission Checklist

- Confirm full registered name, student number and the lecturer's approved technology.
- Clarify Q1 weighting: question says 9; rubric says 6; total 50 uses 6.
- Complete the Actual/status cells for at least five representative cases with dated evidence.
- Attach E01-E06 screenshots or evidence references from the actual environment used.
- Rehearse a genuine successful inference demonstration, not only the unavailable-model error.
- Review all declarations and personally sign only statements that are true.
- Rename the report to `ISJ107V_Assignment 4_<your student number>.pdf`.
- Submit the searchable report PDF and presentation slides through Brightspace/MyTUTor as instructed.
- Do not submit credentials, `.env` files, raw sensitive records or unsupported old performance claims.
