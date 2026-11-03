"""Generate the user guide without starting the application or accessing its database."""

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak


OUTPUT = Path(__file__).resolve().parent / 'Assure_Risk_System_and_User_Guide.pdf'
INK = colors.HexColor('#183242')
TEAL = colors.HexColor('#087f80')
PALE = colors.HexColor('#edf6f6')
GRAY = colors.HexColor('#52616b')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='GuideTitle', fontName='Helvetica-Bold', fontSize=26, leading=31, textColor=INK, spaceAfter=12))
styles.add(ParagraphStyle(name='GuideHeading', fontName='Helvetica-Bold', fontSize=17, leading=22, textColor=INK, spaceAfter=12))
styles.add(ParagraphStyle(name='GuideSubheading', fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=TEAL, spaceBefore=11, spaceAfter=5))
styles.add(ParagraphStyle(name='GuideBody', fontName='Helvetica', fontSize=10, leading=14, textColor=INK, spaceAfter=7))
styles.add(ParagraphStyle(name='GuideSmall', parent=styles['GuideBody'], fontSize=8.5, leading=11, spaceAfter=0))
styles.add(ParagraphStyle(name='GuideCellHead', parent=styles['GuideSmall'], fontName='Helvetica-Bold', textColor=colors.white))
story = []


def p(text, style='GuideBody'):
    return Paragraph(text, styles[style])


def body(text):
    story.append(p(text))


def heading(text):
    story.append(p(text, 'GuideSubheading'))


def page(number, title):
    if story:
        story.append(PageBreak())
    story.append(p(f'USER GUIDE / {number:02d}', 'GuideSubheading'))
    story.append(p(title, 'GuideHeading'))


def steps(items):
    for number, text in enumerate(items, 1):
        body(f'<b>{number}.</b> {text}')


def table(headers, rows, widths):
    data = [[p(escape(value), 'GuideCellHead') for value in headers]]
    data.extend([[p(value, 'GuideSmall') for value in row] for row in rows])
    block = Table(data, colWidths=[width * mm for width in widths], repeatRows=1, hAlign='LEFT')
    block.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PALE]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, -1), (-1, -1), .5, colors.HexColor('#d5e1e5')),
    ]))
    story.extend([block, Spacer(1, 6 * mm)])


page(1, 'System overview')
story.append(p('Assure Risk', 'GuideTitle'))
body('<b>Integrated Life Insurance Risk Assessment System</b><br/>Registration, access and day-to-day use for Applicant, Underwriter and Administrator.')
body('Version 1.0 | 24 October 2026 | Based on the current project code and Render configuration. The live deployment may differ until the latest changes are published.')
heading('What the system does')
body('Assure Risk brings applicant identity, medical history, lifestyle, employment, vehicle insurance and spending information into one record. Authorised users can review that record, view available risk assessments and export an underwriting PDF. Assessment history and activity logs support review and traceability.')
body('It is a decision-support system, not a policy purchase or automatic approval service. Registration does not create an insurance policy, approve an application or generate a risk score.')
heading('The three roles')
table(['Role', 'Main responsibility', 'Record visibility'], [
    ['Applicant', 'View their linked application record and available results; maintain account contact details.', 'Only the record explicitly linked to their account.'],
    ['Underwriter', 'Capture applicant information, review their records, and request assessments when an approved model is available.', 'Records they created.'],
    ['Administrator', 'Manage access, link accounts to records, oversee records and review model information.', 'All applicant records. Admin-site actions also require staff status and appropriate permissions.'],
], [29, 78, 63])
heading('How the workflow fits together')
body('<b>Register account</b> &gt; <b>Underwriter captures six sections</b> &gt; <b>Administrator verifies and links the account</b> &gt; <b>Review or assess when available</b> &gt; <b>View/export the report</b>. Linking and assessment are separate actions; neither happens automatically at registration.')
heading('Find your instructions')
body('2. Registration and account access<br/>3. Applicant guide<br/>4. Underwriter: capturing an application<br/>5. Underwriter: assessment and reports<br/>6. Administrator: users and access<br/>7. Administrator: records and models<br/>8. Troubleshooting and quick reference')

