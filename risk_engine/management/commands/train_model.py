from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = 'Alias for train_risk_model, matching the Assignment 3 deployment documentation.'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--rows', type=int, default=5000)
        parser.add_argument('--seed', type=int, default=42)
        parser.add_argument('--activate', action='store_true')

    def handle(self, *args, **options) -> None:
        call_command(
            'train_risk_model',
            rows=options['rows'],
            seed=options['seed'],
            activate=options['activate'],
        )
