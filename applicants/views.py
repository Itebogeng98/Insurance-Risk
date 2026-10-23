from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from django.views.generic import DetailView, ListView

from accounts.audit import write_audit_log
from accounts.models import AuditLog
from .forms import (
    ApplicantForm,
    LifestyleHabitsForm,
    MedicalHistoryForm,
    SalaryForm,
    SpendingBehaviourForm,
    VehicleInsuranceHistoryForm,
)
from .models import Applicant
from .permissions import can_assess_applicants, can_create_applicants, visible_applicants_for
from risk_engine.recommendations import build_lifestyle_recommendations


APPLICANT_WIZARD_SESSION_KEY = 'applicant_create_wizard'

APPLICANT_WIZARD_STEPS = (
    {
        'key': 'applicant',
        'form_key': 'applicant_form',
        'form_class': ApplicantForm,
        'prefix': 'applicant',
        'title': 'Personal Information',
        'short_title': 'Personal',
        'description': 'Identity and contact details',
        'icon': 'bi-person',
    },
    {
        'key': 'medical',
        'form_key': 'medical_form',
        'form_class': MedicalHistoryForm,
        'prefix': 'medical',
        'title': 'Medical History',
        'short_title': 'Medical',
        'description': 'Health indicators used by the risk engine',
        'icon': 'bi-heart-pulse',
    },
    {
        'key': 'lifestyle',
        'form_key': 'lifestyle_form',
        'form_class': LifestyleHabitsForm,
        'prefix': 'lifestyle',
        'title': 'Lifestyle Habits',
        'short_title': 'Lifestyle',
        'description': 'Behavioural and occupational risk factors',
        'icon': 'bi-activity',
    },
    {
        'key': 'salary',
        'form_key': 'salary_form',
        'form_class': SalaryForm,
        'prefix': 'salary',
        'title': 'Salary',
        'short_title': 'Finance',
        'description': 'Employment and income details',
        'icon': 'bi-cash-coin',
    },
    {
        'key': 'vehicle',
        'form_key': 'vehicle_form',
        'form_class': VehicleInsuranceHistoryForm,
        'prefix': 'vehicle',
        'title': 'Vehicle Insurance History',
        'short_title': 'Vehicle',
        'description': 'Claims, accidents, and driving history',
        'icon': 'bi-car-front',
    },
    {
        'key': 'spending',
        'form_key': 'spending_form',
        'form_class': SpendingBehaviourForm,
        'prefix': 'spending',
        'title': 'Spending Behaviour',
        'short_title': 'Spending',
        'description': 'Savings, debt, and credit profile',
        'icon': 'bi-wallet2',
    },
)


def _wizard_url(step_index: int) -> str:
    return f'{reverse("applicants:create")}?step={step_index + 1}'


def _posted_data_to_session(post_data) -> dict:
    return {key: values for key, values in post_data.lists()}


def _session_data_to_multivalue(data: dict | None):
    if not data:
        return None
    return MultiValueDict(data)


def _get_requested_step(request: HttpRequest) -> int:
    try:
        step_number = int(request.GET.get('step', '1'))
    except ValueError:
        step_number = 1
    return max(0, min(step_number - 1, len(APPLICANT_WIZARD_STEPS) - 1))


def _first_incomplete_step(wizard_data: dict) -> int | None:
    for index, step in enumerate(APPLICANT_WIZARD_STEPS):
        if step['key'] not in wizard_data:
            return index
    return None


def _build_completed_forms(wizard_data: dict):
    forms = {}
    for step in APPLICANT_WIZARD_STEPS:
        data = _session_data_to_multivalue(wizard_data.get(step['key']))
        forms[step['form_key']] = step['form_class'](data, prefix=step['prefix'])
    return forms


def _stored_monthly_income(wizard_data: dict):
    salary_data = _session_data_to_multivalue(wizard_data.get('salary'))
    if not salary_data:
        return None
    salary_form = SalaryForm(salary_data, prefix='salary')
    if salary_form.is_valid():
        return salary_form.cleaned_data['monthly_income']
    return None


def _expenses_within_income_limit(form, monthly_income) -> bool:
    if monthly_income is None or not form.is_valid():
        return True
    monthly_expenses = form.cleaned_data.get('monthly_expenses')
    if monthly_expenses is not None and monthly_expenses > monthly_income * 3:
        form.add_error(
            'monthly_expenses',
            'Monthly expenditure may not exceed salary by more than 200%.',
        )
        return False
    return True


