import hashlib
import json
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand, CommandError

from etl.kaggle import KAGGLE_TRAIN_PATH
from risk_engine.evaluation import evaluate_native


class Command(BaseCommand):
    help = 'Compare native Kaggle models with separate train/validation/test partitions; never activate.'

    def add_arguments(self, parser):
        parser.add_argument('--csv-path', default=str(KAGGLE_TRAIN_PATH))
        parser.add_argument('--output', default='evaluation/kaggle_native.json')
        parser.add_argument('--seed', type=int, default=20261017)

    def handle(self, *args, **options):
        source = Path(options['csv_path'])
        output = Path(options['output'])
        if output.exists():
            raise CommandError('Evaluation output already exists. Choose a new output path to preserve evidence.')
        try:
            result = evaluate_native(pd.read_csv(source), seed=options['seed'], progress=self.stdout.write)
        except (ValueError, OSError) as exc:
            raise CommandError(str(exc)) from exc
        result['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2), encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'Saved evaluation to {output}. Test metrics: {result["test_metrics"]}'))