page(2, 'Registration and account access')
heading('Register a new account')
steps([
    'Open the hosted website address supplied by the system owner. Select <b>Create Account</b>, <b>Open Workspace</b> or <b>Register</b>. These lead to the registration page.',
    'Enter a unique <b>Username</b> and a valid <b>Email</b> address. Keep a record of your username: sign-in uses the username, not the email address.',
    'Use the <b>Applicant</b> role offered by the registration form. Public registration cannot create an Underwriter or Administrator account.',
    'Enter and confirm a strong password. Correct any validation messages and ensure both password fields match.',
    'Select <b>Register</b>. After a successful registration, the system signs you in and opens your dashboard.',
])
body('<b>Need staff access?</b> Register normally and ask an authorised Administrator to verify your identity and assign the appropriate role. Do not share accounts or attempt to change a role through a request or URL.')
heading('Sign in and sign out')
steps([
    'Select <b>Log In</b>, enter your username and password, and submit the form.',
    'Use the sidebar on a desktop. On a phone or tablet, open the menu button at the top left. Available links depend on your access.',
    'To leave the system, open the account menu at the top right and select <b>Logout</b>, especially on a shared computer.',
])
heading('Update your account details')
body('Open <b>Profile</b>, update your first name, last name or email, then select <b>Save Profile</b>. This edits your login account details. It does not update the separate applicant medical/financial record, change your role, or link an application to you.')
heading('Change your password')
body('Open the account menu and select <b>Change Password</b>. Enter the current password, then the new password twice and submit. If you cannot sign in or have forgotten the password, contact your Administrator through your organisation\'s established channel. There is no self-service email password-reset workflow in the current application.')
heading('Account versus application')
body('An <b>account</b> is your username, password and role. An <b>applicant record</b> contains underwriting information and assessment history. Creating an account does not create or claim an applicant record, even when the email addresses match.')

page(3, 'Applicant: view your own application')
heading('Your access')
body('Applicants can view only the applicant record explicitly linked to their account, together with its available assessments, recommendations and reports. The current data model supports one linked applicant record per account, with multiple assessments possible for that record. It is not a multi-policy application portal.')
heading('Before your record becomes visible')
steps([
    'Register and sign in using the steps on page 2.',
    'Provide the required application information and consent to your assigned Underwriter through the agreed process. Applicants do not enter the six-section capture workflow themselves in the current system.',
    'Ask the Administrator to verify your identity and link your account to the correct record. An email match alone is not sufficient.',
    'Return to <b>Applicants</b> or refresh the page after linking. If no record is visible, ask the Administrator to check the account link.',
])
heading('Review your information and reports')
steps([
    'Open <b>Applicants</b> and select <b>View</b> on your record. Only records you are authorised to see are listed.',
    'Review contact information, medical and lifestyle details, salary, vehicle history and spending information. Report errors to the Underwriter or Administrator; the Applicant role cannot edit these underwriting details.',
    'Review the risk category, score, confidence, recommendations and assessment history if an assessment exists. <b>Not assessed yet</b> means no result is available; it does not mean approval or rejection.',
    'Select <b>Report</b> for the report page. Select <b>PDF</b> on the record or <b>Export PDF</b> on the report to download a copy. A report may show that no assessment has been completed.',
])
heading('What Applicants cannot do')
body('Applicants cannot see other applicants\' records, create underwriting records, run risk assessments, upload training datasets, activate models, assign roles or use the administration site. Editing your account email does not grant access to another person\'s record.')
heading('Handling a downloaded report')
body('Reports can contain identity, medical and financial information. Store them securely and share them only with authorised recipients. Do not post reports or screenshots containing personal information in public repositories or public messages.')

page(4, 'Underwriter: capture an application')
heading('Getting access')
body('An Administrator must assign the <b>Underwriter</b> role after verification. Once signed in, use <b>New Applicant</b> to start capture. Underwriters can see records they created, not all records belonging to other Underwriters.')
heading('Complete the six sections')
table(['Step', 'Information to capture', 'Key checks'], [
    ['1. Personal', 'Names, date of birth, gender, national ID, email, phone, address and consent.', 'Age 18-75; ID is 13 digits; consent is required. This format check is not external identity verification.'],
    ['2. Medical', 'Height, weight, blood pressure where available, chronic illness, family history, medication and surgery details.', 'Height in cm; weight in kg. Details are required when chronic illness or family history is selected.'],
    ['3. Lifestyle', 'Smoking, alcohol consumption, exercise days, occupation and occupation risk.', 'Exercise is 0-7 days per week. Select accurate options rather than guessing.'],
    ['4. Salary', 'Employment status, employer/business name, monthly income and years employed.', 'Employer/business name is required when employed or self-employed. Unemployed income must be 0 in this implementation.'],
    ['5. Vehicle', 'Insurance status, insurer, years licensed, accidents, claims and traffic violations.', 'Claims cannot exceed recorded accidents. Insurer is required when insured and blank when not insured.'],
    ['6. Spending', 'Monthly expenses, savings, total debt and credit score when available.', 'Use non-negative amounts; credit score, if entered, must be 300-850. Expenses cannot exceed three times income.'],
], [27, 77, 66])
heading('Save and continue')
body('Fields marked with an asterisk are required. After each section, select <b>Save and Continue</b>. Correct field-level errors before moving on. Use <b>Back</b> or an available completed step to review earlier entries. On the final section, select <b>Save Applicant</b>.')
body('The earlier steps are held in your session; the complete applicant record is created only after the final save succeeds. This is not a permanent draft system. Starting <b>New Applicant</b> again resets the capture session, so finish the current record before starting another.')
heading('After saving')
body('Review the saved profile for accuracy. Ask an Administrator to link the Applicant\'s account when access is required. The normal Underwriter interface does not provide an edit-existing-record workflow; request corrections through an authorised Administrator rather than creating duplicate records.')

