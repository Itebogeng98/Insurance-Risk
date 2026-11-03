"""Build Assignment 4 documents from inspected project evidence; does not run tests."""
from pathlib import Path
from xml.sax.saxutils import escape
import json

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, PageBreak, Spacer
from reportlab.pdfgen import canvas
from PIL import Image as PILImage

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
METRICS = json.loads((PROJECT / 'evaluation/kaggle_native.json').read_text())
INK, TEAL, MUTED = [colors.HexColor(v) for v in ('#183242', '#087f80', '#52616b')]
REPO = 'https://github.com/rk11machaba/Integrated-Life-Insurance-Risk-Assessment-System'
LIVE = 'https://assure-risk.onrender.com'
styles = StyleSheet1()
for name, size, leading, font, color in [
    ('Title4', 25, 30, 'Helvetica-Bold', INK),
    ('Heading4', 18, 23, 'Helvetica-Bold', INK),
    ('Sub4', 11, 15, 'Helvetica-Bold', TEAL),
    ('Body4', 10, 14, 'Helvetica', INK),
    ('Small4', 8.5, 11.5, 'Helvetica', INK),
]:
    styles.add(ParagraphStyle(name=name, fontName=font, fontSize=size, leading=leading,
                              textColor=color, spaceAfter=8))

pages = []
def section(title, blocks):
    pages.append((title, blocks))

section('1. Prototype scope and requirements', [
('h', '1.1 Title, problem, users and emerging technology'),
('p', 'Project: Integrated Life Insurance Risk Assessment System using Artificial Intelligence and Machine Learning (Assure Risk). The problem is fragmented collection and review of personal, medical, lifestyle and financial applicant information. The prototype centralises capture, validation, assessment records and report export. It supports review; it does not issue policies or automate an insurer\'s final decision.'),
('p', 'The three roles are Applicant, Underwriter and Administrator. Applicants view an explicitly linked record. Underwriters capture and review records they created. Administrators manage access and oversee all records. Machine learning is the selected emerging technology in the prior project documentation; lecturer approval is to be confirmed by the student. [R2-R4]'),
('h', '1.2 Demonstrated scope versus implementation status'),
('t', (['ID / requirement', 'Status', 'Implementation and evidence to show'], [
['FR-01 Registration and login', 'Implemented', 'Public registration creates Applicant accounts; privileged roles are administrator-assigned. E01 / TC01.'],
['FR-02 Role-based visibility', 'Implemented', 'Account-linked Applicant records; creator-owned Underwriter records; Administrator oversight. E02 / TC02.'],
['FR-03 Guided capture', 'Implemented', 'Six sections, consent and server-side validation; final transaction saves related records. E03 / TC03-04.'],
['FR-04 Search and record review', 'Implemented', 'Search by name, ID or email within the authorised queryset. E04 / TC05.'],
['FR-05 Report export', 'Implemented', 'Authorised HTML/PDF report with available assessment history. E05 / TC06.'],
['ETR-01 ML risk assessment', 'Partial', 'In-process scoring code exists; no approved model provisioned for the supplied Render configuration. E06 / TC07-08.'],
['FR-06 Model training and review', 'Partial', 'Local worker and CSV validation exist; Render uploads and activation disabled.'],
['FR-07 Live Kaggle API / policy decisions', 'Deferred / out of scope', 'Offline Kaggle evaluation only; no online synchronization, policy issuance or approval workflow.'],
], [48, 24, 98])),
('p', 'Implemented describes source-code functionality, not a claim that each feature has passed a current hosted demonstration. The evidence IDs are capture targets, not screenshots already supplied. [R3-R6]'),
])

