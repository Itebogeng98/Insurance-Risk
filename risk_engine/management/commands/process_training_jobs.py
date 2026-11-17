import logging
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import close_old_connections

from risk_engine.models import TrainingDataset

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process persisted training jobs outside web requests.'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true')
        parser.add_argument('--recover-interrupted', action='store_true',
                            help='Only for a single worker deployment: fail jobs interrupted by restart.')

    def handle(self, *args, **options):
        if options['recover_interrupted']:
            count = TrainingDataset.objects.filter(status='RUNNING').update(
                status='FAILED',
                error_message='Training interrupted by service restart. Upload the dataset again to retry.',
            )
            self.stdout.write(f'Training worker ready; {count} interrupted jobs marked failed.')
        while True:
            close_old_connections()
            dataset = TrainingDataset.objects.filter(status='QUEUED').order_by('pk').first()
            if dataset and TrainingDataset.objects.filter(pk=dataset.pk, status='QUEUED').update(status='RUNNING'):
                try:
                    call_command('train_risk_model', csv_path=dataset.csv_file.path,
                                 dataset_id=dataset.pk, stdout=self.stdout)
                except Exception:
                    logger.exception('Training failed for dataset %s', dataset.pk)
                    TrainingDataset.objects.filter(pk=dataset.pk).update(
                        status='FAILED', error_message='Training failed. Check worker logs before retrying.',
                    )
            if options['once']:
                return
            if dataset is None:
                time.sleep(5)
