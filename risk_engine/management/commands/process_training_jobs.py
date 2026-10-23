import logging
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand

from risk_engine.models import TrainingDataset

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process persisted training jobs outside web requests.'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true')

    def handle(self, *args, **options):
        while True:
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