section('2. Setup, access and security', [
('h', '1.3 Setup and access instructions'),
('p', f'Hosted address: {LIVE}<br/>Repository: {REPO}<br/>Working directory: C:\\Double One Digital\\Projects\\Integrated Life Insurance Risk Assessment System'),
('p', 'Hosted access needs a current browser and internet connection. A laptop with a keyboard and projector/display is recommended for presentation; no special sensor or GPU is required. For local preparation, use Python 3.14, the project dependencies, PostgreSQL (or the configured MySQL backend), and sufficient memory for the selected model. A 4 GB RAM laptop is a planning baseline, not a measured minimum.'),
('p', 'Local preparation: install requirements.txt in a virtual environment; configure SECRET_KEY, DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, ALLOWED_HOSTS and local DEBUG settings in a private environment file. Apply migrations and create the initial administrator using the normal management commands. Start manage.py runserver and browse the printed local address. Exact environment-specific instructions are in DEPLOYMENT.md. No setup commands were executed for this assignment pack.'),
('p', 'Render uses config.render, bash deploy/render-build.sh and bash deploy/render-start.sh. The start script runs migrations and bootstrap_render_admin before Gunicorn. Administrator creation requires all three BOOTSTRAP_ADMIN_* values for a new username; the command never resets an existing password or promotes an existing non-superuser. Remove bootstrap values after successful creation. [R5]'),
('h', 'Demonstration access'),
('p', 'Prepare three private demonstration accounts: Applicant, Underwriter and Administrator. Assign roles and verify logins before the session. Keep passwords out of this report and Git; provide any required assessment credentials privately to the lecturer. The recent live admin-login problem remains unresolved in the available conversation, so no usable hosted admin credential is claimed here.'),
('h', '2.4 Security and reliability controls'),
('p', 'Django password hashing, authenticated views, explicit ownership filters, CSRF protection for session writes, and staff/permission checks protect core actions. Record access and exports generate audit entries. Render settings enforce HTTPS and secure cookies; environment values are not committed. Applicant email matching does not establish ownership. Never grant staff status to ordinary Underwriters: this implementation treats staff as administrator-level visibility. [R3, R5-R6]'),
('p', 'Capture uses a database transaction for the Applicant and five supporting records. Invalid forms return field errors. Expected model-availability errors produce user feedback without fabricated results. This is not a claim of complete resilience: assessment, indicator and recommendation writes are not wrapped in one explicit transaction, so failure recovery and atomic scoring persistence remain corrective work. [R4, R6]'),
])

section('3. End-to-end workflow and persistent data', [
('h', '2.1 Demonstration workflow'),
('p', '1. Register an Applicant account and sign in. An Administrator verifies and assigns a separate Underwriter account; ordinary registration cannot select privileged roles.<br/>2. As Underwriter, select New Applicant. Enter Personal, Medical, Lifestyle, Salary, Vehicle Insurance and Spending sections.<br/>3. Show one invalid value, explain the error, correct it and continue. Required consent, age, identity format, medical limits and financial relationships are checked.<br/>4. Save Applicant on the final step. Reopen the record from Applicants to show persistence.<br/>5. As Administrator, verify ownership and set the record\'s Account field to the Applicant account.<br/>6. As Applicant, view the linked record and demonstrate the absence of assessment/capture privileges.<br/>7. Review/export a PDF. When an approved model exists, request an assessment and show its stored output; otherwise explicitly demonstrate the blocked branch. [R3-R6]'),
('p', 'The earlier wizard sections live in the session until final save. Starting New Applicant again resets that capture session. This is not a permanent draft feature. Applicants currently view records; they do not self-submit the six-section application.'),
('h', '2.3 Data and state'),
('p', 'The hosted configuration uses PostgreSQL. User/UserProfile hold authentication and roles. Applicant records identity, consent, creator and optional verified account link. Five one-to-one supporting models hold the domain data. RiskAssessment, FeatureContribution and Recommendation store output and history. ModelVersion stores artifact metadata and approval information. AuditLog stores selected user actions.'),
('p', 'The Account link is one-to-one: an Applicant account can be linked to at most one applicant record, with many assessments for that record. Underwriters see records they created. Refreshing/reopening a saved record should retain it because it is stored in the database, not the browser session. This behaviour is a demonstration checkpoint, not a newly observed result.'),
('h', 'Meaningful outputs and boundaries'),
('p', 'Outputs include a saved profile, authorised record list, validation messages, report PDF, and (when available) score, category, confidence and recommendations. No-assessment reports must not be presented as completed AI assessments. The regular report highlights the latest result; the assessment-specific API report selects its requested assessment.'),
('p', 'Use the explicitly fictional manual data in the presentation notes, not real applicants or production credentials. Existing screenshot artifacts from earlier browser checks contain test fixtures and are not fresh evidence of the current hosted release.'),
])