page(5, 'Underwriter: assessment and reports')
heading('Locate and review a record')
steps([
    'Open <b>Applicants</b>. Search by name, national ID or email; select <b>Search</b>, then <b>View</b> on the correct record. Use <b>Clear</b> to remove a search.',
    'Check that the identity and all five supporting sections are complete. Resolve inaccurate or missing information before requesting an assessment.',
    'When an approved model is available, select <b>Run Risk Assessment</b>. A successful run stores an assessment and its recommendations. It does not issue a policy or record a formal underwriting approval.',
])
heading('Understand the result')
table(['Item', 'Meaning'], [
    ['Risk score', 'A numerical summary on a 0-100 scale; higher scores indicate greater model-estimated risk. It is not an insurance premium or a calibrated probability of a claim.'],
    ['Risk category', 'The model classification: LOW, MEDIUM or HIGH. Review it with the applicant information.'],
    ['Confidence', 'The model\'s confidence in its classification. For example, 0.720 represents 72% model confidence, not 72% certainty of a real-world event.'],
    ['Manual review', 'Flags a result needing review, based on the configured confidence threshold. It is not an approval/rejection status.'],
    ['Rule-based indicators', 'Indicators calculated from applicant information. They are not an explanation of the model\'s internal feature attribution.'],
    ['Recommendations and history', 'Suggested improvements and previous assessment records. History identifies when a result was generated and the model version used.'],
], [41, 129])
heading('View and export')
body('Select <b>Report</b> on the applicant profile, then <b>Export PDF</b>, or use the profile\'s <b>PDF</b> button. The standard report highlights the latest assessment and includes available history. Check the applicant identity and assessment date before sharing it.')
heading('Current hosted configuration')
body('The supplied Render configuration does not bundle an approved model and does not enable online training or activation. New scoring remains unavailable until an approved, compatible model and its artifact are provisioned. An unavailable-model message is not an applicant result. Do not invent a score, bypass the approval checks or repeatedly resubmit the assessment.')

page(6, 'Administrator: users and access')
heading('Initial administrator account')
body('The deployment owner provisions the first Administrator; it cannot be selected during public registration. The project provides a one-time bootstrap command using BOOTSTRAP_ADMIN_USERNAME, BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD. These are configured by the deployment owner, not entered into the public registration page. Remove the bootstrap values after creation. See RENDER_DEPLOYMENT.md for operator instructions.')
heading('Assign an Underwriter role')
steps([
    'Ask the intended staff member to register an account, then verify the person and the access request.',
    'Sign in to <b>Admin</b> (the administration site). Open <b>User profiles</b> under Accounts and find the correct username.',
    'Change <b>Role</b> to <b>Underwriter</b> and save. Ask the user to refresh or sign in again.',
    'Leave the user\'s <b>Staff status</b> and <b>Superuser status</b> off. In this implementation, staff status grants administrator-level visibility in the application; it is not an ordinary employee flag.',
])
heading('Assign Administrator access carefully')
body('Set the verified user\'s profile role to <b>Administrator</b> for application-level administration. To use the Django administration site, the user also needs <b>Staff status</b> and suitable permissions. An Administrator role alone does not grant access to that site. A superuser has unrestricted permissions and should be reserved for trusted system operators.')
body('Use the Users page to grant only the permissions required for account, profile, applicant and audit management. Do not give ordinary Applicants or Underwriters staff status or permission to change users, roles or applicant ownership.')
heading('Maintain accounts')
body('In the Users administration page, authorised administrators can update account information, reset a forgotten password and deactivate a user by clearing <b>Active</b>. Verify identity before a password reset and communicate access details through an approved private channel. Prefer deactivation to deletion when retaining audit history is important.')
heading('Responsibility for access')
body('Check both the profile role and the account\'s staff/superuser flags when investigating unexpected access. Role changes and account links should follow an explicit verification process. The system does not verify a person\'s real identity simply because they registered with an email address.')

