from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST
import csv

from accounts.audit import write_audit_log
from accounts.models import AuditLog
from applicants.permissions import can_assess_applicants, get_visible_applicant_or_404, is_administrator

from .model_versions import activate_model_version
from .training import queue_training
from .models import ModelVersion, TrainingDataset
from .scoring import IncompleteApplicantProfileError, ModelNotTrainedError, assess_applicant
from .applicant_data import APPLICANT_COLUMNS


@login_required
@require_GET
def applicant_training_template(request):
    if not is_administrator(request.user):
        return HttpResponse('Administrator role required.', status=403)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="applicant-training-template.csv"'
    csv.writer(response).writerow(APPLICANT_COLUMNS)
    return response


@login_required
@require_POST
def assess_applicant_view(request: HttpRequest, applicant_id: int) -> HttpResponse:
    applicant = get_visible_applicant_or_404(request.user, pk=applicant_id)
    if not can_assess_applicants(request.user):
        messages.error(request, 'Applicant accounts can view assessment results, but cannot run risk assessments.')
        return redirect('applicants:detail', pk=applicant.pk)
    try:
        assessment = assess_applicant(applicant)
        write_audit_log(
            request=request,
            action=AuditLog.Action.RISK_ASSESSMENT,
            object_type='RiskAssessment',
            object_id=assessment.pk,
            detail=f'Risk assessment completed for applicant {applicant.pk}.',
        )
        messages.success(request, 'Risk assessment completed.')
    except IncompleteApplicantProfileError as exc:
        messages.error(request, str(exc))
    except ModelNotTrainedError as exc:
        messages.error(request, str(exc))
    return redirect('applicants:detail', pk=applicant.pk)


@login_required
def model_management(request: HttpRequest) -> HttpResponse:
    if not is_administrator(request.user):
        messages.error(request, 'Administrator role required.')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'upload':
            try:
                dataset = queue_training(request.FILES.get('dataset'), request.user, request.POST.get('description'))
            except ValidationError as exc:
                messages.error(request, '; '.join(exc.messages))
            else:
                write_audit_log(
                    request=request,
                    action=AuditLog.Action.MODEL_TRAINING,
                    object_type='TrainingDataset',
                    object_id=dataset.pk,
                    detail='Validated dataset queued for training.',
                )
                messages.success(request, 'Dataset queued. The trained model will be available for review before activation.')
        elif action == 'activate':
            version_id = request.POST.get('version_id', '')
            version = ModelVersion.objects.filter(pk=version_id).first() if version_id.isdigit() else None
            if version:
                try:
                    activate_model_version(version)
                except (OSError, ValueError) as exc:
                    messages.error(request, str(exc))
                else:
                    messages.success(request, f'{version.version_tag} activated.')
            else:
                messages.error(request, 'Select a valid model version.')
        return redirect('risk_engine:model_management')

    return render(request, 'risk_engine/model_management.html', {
        'training_enabled': getattr(settings, 'TRAINING_ENABLED', True),
        'model_activation_enabled': getattr(settings, 'MODEL_ACTIVATION_ENABLED', True),
        'datasets': TrainingDataset.objects.all()[:20],
        'model_versions': ModelVersion.objects.all()[:20],
    })