section('4. Emerging technology, measures and risks', [
('h', '2.2 Machine-learning integration'),
('p', 'The application scoring path constructs an applicant feature row, checks required sections and loads an approved joblib artifact. The schema-3 training pipeline imputes numeric missing values, scales numerics, one-hot encodes categories and fits GradientBoostingClassifier. Inference uses predict_proba; the maximum-probability class becomes the category. The score is a weighted combination of class probabilities (LOW 15, MEDIUM 50, HIGH 85), not a calibrated claim probability. [R6]'),
('p', 'Confidence below the configured threshold flags manual review. Stored rule-based indicators are separate from model attribution; they must not be described as SHAP or feature-level explanations of the model. Production requires a verified input contract and passing accuracy/macro-F1 thresholds.'),
('h', '4.2 Quantitative measures from existing evidence'),
('t', (['Measure', 'Recorded result', 'Interpretation'], [
['Native Kaggle internal-test accuracy', f"{METRICS['test_metrics']['accuracy']:.2%}", 'Below the 85% project target.'],
['Native Kaggle internal-test macro F1', f"{METRICS['test_metrics']['macro_f1']:.4f}", 'Below the 0.80 project target.'],
['HIGH-class recall', '56.06%', '737 of 2,551 HIGH examples were predicted LOW.'],
], [65, 32, 73])),
('p', 'These are recorded offline results, not new tests or hosted scoring measurements. The native benchmark retained 59,351 of 59,381 records after removing duplicate predictors, with train/validation/test sizes 35,610 / 11,870 / 11,871. It selected a balanced histogram-gradient-boosting model by validation macro F1. This is distinct from the applicant-form pipeline. [R7-R8]'),
('h', '4.3 Important limitations and corrective actions'),
('p', '<b>Risk 1: incompatible training inputs.</b> The anonymised Kaggle predictors cannot be reconstructed from the live form. Obtain authorised, labelled applicant-schema data, review provenance and validate on independent data before production approval. Do not activate the native benchmark or invent conversions.'),
('p', '<b>Risk 2: incomplete hosted AI workflow.</b> Render disables uploads and activation and has no bundled approved artifact. Prepare and rehearse a separately labelled local demonstration of valid-input inference, or provision a validated compatible model with durable storage. An offline metric table or blocked scoring request alone does not satisfy a successful end-to-end emerging-technology demonstration.'),
('p', 'Also resolve live admin access before presentation and make assessment persistence atomic. The old 93.5% accuracy claim in historical Assignment 3 text is superseded and must not be reused. [R7-R8]'),
])

