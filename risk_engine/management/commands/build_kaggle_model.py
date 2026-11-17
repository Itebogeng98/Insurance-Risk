"""Build a native-data research model without writing production database rows."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from risk_engine.evaluation import evaluate_native


class Command(BaseCommand):
    help = 'Download authorised Kaggle data and train a build-bundled native analysis model.'

    def handle(self, *args, **options):
        if not os.environ.get('KAGGLE_API_TOKEN', '').strip():
            raise CommandError('Set KAGGLE_API_TOKEN privately in Render before enabling the Kaggle build.')
        destination = Path(settings.BASE_DIR) / 'risk_engine' / 'ml_models' / 'kaggle_native'
        with tempfile.TemporaryDirectory(prefix='prudential-build-') as temporary:
            directory = Path(temporary)
            self.stdout.write('Downloading authorised Prudential train.csv from Kaggle...')
            try:
                subprocess.run([
                    'kaggle', 'competitions', 'download',
                    'prudential-life-insurance-assessment', '-f', 'train.csv',
                    '-p', str(directory), '-q',
                ], check=True, timeout=600, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (OSError, subprocess.SubprocessError) as exc:
                raise CommandError(
                    'Kaggle download failed. Check the API token, competition rule acceptance '
                    'and network access. Credentials were not logged.'
                ) from exc
            source = directory / 'train.csv'
            if not source.exists():
                archive = directory / 'train.csv.zip'
                try:
                    with zipfile.ZipFile(archive) as bundle:
                        info = bundle.getinfo('train.csv')
                        if info.file_size > 50 * 1024 * 1024:
                            raise CommandError('Kaggle CSV exceeds the 50 MB build input limit.')
                        source.write_bytes(bundle.read(info))
                except (OSError, KeyError, zipfile.BadZipFile) as exc:
                    raise CommandError('Kaggle did not return the expected train.csv file.') from exc
            if source.stat().st_size > 50 * 1024 * 1024:
                raise CommandError('Kaggle CSV exceeds the 50 MB build input limit.')
            result = evaluate_native(
                pd.read_csv(source), progress=lambda message: self.stdout.write(message),
                export_dir=destination,
            )
            result.update({
                'purpose': 'Build-trained Kaggle native analysis; not live applicant scoring',
                'native_analysis_ready': True,
                'built_at': timezone.now().isoformat(),
                'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'artifact_sha256': hashlib.sha256((destination / 'model.joblib').read_bytes()).hexdigest(),
            })
            (destination / 'evaluation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(
            f'KAGGLE BUILD COMPLETE: {result["selected_model"]}; '
            f'accuracy={result["test_metrics"]["accuracy"]:.4f}; '
            f'macro_f1={result["test_metrics"]["macro_f1"]:.4f}. '
            'Available for native Kaggle analysis only.'
        ))
