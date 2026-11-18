from applicants.permissions import application_profile_complete, can_create_applicants, is_applicant, is_administrator


def demonstration_status(request):
    applicant_account = request.user.is_authenticated and is_applicant(request.user)
    has_draft = bool(request.session.get('applicant_create_wizard'))
    create_label = 'Apply Now' if applicant_account else 'New Applicant'
    if has_draft:
        create_label = 'Continue Application' if applicant_account else 'Continue Capture'
    return {
        'can_create_applicants': can_create_applicants(request.user),
        'is_applicant_account': applicant_account,
        'has_application_draft': has_draft,
        'application_create_label': create_label,
        'is_administrator_account': request.user.is_authenticated and is_administrator(request.user),
        'application_profile_complete': application_profile_complete(request.user),
    }