section('5. Updated use-case diagram', [
('h', '3.1 Actors and prototype functions'),
('i', ('01_use_cases.png', 'Figure 1. Three-role use-case model, generated with the installed PlantUML tool.')),
('p', 'All actors use the same application but have different record scopes. Applicant registration creates only an Applicant account. Administrator-only account linking is independent of capture. Capture includes validation; assessment is a separate command because a record can exist without a score. Model availability is a precondition, not proof of an operational hosted AI feature.'),
('p', 'Source alignment: applicants/permissions.py, accounts/forms.py, applicants/views.py and risk_engine/views.py. Staff status and admin-site permissions remain additional access conditions. [R3-R6]'),
])
section('6. Workflow activity diagram', [
('h', '3.2 Decisions, alternative paths and emerging technology'),
('i', ('02_activity.png', 'Figure 2. Capture-to-report activity with invalid-input, access-denial and model-unavailable alternatives.')),
('p', 'The successful inference branch is implemented but conditional on a usable model. The current supplied hosted configuration takes the unavailable/approval-error branch. Administrator account linking is a separate workflow, not an automatic side effect of capture. [R4-R6]'),
])
section('7. Updated class diagram', [
('h', '3.3 Classes, operations and multiplicities'),
('i', ('03_classes.png', 'Figure 3. Core domain classes and actual database relationships; selected attributes shown.')),
('p', 'The five supporting records are optional at database level (0..1), but completed capture requires all five. Account ownership differs from record creation. An applicant can have many assessments. ModelVersion is referenced by a string, not a foreign key. clean() validates models; scoring is a module function. TrainingDataset and AuditLog are omitted from this core-domain view. [R3, R4, R6]'),
])
section('8. Assessment sequence diagram', [
('h', '3.4 UI, application logic, data and machine learning'),
('i', ('04_sequence.png', 'Figure 4. Authenticated assessment request, database lookup, model validation and in-process inference.')),
('p', 'The browser sends a CSRF-protected request. The view enforces visibility and role permissions before scoring. Model metadata is read from the database; joblib loads the artifact; scikit-learn produces probabilities. Saved outputs are then used by the profile and reports. This is not a network call to Kaggle or an external AI endpoint. Errors return meaningful feedback rather than an invented result. [R6]'),
])
section('9. Deployment and implementation differences', [
('h', '3.5 Prototype modules and execution environment'),
('i', ('05_deployment.png', 'Figure 5. Render runtime and separate local evaluation/training environment.')),
('p', 'This is the supplied configuration, not a remotely inspected inventory. Render has no training worker, approved model artifact or Kaggle synchronization. The local worker polls database jobs; the Celery configuration is not the active queue. Native evaluation is separate from live scoring. Docker Compose is an alternative full-stack deployment, not this topology. Durable storage, model approval and operational verification remain necessary. [R5-R8]'),
])
section('10. Verification and evidence register', [
('h', '4.1 Representative cases: expected versus actual'),
('p', 'No application tests were executed for this assignment preparation, following the student\'s instruction. The table is a current verification register, not a fabricated pass report. Existing test code specifies expected behaviour but is not fresh execution evidence. Complete the Actual/status column after authorised testing or observed rehearsal.'),
('t', (['Case', 'Action and expected result', 'Actual / status now'], [
['TC01 / FR-01', 'Register Applicant; valid data creates an account. Privileged role submission is rejected.', 'Not rerun; current hosted result pending.'],
['TC02 / FR-02', 'Applicant opens another record; access denied. Verified account link permits only its own record.', 'Not rerun; access checks inspected in source.'],
['TC03 / FR-03', 'Complete six sections and final save; record and five related sections persist.', 'Not rerun; record evidence required.'],
['TC04 / FR-03', 'Submit missing consent / invalid age / excessive claims; errors shown and no completed record saved.', 'Not rerun; field validators inspected.'],
['TC05 / FR-04', 'Reopen a saved record and search; database data retained within permitted scope.', 'Not rerun; persistence evidence required.'],
['TC06 / FR-05', 'Export authorised report; PDF has correct applicant/result. Unauthorised access denied.', 'Not rerun; actual PDF screenshot required.'],
['TC07 / ETR-01', 'In approved/local demo environment, valid feature row yields stored category, score and confidence.', 'Current successful demo not established. Must prepare before assessment.'],
['TC08 / ETR-01', 'Hosted missing/unverified model produces error, without fabricated assessment.', 'Configured to block; actual hosted feedback pending capture.'],
], [29, 88, 53])),
('p', 'Historical context: earlier development runs reported successful automated checks, but later UI changes invalidate an unchanged pass claim. In particular, accounts/test_demonstration.py still expects the removed academic banner. Update that obsolete assertion and obtain permission before rerunning. This is a source-inspection finding, not an executed failure.'),
('p', 'Evidence to add: E01 login/registration; E02 account linking and access denial; E03 validation plus final save; E04 persisted profile/search; E05 exported PDF; E06 genuine inference input/output and stored result. Use fictional records, record the environment/date/commit, and redact all credentials.'),
])
section('11. Presentation and assessment readiness', [
('h', '5.1 / 5.3 Five-minute presentation'),
('t', (['Time', 'Slide / topic', 'Key message'], [
['0:00-0:40', '1. Problem and purpose', 'One structured underwriting record instead of fragmented information.'],
['0:40-1:25', '2. Users and workflow', 'Three roles, verified account linking, six-step capture and reports.'],
['1:25-2:10', '3. Architecture', 'Django modules, PostgreSQL, Render and a separate local evaluation path.'],
['2:10-3:00', '4. Emerging technology', 'Applicant pipeline versus native Kaggle benchmark; explain observable inference.'],
['3:00-3:45', '5. Features and controls', 'Validation, authorised queries, secure credentials and report export.'],
['3:45-4:25', '6. Results', '75.06% accuracy / 0.6718 macro F1; offline targets not met.'],
['4:25-5:00', '7. Limits and next steps', 'Input compatibility, hosted model gap, admin access and fresh evidence.'],
], [25, 55, 90])),
('h', '5.2 Ten-minute live demonstration'),
('p', '0-1 min: identify environment and prepared accounts. 1-4 min: capture six sections, show one validation error, then save. 4-5 min: reopen the persistent record. 5-6 min: administrator links the verified Applicant account. 6-7 min: Applicant views its own record and cannot assess. 7-9 min: demonstrate genuine input-to-model-to-stored-output integration in the prepared compatible environment. 9-10 min: export the PDF and explain the key limitation.'),
('p', 'Fallback: keep the local environment available, plus pre-recorded demonstration and dated screenshots if permitted by the lecturer. Neither a recording nor the blocked scoring branch should be misrepresented as a successful live AI demonstration. Do not change production validation rules to make the presentation appear complete.'),
('h', '5.4 Individual understanding and readiness'),
('p', 'Be ready to explain ownership filtering, transactional capture, model preprocessing, the label definition, leakage prevention, offline evaluation, PDF selection and deployment limits. Speaker notes include answers tied to the current implementation.'),
('p', '<b>Submission gate:</b> confirm student number and approved technology; resolve admin access; prepare the valid-input AI demonstration; record at least five actual case outcomes; attach dated screenshots; review and sign declarations. This report is a preparation draft until those items are completed.'),
])

