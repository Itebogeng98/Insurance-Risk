from pathlib import Path

import pandas as pd
from django.core.exceptions import ValidationError
from django.conf import settings

from .models import TrainingDataset
from .applicant_data import read_applicant_csv


PRUDENTIAL_COLUMNS = {
    'Ins_Age', 'Ht', 'Wt', 'BMI', 'Employment_Info_1', 'Employment_Info_2',
    'Employment_Info_6', 'InsuredInfo_1', 'Medical_History_1', 'Response',
}
MAX_DATASET_BYTES = 50 * 1024 * 1024


def validate_training_csv(source):
    try:
        frame = pd.read_csv(source)
    except (ValueError, UnicodeError, pd.errors.ParserError) as exc:
        raise ValidationError('Upload a readable UTF-8 CSV file.') from exc
    if 'risk_category' in frame or 'record_id' in frame:
        if hasattr(source, 'seek'):
            source.seek(0)
        return len(read_applicant_csv(source))
    missing = PRUDENTIAL_COLUMNS - set(frame.columns)
    if missing:
        raise ValidationError('Missing Prudential columns: ' + ', '.join(sorted(missing)))
    if len(frame) < 30 or len(frame) > 200000:
        raise ValidationError('Provide between 30 and 200,000 training rows.')
    for column in PRUDENTIAL_COLUMNS:
        values = pd.to_numeric(frame[column], errors='coerce')
        if values.notna().sum() == 0 or (frame[column].notna() & values.isna()).any() or not values.dropna().map(lambda v: float('-inf') < v < float('inf')).all():
            raise ValidationError(f'{column} must contain numeric values, with no infinity or text.')
    if not frame['Response'].isin(range(1, 9)).all():
        raise ValidationError('Response must be an integer from 1 to 8.')
    categories = pd.cut(frame['Response'], [0, 2, 5, 8], labels=['HIGH', 'MEDIUM', 'LOW'])
    if (categories.value_counts() < 5).any():
        raise ValidationError('Provide at least five records in each risk category.')
    return len(frame)


def queue_training(uploaded, user, description=''):
    if not getattr(settings, 'TRAINING_ENABLED', True):
        raise ValidationError('Dataset uploads and training are unavailable on this deployment.')
    if uploaded is None or Path(uploaded.name).suffix.lower() != '.csv':
        raise ValidationError('Choose a labelled applicant or Prudential CSV file.')
    if uploaded.size > MAX_DATASET_BYTES:
        raise ValidationError('The dataset must not exceed 50 MB.')
    count = validate_training_csv(uploaded)
    uploaded.seek(0)
    dataset = TrainingDataset(
        description=(description or uploaded.name)[:200], csv_file=uploaded,
        uploaded_by=user, row_count=count, accepted_rows=count,
        status=TrainingDataset.Status.QUEUED,
    )
    dataset.save()
    return dataset
