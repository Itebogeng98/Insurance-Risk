"""Build a native-data research model without writing production database rows."""

import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import tempfile
import zipfile

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from risk_engine.evaluation import evaluate_native


def download_failure_hint(output):
    """Classify private CLI output without echoing tokens, URLs or response bodies."""
    message = output.lower()
    if re.search(r'\b401\b', message) or 'authentication required' in message or 'unauthorized' in message:
        return 'Authentication failed. Replace the token, or use KAGGLE_USERNAME and KAGGLE_KEY without KAGGLE_API_TOKEN.'
    if re.search(r'\b403\b|accept[^\n]*rules', message) or 'forbidden' in message:
        return 'Access denied. Check competition access and accept its rules using the same Kaggle account as the credentials.'
    if re.search(r'\b404\b', message) or 'not found' in message:
        return 'Competition or file unavailable. Confirm this account can download Prudential train.csv on Kaggle.'
    if re.search(r'\b429\b', message) or 'too many requests' in message:
        return 'Kaggle rate limit reached. Wait before redeploying.'
    if any(word in message for word in ('timed out', 'timeout', 'connectionerror', 'name resolution', 'sslerror')):
        return 'Network, timeout or TLS error contacting Kaggle. Retry later and check Render connectivity.'
    if 'unrecognized arguments' in message or 'invalid choice' in message:
        return 'Kaggle CLI rejected its arguments. Confirm the build installed the pinned kaggle==2.2.5 version.'
    if 'modulenotfounderror' in message or 'importerror' in message:
        return 'Kaggle CLI dependency import failed. Review the pip installation stage of the build.'
    return 'Unclassified CLI failure. Verify account access by downloading train.csv in the Kaggle website; raw output remains private.'


class Command(BaseCommand):
    help = 'Download authorised Kaggle data and train a build-bundled native analysis model.'

    def handle(self, *args, **options):
        supplied_path = os.environ.get('KAGGLE_BUILD_CSV_PATH', '').strip()
        supplied_source = None
        if supplied_path:
            supplied_source = Path(supplied_path)
            if not supplied_source.is_absolute():
                supplied_source = Path(settings.BASE_DIR) / supplied_source
            if not supplied_source.is_file() or supplied_source.suffix.lower() != '.csv':
                raise CommandError('KAGGLE_BUILD_CSV_PATH must identify an existing CSV inside the Render build environment, not a Windows path or ZIP.')
        download_env = os.environ.copy()
        for key in ('KAGGLE_API_TOKEN', 'KAGGLE_USERNAME', 'KAGGLE_KEY'):
            value = download_env.get(key, '').strip()
            if value:
                download_env[key] = value
            else:
                download_env.pop(key, None)
        token = download_env.get('KAGGLE_API_TOKEN', '')
        if not supplied_source and not token and not (download_env.get('KAGGLE_USERNAME') and download_env.get('KAGGLE_KEY')):
            raise CommandError('Set KAGGLE_API_TOKEN, or both KAGGLE_USERNAME and KAGGLE_KEY, privately in Render.')
        if not supplied_source and token.startswith(('{', '"', "'", 'export ', 'KAGGLE_API_TOKEN=')):
            raise CommandError('KAGGLE_API_TOKEN must contain only the token value, without JSON, quotes or a shell command.')
        destination = Path(settings.BASE_DIR) / 'risk_engine' / 'ml_models' / 'kaggle_native'
        with tempfile.TemporaryDirectory(prefix='prudential-build-') as temporary:
            directory = Path(temporary)
            if supplied_source:
                self.stdout.write('Using supplied Prudential CSV; Kaggle API download skipped.')
            else:
                self.stdout.write('Downloading authorised Prudential train.csv from Kaggle...')
                self.stdout.flush()
                try:
                    subprocess.run([
                        'kaggle', 'competitions', 'download',
                        'prudential-life-insurance-assessment', '-f', 'train.csv',
                        '-p', str(directory), '-q',
                    ], check=True, timeout=600, capture_output=True, text=True,
                        encoding='utf-8', errors='replace', env=download_env)
                except subprocess.TimeoutExpired:
                    raise CommandError('Kaggle download timed out after 10 minutes. No training started.') from None
                except subprocess.CalledProcessError as exc:
                    raise CommandError(
                        f'Kaggle CLI exited with code {exc.returncode}. '
                        + download_failure_hint((exc.stdout or '') + '\n' + (exc.stderr or ''))
                    ) from None
                except OSError:
                    raise CommandError('Kaggle CLI could not start. Check its installation and executable path in the build.') from None
            source = supplied_source or directory / 'train.csv'
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