references = [
('R1', 'ISJ107V Assignment 4 S2 2026: Functional Prototype and Presentation. Supplied six-page assessment brief.'),
('R2', 'Assignment3_Consolidated_Final_Answers.md. Prior project title and technology baseline; superseded numeric claims are not reused.'),
('R3', 'accounts/forms.py; accounts/models.py; applicants/permissions.py; accounts/admin.py. Registration, roles and access rules.'),
('R4', 'applicants/views.py; applicants/forms.py; applicants/models.py. Capture, validation and relationships.'),
('R5', 'config/render.py; config/production.py; render.yaml; deploy/render-start.sh; RENDER_DEPLOYMENT.md; compose.yaml. Deployment and bootstrap.'),
('R6', 'risk_engine/pipeline.py; scoring.py; model_versions.py; api.py; models.py; reports/views.py. Inference, records and PDFs.'),
('R7', 'evaluation/kaggle_native.json; evaluation/RESULTS.md. Existing native-feature evaluation recorded 17 October 2026.'),
('R8', 'evaluation/MAPPING_AUDIT.md; evaluation/APPLICANT_DATA_CONTRACT.md. Input mapping limitations and labelled-data contract.'),
('R9', 'accounts/test_demonstration.py; applicants/tests.py; risk_engine/test_security_training.py; reports/tests.py. Test specifications, not fresh run evidence.'),
('R10', 'PlantUML. Download and Smetana layout documentation. https://plantuml.com/download and https://plantuml.com/smetana02 (accessed 30 October 2026). Diagrams rendered locally using the existing VS Code PlantUML installation.'),
('R11', 'Kaggle, Prudential Life Insurance Assessment data dictionary. https://www.kaggle.com/c/prudential-life-insurance-assessment/data/ (cited by the project mapping audit; not newly retrieved for this report).'),
]


def para(text, style='Body4'):
    return Paragraph(text, styles[style])


def make_table(spec):
    headers, rows, widths = spec
    data = [[para(escape(h), 'Small4') for h in headers]]
    data += [[para(cell, 'Small4') for cell in row] for row in rows]
    t = Table(data, colWidths=[x * mm for x in widths], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d9eeee')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f6f7')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return t


def footer(c, doc):
    c.saveState()
    c.setFillColor(TEAL)
    c.setFont('Helvetica-Bold', 8)
    c.drawString(20*mm, 285*mm, 'ASSURE RISK | ISJ107V ASSIGNMENT 4')
    c.setFillColor(MUTED)
    c.setFont('Helvetica', 8)
    c.drawString(20*mm, 12*mm, 'Preparation draft | 30 October 2026')
    c.drawRightString(190*mm, 12*mm, str(doc.page))
    c.restoreState()


