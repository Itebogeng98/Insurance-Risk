import pathlib
import shutil

from django.conf import settings
from django.db import transaction

from .models import ModelVersion, TrainingDataset


def validate_production_model(version):
    if not getattr(settings, 'REQUIRE_VALIDATED_MODEL', False):
        return
    if version is None or version.training_schema < 2:
        raise ValueError('Retrain this legacy model before production activation.')
    if not version.input_contract_verified:
        raise ValueError('The training inputs have not been verified against live applicant inputs.')
    if (version.accuracy is None or float(version.accuracy) < settings.MODEL_MIN_ACCURACY
            or version.macro_f1 is None or float(version.macro_f1) < settings.MODEL_MIN_MACRO_F1):
        raise ValueError('This model does not meet the production accuracy and macro F1 thresholds.')


def model_artifact_path(version: ModelVersion) -> pathlib.Path:
    artifact_path = pathlib.Path(version.artifact_path)
    if artifact_path.is_absolute():
        return artifact_path
    return pathlib.Path(settings.BASE_DIR) / artifact_path


def active_model_path() -> pathlib.Path:
    return pathlib.Path(settings.MODEL_DIR) / 'risk_model.joblib'


def clear_model_cache() -> None:
    from .scoring import _load_model

    _load_model.cache_clear()


def activate_model_version(version: ModelVersion) -> pathlib.Path:
    if not getattr(settings, 'MODEL_ACTIVATION_ENABLED', True):
        raise ValueError('Model activation is unavailable on this deployment.')
    validate_production_model(version)
    source = model_artifact_path(version)
    if not source.exists():
        raise FileNotFoundError(f'Model artefact not found: {source}')

    target = active_model_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != target.resolve():
        shutil.copyfile(source, target)

    with transaction.atomic():
        ModelVersion.objects.update(is_active=False)
        version.is_active = True
        version.save(update_fields=['is_active'])
        TrainingDataset.objects.update(is_active=False)
        TrainingDataset.objects.filter(model_version=version.version_tag).update(is_active=True)

    clear_model_cache()
    return target
