from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.views.generic import TemplateView

from applicants.permissions import visible_applicants_for
from accounts.audit import write_audit_log
from accounts.models import AuditLog
from risk_engine.models import RiskAssessment

from .forms import ProfileForm, RegistrationForm, StyledAuthenticationForm


def home(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    return render(request, 'landing.html')


@login_required
def dashboard(request):
    applicants = visible_applicants_for(request.user).prefetch_related('risk_assessments')
    applicant_ids = applicants.values_list('pk', flat=True)
    latest_assessments = RiskAssessment.objects.filter(applicant_id__in=applicant_ids)
    risk_counts = latest_assessments.values('risk_category').annotate(total=Count('id'))
    counts_by_category = {item['risk_category']: item['total'] for item in risk_counts}

    context = {
        'total_applicants': applicants.count(),
        'assessed_applicants': applicants.filter(risk_assessments__isnull=False).distinct().count(),
        'high_risk_count': counts_by_category.get(RiskAssessment.RiskCategory.HIGH, 0),
        'medium_risk_count': counts_by_category.get(RiskAssessment.RiskCategory.MEDIUM, 0),
        'low_risk_count': counts_by_category.get(RiskAssessment.RiskCategory.LOW, 0),
        'recent_applicants': applicants.select_related('created_by').order_by('-created_at')[:5],
        'attention_applicants': applicants.filter(
            Q(risk_assessments__risk_category=RiskAssessment.RiskCategory.HIGH)
            | Q(risk_assessments__isnull=True)
        ).distinct().order_by('-created_at')[:5],
    }
    return render(request, 'accounts/dashboard.html', context)


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:dashboard')

    def form_valid(self, form: RegistrationForm) -> HttpResponse:
        response = super().form_valid(form)
        login(self.request, self.object)
        write_audit_log(
            request=self.request,
            user=self.object,
            action=AuditLog.Action.LOGIN_SUCCESS,
            object_type='User',
            object_id=self.object.pk,
            detail='Registered and signed in.',
        )
        return response


class AccountLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = StyledAuthenticationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        write_audit_log(
            request=self.request,
            user=self.request.user,
            action=AuditLog.Action.LOGIN_SUCCESS,
            object_type='User',
            object_id=self.request.user.pk,
            detail='Signed in.',
        )
        return response

    def form_invalid(self, form):
        username = self.request.POST.get('username', '')
        write_audit_log(
            request=self.request,
            action=AuditLog.Action.LOGIN_FAILURE,
            object_type='User',
            detail=f'Failed login attempt for username "{username}".',
        )
        return super().form_invalid(form)


class AccountLogoutView(LogoutView):
    pass


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form: ProfileForm) -> HttpResponse:
        messages.success(self.request, 'Profile updated.')
        return super().form_valid(form)


class LegalPageView(TemplateView):
    template_name = 'accounts/legal_page.html'

    page_content = {
        'privacy': {
            'title': 'Privacy Policy',
            'intro': 'How Assure Risk handles personal information provided through this system.',
            'items': [
                'We collect applicant, medical, lifestyle, vehicle insurance, salary and spending information needed for risk assessment.',
                'Applicant information is used to calculate risk scores, generate recommendations and produce underwriting reports.',
                'Authenticated users can only access applicant records they are authorised to view.',
                'Users should enter accurate information and avoid capturing data that is not relevant to the assessment.',
            ],
        },
        'terms': {
            'title': 'Terms of Use',
            'intro': 'Conditions for using the Assure Risk website and assessment workspace.',
            'items': [
                'The system supports life insurance applicant risk assessment and does not replace professional underwriting judgement.',
                'Users are responsible for entering accurate, authorised and relevant information.',
                'Reports and recommendations should be reviewed before they are used for formal decisions.',
                'Unauthorised access, misuse or interference with the system is not permitted.',
            ],
        },
        'paia': {
            'title': 'PAIA',
            'intro': 'Access to information notice for Assure Risk.',
            'items': [
                'Requests for access to records should identify the applicant, report or account information requested.',
                'Requests must include requester contact details and enough information to verify authority to access the record.',
                'Assure Risk will review requests according to applicable South African access-to-information requirements.',
                'This page provides project-ready PAIA information and can be replaced by a formal PAIA manual when available.',
            ],
        },
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_key = kwargs['page']
        context.update(self.page_content[page_key])
        return context
