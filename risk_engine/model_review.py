"""Human provenance review before a candidate can be activated."""

import hashlib
import json

from django.db import transaction

from accounts.models import AuditLog
from applicants.permissions import is_administrator
from .model_versions import model_artifact_path, validate_production_model
from .models import ModelVersion, TrainingDataset


@transaction.atomic
def approve_model(version_id, user, notes):
    if not user.is_active or not is_administrator(user):
        raise ValueError('Administrator role required.')
    notes = (notes or '').strip()
    if not 30 <= len(notes) <= 2000:
        raise ValueError('Record 30 to 2,000 characters describing the provenance and input review.')
    version = ModelVersion.objects.select_for_update().get(pk=version_id)
    if version.input_contract_verified:
        raise ValueError('This model has already been reviewed.')
    if version.training_schema != 3:
        raise ValueError('Only applicant-schema models can be approved. Prudential adapter models are not eligible.')
    dataset = TrainingDataset.objects.filter(
        model_version=version.version_tag, status=TrainingDataset.Status.COMPLETE,
    ).first()
    if dataset is None:
        raise ValueError('A completed uploaded applicant dataset is required for review.')
    artifact = model_artifact_path(version)
    if not artifact.is_file():
        raise ValueError('The trained model file is missing. Train a new candidate.')
    try:
        evidence = json.loads(artifact.with_suffix('.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValueError('Training evidence is missing or unreadable.') from exc
    if (not isinstance(evidence, dict)
            or evidence.get('model_version') != version.version_tag
            or evidence.get('input_format') != 'applicant'):
        raise ValueError('Training evidence does not identify this applicant-schema model.')
    with dataset.csv_file.open('rb') as source:
        checksum = hashlib.file_digest(source, 'sha256').hexdigest()
    if checksum != evidence.get('source_sha256'):
        raise ValueError('The dataset no longer matches the training evidence. Retrain before review.')
    # Approval records an accountable human review, not automatic verification
    # that a CSV's claimed human labels or provenance are truthful.
    version.input_contract_verified = True
    validate_production_model(version)
    version.save(update_fields=['input_contract_verified'])
    AuditLog.objects.create(
        user=user, action=AuditLog.Action.DATA_CHANGE,
        object_type='ModelVersion', object_id=str(version.pk),
        detail=f'Input/provenance review approved for {version.version_tag}. Review notes: {notes}',
    )
    return version