page(7, 'Administrator: records and models')
heading('Link an application to its Applicant account')
steps([
    'Confirm that the Applicant has registered and that an Underwriter has saved the correct applicant record.',
    'Verify the account holder\'s identity and authority to view the record. Do not rely solely on matching names or email addresses.',
    'In <b>Admin</b>, open <b>Applicants</b> and select the correct record. Find the <b>Account</b> field and select the verified user account.',
    'Save the record. Ask the Applicant to sign in and open <b>Applicants</b>. The linked record and its reports should now be visible.',
])
body('The Account field is a one-to-one link: one account cannot be attached to several applicant records. A record without an account link remains invisible to Applicant users. Changing an email address is not a substitute for updating this link.')
heading('Review and correct records')
body('Administrators can review all applicant records. With the appropriate admin-site permissions, they can correct applicant details and the medical, lifestyle, salary, vehicle and spending sections. Check related values together. If source data changes, existing assessments remain historical snapshots; a new assessment is required when scoring is available.')
heading('Review activity')
body('Open <b>Audit logs</b> under Accounts to review recorded activity such as sign-ins, record access, changes, assessments and report exports. Use the filters and search to find relevant entries. Do not assume that every possible admin-site action is recorded in the application\'s custom audit log; Django also has its own admin action history.')
heading('Model Management')
body('Open <b>Model Management</b> to review stored model versions, metrics and dataset history. In the supplied Render configuration, dataset uploads, training and activation are disabled. The page is for reviewing available information; it does not mean a model is active or approved.')
body('On a separately configured environment with durable storage and a training worker, administrators can upload a supported CSV, review the queued training outcome and consider activation. Uploading is not immediate training, and a trained candidate is not automatically approved. Production also checks model metrics and compatibility with live applicant inputs.')
heading('Kaggle and deployment responsibilities')
body('Kaggle is used in the project\'s offline evaluation work. The hosted web workflow does not fetch a live risk score from Kaggle or automatically synchronise Kaggle data. The deployment owner manages database availability, backups, secrets and any future model provisioning outside the normal Applicant workflow.')

page(8, 'Troubleshooting and quick reference')
table(['What you see', 'What to do'], [
    ['No application listed', 'Applicant: ask an Administrator to verify the Account link. Underwriter: confirm that you created the record. Registration alone does not create an application.'],
    ['Access denied or record not found', 'Check the account and role you signed in with. A direct link does not bypass ownership restrictions. Ask the Administrator to review access.'],
    ['Validation message during capture', 'Correct the highlighted field and resubmit the current step. Check units, required details, consent and relationships such as claims versus accidents.'],
    ['Not assessed yet', 'The record exists but no assessment has been stored. Ask the Underwriter whether scoring is available. This is not an application decision.'],
    ['Model unavailable or not approved', 'Refer the issue to the Administrator. The current Render configuration cannot train or activate a model through the web interface.'],
    ['Training unavailable', 'This is an intentional restriction in the supplied Render configuration, not a permission Applicants can request for themselves.'],
    ['Forgotten password', 'Contact an authorised Administrator for identity verification and reset. There is no public email-reset page in the current system.'],
    ['PDF contains no score', 'A PDF can be generated before assessment. Review the no-assessment message and confirm that a valid result exists before treating it as an assessed report.'],
], [47, 123])
heading('Using a phone or tablet')
body('Open the top-left menu for navigation and the top-right account menu for profile, password and logout actions. Forms stack vertically on small screens. Wide data tables scroll horizontally within their own area; swipe inside the table to see additional columns.')
heading('Useful page addresses')
body('Add these paths to the website address supplied by the system owner:<br/><b>/accounts/register/</b> - Registration<br/><b>/accounts/login/</b> - Sign in<br/><b>/accounts/dashboard/</b> - Dashboard<br/><b>/accounts/profile/</b> - Account profile<br/><b>/accounts/password/</b> - Change password<br/><b>/admin/</b> - Authorised administration')
heading('Before you finish')
body('Confirm you worked on the correct applicant, save the current task, store exported reports securely and log out. For assistance, use your organisation\'s verified support channel; this guide does not invent a support email address or telephone number.')


def decorate(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#d5e1e5'))
    canvas.line(20 * mm, 281 * mm, 190 * mm, 281 * mm)
    canvas.setFillColor(TEAL)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawString(20 * mm, 285 * mm, 'ASSURE RISK')
    canvas.setFillColor(GRAY)
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(190 * mm, 285 * mm, 'SYSTEM AND USER GUIDE')
    canvas.line(20 * mm, 17 * mm, 190 * mm, 17 * mm)
    canvas.drawString(20 * mm, 12 * mm, 'Version 1.0 | 24 October 2026')
    canvas.drawRightString(190 * mm, 12 * mm, f'Page {doc.page}')
    canvas.restoreState()


if __name__ == '__main__':
    document = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=22 * mm, bottomMargin=23 * mm,
        title='Assure Risk - System and User Guide',
        author='Assure Risk', subject='Registration and workflows for three user roles',
    )
    document.build(story, onFirstPage=decorate, onLaterPages=decorate)
    print(OUTPUT)
