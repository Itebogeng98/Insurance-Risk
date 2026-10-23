from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from functools import wraps

from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, get_user_model, login
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_GET, require_POST

from accounts.audit import write_audit_log
from accounts.models import AuditLog, UserProfile
from accounts.forms import RegistrationForm
from applicants.forms import (
    ApplicantForm,
    LifestyleHabitsForm,
    MedicalHistoryForm,
    SalaryForm,
    SpendingBehaviourForm,
    VehicleInsuranceHistoryForm,
)
from applicants.models import Applicant
from applicants.permissions import can_assess_applicants, can_create_applicants, get_visible_applicant_or_404, is_administrator
from reports.views import _render_pdf, _report_context, _plain_report_text
from risk_engine.models import RiskAssessment, TrainingDataset
from risk_engine.recommendations import build_lifestyle_recommendations
from risk_engine.scoring import IncompleteApplicantProfileError, ModelNotTrainedError, assess_applicant
from risk_engine.training import queue_training


def _json_body(request: HttpRequest) -> dict:
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _make_jwt(user) -> str:
    header = {'alg': 'HS256', 'typ': 'JWT'}
    payload = {'sub': user.pk, 'username': user.username, 'exp': int(time.time()) + 60 * 60 * 8}
    signing_input = '.'.join([
        _b64url(json.dumps(header, separators=(',', ':')).encode()),
        _b64url(json.dumps(payload, separators=(',', ':')).encode()),
    ])
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        signing_input.encode(),
        hashlib.sha256,
    ).digest()
    return f'{signing_input}.{_b64url(signature)}'


def _decode_jwt(token: str):
    try:
        header_part, payload_part, signature_part = token.split('.')
        signing_input = f'{header_part}.{payload_part}'
        expected = _b64url(hmac.new(
            settings.SECRET_KEY.encode(),
            signing_input.encode(),
            hashlib.sha256,
        ).digest())
        if not hmac.compare_digest(signature_part, expected):
            return None
        padded_payload = payload_part + '=' * (-len(payload_part) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded_payload))
        if payload.get('exp', 0) < time.time():
            return None
        return get_user_model().objects.filter(pk=payload.get('sub'), is_active=True).first()
    except (ValueError, json.JSONDecodeError, TypeError):
        return None


def _bearer_user(request: HttpRequest):
    header = request.META.get('HTTP_AUTHORIZATION', '')
    if not header.startswith('Bearer '):
        return None
    return _decode_jwt(header.removeprefix('Bearer ').strip())


def api_login_required(view_func):
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        if request.META.get('HTTP_AUTHORIZATION'):
            user = _bearer_user(request)
            if user is None:
                return JsonResponse({'error': 'Authentication required.'}, status=401)
            request.user = user
            return view_func(request, *args, **kwargs)
        if not request.user.is_authenticated or not request.user.is_active:
            return JsonResponse({'error': 'Authentication required.'}, status=401)
        return csrf_protect(view_func)(request, *args, **kwargs)
    return wrapper


def _prefix_data(data: dict, prefix: str) -> dict:
    return {f'{prefix}-{key}': value for key, value in data.items()}


def _assessment_payload(assessment: RiskAssessment) -> dict:
    return {
        'assessmentId': assessment.pk,
        'applicantId': assessment.applicant_id,
        'riskClass': assessment.risk_category.title(),
        'riskScore': float(assessment.risk_score),
        'confidence': float(assessment.confidence),
        'modelVersion': assessment.model_version,
        'needsManualReview': assessment.needs_manual_review,
        'topFactors': [
            {
                'feature': item.feature,
                'label': item.label,
                'contribution': float(item.contribution),
            }
            for item in assessment.feature_contributions.all()
        ],
        'recommendations': build_lifestyle_recommendations(assessment.applicant),
    }


@csrf_exempt
@require_POST
def api_register(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    required = {'username', 'email', 'password'}
    missing = sorted(required - data.keys())
    if missing:
        return JsonResponse({'errors': {'missing': missing}}, status=400)
    role = data.get('role', UserProfile.Role.CUSTOMER)
    if role == 'APPLICANT':
        role = UserProfile.Role.CUSTOMER
    if role == UserProfile.Role.ADMINISTRATOR:
        return JsonResponse(
            {'errors': {'role': ['Administrator accounts must be created by an existing administrator.']}},
            status=400,
        )
    form = RegistrationForm(data={
        'username': data['username'], 'email': data['email'], 'role': role,
        'password1': data['password'], 'password2': data['password'],
    })
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)
    with transaction.atomic():
        user = form.save()
    return JsonResponse({'userId': user.pk}, status=201)