def build_report():
    story = [para('Functional Prototype<br/>and Presentation', 'Title4'), Spacer(1, 8*mm),
             para('Integrated Life Insurance Risk Assessment System', 'Heading4'),
             para('Assure Risk | AI and Machine Learning'),
             para('Student: Mc Makwela (confirm full registered name)<br/>Student number: TO BE PROVIDED<br/>Module: ISJ107V | Assignment 4 | Individual assessment<br/>Prepared: 30 October 2026'),
             Spacer(1, 8*mm), para('Submission status', 'Sub4'),
             para('Preparation draft, not a claim of completed live assessment. Eleven report pages follow this cover; references and declaration appendix are excluded from that count. Replace StudentNumber in the filename after confirmation.'),
             para('The brief states Question 1 is 9 marks, while its rubric and marker summary use 6 marks. The 50-mark total is consistent with 6. All Question 1 subquestions are addressed; ask the lecturer which weighting applies.'),
             para('The brief places presentations from 3 October 2026. Confirm your allocated session with the lecturer; this pack does not infer a new deadline.'),
             para('Contents', 'Sub4')]
    story.append(para('<br/>'.join(f'{n+2}. {title}' for n,(title,_) in enumerate(pages)), 'Small4'))
    markdown = ['# ISJ107V Assignment 4 - Preparation Draft', '', 'Student: Mc Makwela (confirm)', 'Student number: TO BE PROVIDED', '']
    for title, blocks in pages:
        story += [PageBreak(), para(title, 'Heading4')]
        markdown += ['', '## '+title, '']
        for kind, value in blocks:
            if kind in ('h', 'p'):
                story.append(para(value, 'Sub4' if kind=='h' else 'Body4'))
                markdown += [('### ' if kind=='h' else '')+value, '']
            elif kind == 't':
                story.extend([make_table(value), Spacer(1, 3*mm)])
                heads, rows, _ = value
                markdown += ['| '+' | '.join(heads)+' |', '| '+' | '.join(['---']*len(heads))+' |']
                markdown += ['| '+' | '.join(row)+' |' for row in rows]
            else:
                filename, caption = value
                path = ROOT / 'uml' / filename
                width,height = PILImage.open(path).size
                ratio = min(170*mm/width, 172*mm/height)
                story += [Image(str(path), width=width*ratio, height=height*ratio), Spacer(1, 3*mm), para(caption, 'Small4'), Spacer(1, 4*mm)]
                markdown += [f'![{caption}](uml/{filename})', '']
    story += [PageBreak(), para('References and evidence sources', 'Heading4')]
    markdown += ['## References', '']
    for key, value in references:
        story.append(para(f'<b>[{key}]</b> {escape(value)}', 'Small4'))
        story.append(Spacer(1, 3*mm))
        markdown.append(f'[{key}] {value}')
    story += [PageBreak(), para('Appendix: declarations and evidence gate', 'Heading4'),
              para('Declaration of original work - unsigned draft', 'Sub4'),
              para('I confirm that the submitted project and report accurately represent my own contribution, that external sources and assistance are acknowledged, and that I can explain the design, code, evidence and limitations. I have not represented unperformed tests, fabricated screenshots or another environment\'s outputs as current live results.'),
              para('Student must review this declaration, amend it to match actual contributions and institutional policy, and sign it personally. No signature or originality certification is supplied by this document generator.'),
              para('AI-tool use declaration - review before submission', 'Sub4'),
              para('An OpenAI coding assistant assisted with project source review, report drafting, UML source generation, slide preparation and speaker notes. PlantUML rendered the diagrams and ReportLab generated the PDFs. The student must verify all content, disclose any additional AI-assisted code work, and confirm that this use is permitted by the lecturer. Permission has not been assumed or certified.'),
              para('Student name: __________________________<br/>Student number: ________________________<br/>Signature: ______________________________<br/>Date: __________________________________'),
              para('Evidence required before submission', 'Sub4'),
              para('Confirm identity and approved technology; resolve administrator login; prepare genuine local or approved hosted inference; capture E01-E06; complete actual results for at least five cases; rehearse five-minute talk and ten-minute demo; remove draft markers only after verification. No passwords should appear in the public report.'),
              para('Read presentation_notes.md for the timed script, fictional manual sample, technical questions and fallback procedure. The slide PDF is Assignment4_Presentation_Slides.pdf; editable slide content is in this builder and in the notes.')]
    document = SimpleDocTemplate(str(ROOT/'ISJ107V_Assignment 4_StudentNumber.pdf'), pagesize=A4,
                                 leftMargin=20*mm, rightMargin=20*mm, topMargin=23*mm, bottomMargin=21*mm,
                                 title='ISJ107V Assignment 4 - Assure Risk Prototype', author='Mc Makwela (draft)')
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    (ROOT/'Assignment4_Report_Source.md').write_text('\n'.join(markdown), encoding='utf-8')


