import pathlib
import time
import uuid
import json
import hashlib

import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.utils import resample

from etl.kaggle import load_prudential_applicants
from etl.synthetic import generate_synthetic_applicants
from risk_engine.features import build_feature_frame
from risk_engine.models import ModelVersion, TrainingDataset
from risk_engine.training import validate_training_csv
from risk_engine.pipeline import build_risk_pipeline
from risk_engine.risk_rules import label_training_data
from risk_engine.applicant_data import read_applicant_csv

class Command(BaseCommand):
    help = 'Train an inactive candidate from labelled applicant CSV, Prudential CSV, or demonstration data.'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--rows', type=int, default=5000)
        parser.add_argument('--seed', type=int, default=42)
        parser.add_argument('--kaggle-rows', type=int, default=20000)
        parser.add_argument('--no-kaggle', action='store_true')
        parser.add_argument('--csv-path')
        parser.add_argument('--dataset-id', type=int)
        parser.add_argument('--activate', action='store_true')

    def handle(self, *args, **options) -> None:
        if options['csv_path']:
            validate_training_csv(options['csv_path'])
            columns = pd.read_csv(options['csv_path'], nrows=0).columns
            applicant_schema = 'risk_category' in columns or 'record_id' in columns
            labeled = (read_applicant_csv(options['csv_path']) if applicant_schema
                       else load_prudential_applicants(options['csv_path']))
        else:
            applicant_schema = False
            rng = np.random.default_rng(options['seed'])
            raw = generate_synthetic_applicants(options['rows'], seed=options['seed'])
            labeled = label_training_data(raw, rng)
            labeled['source_dataset'] = 'synthetic'

        if not options['csv_path'] and not options['no_kaggle']:
            kaggle = load_prudential_applicants(limit=options['kaggle_rows'], seed=options['seed'])
            if not kaggle.empty:
                labeled = pd.concat([labeled, kaggle], ignore_index=True)

        features = build_feature_frame(labeled)
        target = labeled['risk_category']

        x_train, x_test, y_train, y_test = train_test_split(
            features,
            target,
            test_size=0.2,
            random_state=options['seed'],
            stratify=target,
        )

        train = x_train.copy()
        train['risk_category'] = y_train.values
        target_count = train['risk_category'].value_counts().max()
        balanced_parts = []
        for _, group in train.groupby('risk_category'):
            balanced_parts.append(
                resample(
                    group,
                    replace=True,
                    n_samples=target_count,
                    random_state=options['seed'],
                )
            )
        balanced_train = pd.concat(balanced_parts).sample(
            frac=1,
            random_state=options['seed'],
        )
        x_train = balanced_train.drop(columns=['risk_category'])
        y_train = balanced_train['risk_category']

        pipeline = build_risk_pipeline(random_state=options['seed'])
        pipeline.fit(x_train, y_train)

        predictions = pipeline.predict(x_test)
        accuracy = accuracy_score(y_test, predictions)
        macro_f1 = f1_score(y_test, predictions, average='macro')
        latency_sample = x_test.head(min(1000, len(x_test)))
        durations = []
        for _, row in latency_sample.iterrows():
            start = time.perf_counter()
            pipeline.predict(row.to_frame().T)
            durations.append((time.perf_counter() - start) * 1000)
        inference_p95_ms = float(np.percentile(durations, 95)) if durations else 0.0

        model_dir = pathlib.Path(settings.MODEL_DIR)
        model_dir.mkdir(parents=True, exist_ok=True)
        version_tag = f'gb-{uuid.uuid4().hex}'
        version_path = model_dir / f'{version_tag}.joblib'
        joblib.dump(pipeline, version_path)
        evidence = {
            'model_version': version_tag, 'seed': options['seed'],
            'input_format': 'applicant' if applicant_schema else 'demonstration_adapter',
            'input_contract_verified': False,
            'review_required': 'Review data provenance and human outcomes before production approval.',
            'source_sha256': hashlib.sha256(pathlib.Path(options['csv_path']).read_bytes()).hexdigest() if options['csv_path'] else None,
            'source_rows': len(labeled), 'training_rows_after_balancing': len(x_train),
            'test_rows': len(x_test), 'accuracy': float(accuracy), 'macro_f1': float(macro_f1),
            'inference_p95_ms': inference_p95_ms,
            'feature_columns': list(features.columns),
            'evaluation_protocol': 'Fixed model, stratified 80/20 internal holdout; no parameter search.',
        }
        version_path.with_suffix('.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
        version = ModelVersion.objects.create(
            version_tag=version_tag,
            accuracy=round(accuracy, 3),
            macro_f1=round(macro_f1, 3),
            inference_p95_ms=round(inference_p95_ms, 2),
            artifact_path=str(version_path),
            is_active=False,
            training_schema=3 if applicant_schema else 2,
        )
        if options['dataset_id']:
            TrainingDataset.objects.filter(pk=options['dataset_id']).update(
                model_version=version.version_tag, accuracy=version.accuracy,
                macro_f1=version.macro_f1, inference_p95_ms=version.inference_p95_ms,
                status='COMPLETE', error_message='',
            )
        if options['activate']:
            from risk_engine.model_versions import activate_model_version
            activate_model_version(version)

        self.stdout.write(self.style.SUCCESS(
            f'Trained on {len(x_train)} rows, validated on {len(x_test)} rows. '
            f'sources={labeled["source_dataset"].value_counts().to_dict()}. '
            f'accuracy={accuracy:.3f}, macro_f1={macro_f1:.3f}, '
            f'inference_p95_ms={inference_p95_ms:.2f}, model_version={version_tag}. '
            f'Saved to {version_path}'
        ))