class ApplicantListView(LoginRequiredMixin, ListView):
    model = Applicant
    template_name = 'applicants/applicant_list.html'
    context_object_name = 'applicants'
    paginate_by = 20

    def get_queryset(self):
        queryset = visible_applicants_for(self.request.user).select_related('created_by').prefetch_related(
            'risk_assessments'
        ).order_by('-created_at')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(national_id__icontains=query)
                | Q(email__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['can_create_applicants'] = can_create_applicants(self.request.user)
        return context


class ApplicantDetailView(LoginRequiredMixin, DetailView):
    model = Applicant
    template_name = 'applicants/applicant_detail.html'
    context_object_name = 'applicant'

    def get_queryset(self):
        return visible_applicants_for(self.request.user).select_related(
            'medical_history', 'lifestyle_habits', 'salary',
            'vehicle_insurance_history', 'spending_behaviour',
        ).prefetch_related('risk_assessments__feature_contributions', 'risk_assessments__recommendations')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        latest_assessment = self.object.risk_assessments.first()
        context['recommendations'] = (
            [recommendation.message for recommendation in latest_assessment.recommendations.all()]
            if latest_assessment
            else build_lifestyle_recommendations(self.object)
        )
        context['can_assess_applicants'] = can_assess_applicants(self.request.user)
        write_audit_log(
            request=self.request,
            action=AuditLog.Action.DATA_ACCESS,
            object_type='Applicant',
            object_id=self.object.pk,
            detail='Applicant detail viewed.',
        )
        return context


@login_required
def applicant_create(request: HttpRequest) -> HttpResponse:
    if not can_create_applicants(request.user):
        messages.error(request, 'Applicant accounts can view their own records, but cannot create applicant profiles.')
        return redirect('applicants:list')

    if request.method == 'GET' and 'step' not in request.GET:
        request.session.pop(APPLICANT_WIZARD_SESSION_KEY, None)

    wizard_data = request.session.get(APPLICANT_WIZARD_SESSION_KEY, {})
    step_index = _get_requested_step(request)

    first_incomplete = _first_incomplete_step(wizard_data)
    if request.method == 'GET' and first_incomplete is not None and step_index > first_incomplete:
        return redirect(_wizard_url(first_incomplete))

    step = APPLICANT_WIZARD_STEPS[step_index]
    stored_data = _session_data_to_multivalue(wizard_data.get(step['key']))
    form_data = request.POST if request.method == 'POST' else stored_data
    current_form = step['form_class'](form_data, prefix=step['prefix'])

    if request.method == 'POST':
        monthly_income = _stored_monthly_income(wizard_data) if step['key'] == 'spending' else None
        if current_form.is_valid() and _expenses_within_income_limit(current_form, monthly_income):
            wizard_data[step['key']] = _posted_data_to_session(request.POST)
            request.session[APPLICANT_WIZARD_SESSION_KEY] = wizard_data
            request.session.modified = True

            if step_index < len(APPLICANT_WIZARD_STEPS) - 1:
                return redirect(_wizard_url(step_index + 1))

            forms_map = _build_completed_forms(wizard_data)
            validity = [form.is_valid() for form in forms_map.values()]
            if not all(validity):
                first_invalid = next(
                    index for index, wizard_step in enumerate(APPLICANT_WIZARD_STEPS)
                    if not forms_map[wizard_step['form_key']].is_valid()
                )
                return redirect(_wizard_url(first_invalid))

            with transaction.atomic():
                applicant = forms_map['applicant_form'].save(commit=False)
                applicant.created_by = request.user
                applicant.save()
                for key in (
                    'medical_form', 'lifestyle_form', 'salary_form',
                    'vehicle_form', 'spending_form',
                ):
                    instance = forms_map[key].save(commit=False)
                    instance.applicant = applicant
                    instance.save()
            write_audit_log(
                request=request,
                action=AuditLog.Action.DATA_CHANGE,
                object_type='Applicant',
                object_id=applicant.pk,
                detail='Applicant created.',
            )
            request.session.pop(APPLICANT_WIZARD_SESSION_KEY, None)
            return redirect('applicants:detail', pk=applicant.pk)

    steps_context = []
    for index, wizard_step in enumerate(APPLICANT_WIZARD_STEPS):
        steps_context.append({
            **wizard_step,
            'number': index + 1,
            'is_active': index == step_index,
            'is_complete': wizard_step['key'] in wizard_data and index != step_index,
            'is_available': index <= (first_incomplete if first_incomplete is not None else step_index),
            'url': _wizard_url(index),
        })

    return render(request, 'applicants/applicant_form.html', {
        'current_form': current_form,
        'current_step': {
            **step,
            'number': step_index + 1,
        },
        'step_index': step_index,
        'total_steps': len(APPLICANT_WIZARD_STEPS),
        'steps': steps_context,
        'previous_step_url': _wizard_url(step_index - 1) if step_index > 0 else None,
        'next_button_label': 'Save Applicant' if step_index == len(APPLICANT_WIZARD_STEPS) - 1 else 'Save and Continue',
    })