slides = [
('Assure Risk', 'Integrated Life Insurance Risk Assessment System', [
    'Problem: applicant information is fragmented across review activities.',
    'Purpose: structured capture, authorised review and consistent reporting.',
    'Technology: supervised machine learning for risk classification.',
], '0:00-0:40'),
('Three roles. One record workflow.', 'Applicant | Underwriter | Administrator', [
    'Applicant: view only the account-linked record and reports.',
    'Underwriter: capture six sections and review records they created.',
    'Administrator: verify access, link accounts and oversee records.',
    'Capture > Validate > Persist > Assess when available > Export.',
], '0:40-1:25'),
('Architecture', 'Web application and local research are separate', [
    'Render: Gunicorn + Django + PostgreSQL; WhiteNoise serves assets.',
    'Modules: accounts, applicants, risk_engine, reports and etl.',
    'Inference: in-process joblib / scikit-learn, not a Kaggle API call.',
    'Local evaluation produces evidence; it does not deploy a model.',
], '1:25-2:10'),
('Machine learning integration', 'Valid input must produce an observable system result', [
    'Applicant pipeline: imputation, scaling, encoding, gradient boosting.',
    'Probabilities produce category, score, confidence and review flag.',
    'Indicators are rule-based, not model feature attribution.',
    'Hosted success path is blocked until a compatible model is approved.',
], '2:10-3:00'),
('Prototype features and controls', 'Show behaviour, not only screens', [
    'Six-step capture with consent and cross-field validation.',
    'Account-linked access; Underwriters cannot browse others\' records.',
    'Persistent profiles, assessment history and PDF reports.',
    'CSRF, hashed passwords, private secrets and audit entries.',
], '3:00-3:45'),
('Recorded results', 'Native Kaggle benchmark - not live applicant scoring', [
    'Accuracy: 75.06% (target 85%).',
    'Macro F1: 0.6718 (target 0.80).',
    '11,871 internal test records; HIGH recall 56.06%.',
    'Current deployment checks remain pending; no new tests run.',
], '3:45-4:25'),
('Limitations and next steps', 'Honest evidence and a reliable demonstration', [
    'Obtain verified labelled data matching live applicant inputs.',
    'Resolve admin access and prepare genuine inference evidence.',
    'Complete actual test outcomes and rehearse the full workflow.',
    'Keep a local fallback; never present a blocked result as AI success.',
], '4:25-5:00'),
]


def build_slides():
    c = canvas.Canvas(str(ROOT/'Assignment4_Presentation_Slides.pdf'), pagesize=(960, 540))
    c.setTitle('Assure Risk - Assignment 4 Prototype Presentation')
    for number, (title, subtitle, bullets, timing) in enumerate(slides, 1):
        c.setFillColor(colors.HexColor('#f5f8fa')); c.rect(0,0,960,540,fill=1,stroke=0)
        c.setFillColor(TEAL); c.rect(0,0,12,540,fill=1,stroke=0)
        c.setFont('Helvetica-Bold', 12); c.drawString(46,500,'ISJ107V | ASSIGNMENT 4 | MC MAKWELA (CONFIRM NAME)')
        for text, y, size, font in [(title,437,32,'Helvetica-Bold'),(subtitle,393,17,'Helvetica')]:
            c.setFillColor(INK); c.setFont(font,size); c.drawString(46,y,text)
        y = 330
        for text in bullets:
            s = ParagraphStyle('slide', fontName='Helvetica', fontSize=21, leading=29, textColor=INK)
            block = Paragraph(escape(text), s)
            _,h = block.wrap(845, 100)
            block.drawOn(c, 58, y-h)
            c.setFillColor(TEAL); c.circle(46,y-12,3,fill=1,stroke=0)
            y -= h + 19
        c.setFillColor(MUTED); c.setFont('Helvetica',11)
        c.drawString(46,24,f'{timing} | Preparation draft - replace pending evidence before assessment')
        c.drawRightString(915,24,f'{number} / {len(slides)}')
        c.showPage()
    c.save()


if __name__ == '__main__':
    build_report()
    build_slides()
    print('Report, editable report source and presentation PDF generated in', ROOT)