@csrf_protect
@require_POST
def api_login(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    user = authenticate(request, username=data.get('username'), password=data.get('password'))
    if user is None:
        write_audit_log(
            request=request,
            action=AuditLog.Action.LOGIN_FAILURE,
            object_type='User',
            detail=f'API login failed for username "{data.get("username", "")}".',
        )
        return JsonResponse({'error': 'Invalid credentials'}, status=401)
    login(request, user)
    write_audit_log(
        request=request,
        user=user,
        action=AuditLog.Action.LOGIN_SUCCESS,
        object_type='User',
        object_id=user.pk,
        detail='API sign-in.',
    )
    return JsonResponse({'accessToken': _make_jwt(user), 'tokenType': 'Bearer', 'userId': user.pk})


@csrf_exempt
@api_login_required
@require_POST
def api_create_applicant(request: HttpRequest) -> JsonResponse:
    if not can_create_applicants(request.user):
        return JsonResponse({'error': 'Applicant accounts cannot create applicant profiles.'}, status=403)
    data = _json_body(request)
    section_map = {
        'applicant': ApplicantForm(_prefix_data(data.get('applicant', data), 'applicant'), prefix='applicant'),
        'medical': MedicalHistoryForm(_prefix_data(data.get('medical', {}), 'medical'), prefix='medical'),
        'lifestyle': LifestyleHabitsForm(_prefix_data(data.get('lifestyle', {}), 'lifestyle'), prefix='lifestyle'),
        'salary': SalaryForm(_prefix_data(data.get('salary', {}), 'salary'), prefix='salary'),
        'vehicle': VehicleInsuranceHistoryForm(_prefix_data(data.get('vehicle', {}), 'vehicle'), prefix='vehicle'),
        'spending': SpendingBehaviourForm(_prefix_data(data.get('spending', {}), 'spending'), prefix='spending'),
    }
    if not all(form.is_valid() for form in section_map.values()):
        return JsonResponse(
            {'errors': {key: form.errors for key, form in section_map.items() if form.errors}},
            status=400,
        )
    salary = section_map['salary'].cleaned_data['monthly_income']
    expenses = section_map['spending'].cleaned_data['monthly_expenses']
    if expenses > salary * 3:
        return JsonResponse(
            {'errors': {'spending': {'monthly_expenses': ['Monthly expenditure may not exceed salary by more than 200%.']}}},
            status=400,
        )
    with transaction.atomic():
        applicant = section_map['applicant'].save(commit=False)
        applicant.created_by = request.user
        applicant.save()
        for key in ('medical', 'lifestyle', 'salary', 'vehicle', 'spending'):
            instance = section_map[key].save(commit=False)
            instance.applicant = applicant
            instance.save()
    write_audit_log(
        request=request,
        action=AuditLog.Action.DATA_CHANGE,
        object_type='Applicant',
        object_id=applicant.pk,
        detail='Applicant created through API.',
    )
    return JsonResponse({'applicantId': applicant.pk}, status=201)


@csrf_exempt
@api_login_required
@require_POST
def api_predict_risk(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    applicant = get_visible_applicant_or_404(request.user, pk=data.get('applicantId'))
    if not can_assess_applicants(request.user):
        return JsonResponse({'error': 'Applicant accounts cannot run risk assessments.'}, status=403)
    try:
        assessment = assess_applicant(applicant)
    except IncompleteApplicantProfileError as exc:
        return JsonResponse({'error': str(exc)}, status=422)
    except ModelNotTrainedError as exc:
        return JsonResponse({'error': str(exc)}, status=503)
    write_audit_log(
        request=request,
        action=AuditLog.Action.RISK_ASSESSMENT,
        object_type='RiskAssessment',
        object_id=assessment.pk,
        detail=f'API risk assessment for applicant {applicant.pk}.',
    )
    return JsonResponse(_assessment_payload(assessment))


@api_login_required
@require_GET
def api_assessment_detail(request: HttpRequest, assessment_id: int) -> JsonResponse:
    assessment = get_object_or_404(RiskAssessment.objects.select_related('applicant').prefetch_related(
        'feature_contributions'
    ), pk=assessment_id)
    get_visible_applicant_or_404(request.user, pk=assessment.applicant_id)
    write_audit_log(
        request=request,
        action=AuditLog.Action.DATA_ACCESS,
        object_type='RiskAssessment',
        object_id=assessment.pk,
        detail='API assessment detail viewed.',
    )
    return JsonResponse(_assessment_payload(assessment))


@api_login_required
@require_GET
def api_report_pdf(request: HttpRequest, assessment_id: int):
    assessment = get_object_or_404(RiskAssessment.objects.select_related('applicant'), pk=assessment_id)
    context = _report_context(request, assessment.applicant_id, assessment_id=assessment.pk)

    pdf = _render_pdf(
        _plain_report_text(context),
        request.build_absolute_uri('/'),
    )
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="underwriting-report-{assessment.applicant_id}-assessment-{assessment.pk}.pdf"'
    )
    write_audit_log(
        request=request, action=AuditLog.Action.DATA_ACCESS,
        object_type='RiskAssessment', object_id=assessment.pk,
        detail='Assessment-specific API PDF exported.',
    )
    return response


@csrf_exempt
@api_login_required
@require_POST
def api_upload_dataset(request: HttpRequest) -> JsonResponse:
    if not is_administrator(request.user):
        return JsonResponse({'error': 'Administrator role required.'}, status=403)
    try:
        dataset = queue_training(request.FILES.get('file'), request.user, request.POST.get('description'))
    except ValidationError as exc:
        return JsonResponse({'errors': exc.messages}, status=400)
    write_audit_log(
        request=request,
        action=AuditLog.Action.MODEL_TRAINING,
        object_type='TrainingDataset',
        object_id=dataset.pk,
        detail=f'Queued training dataset with {dataset.row_count} rows.',
    )
    return JsonResponse(
        {
            'datasetId': dataset.pk,
            'rowCount': dataset.row_count,
            'retrainingJobId': str(dataset.pk),
            'status': dataset.status,
            'modelVersion': dataset.model_version,
        },
        status=202,
    )
