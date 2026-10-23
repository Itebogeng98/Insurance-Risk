from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = 'Alias for import_applicants, matching the Assignment 3 deployment documentation.'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('csv_path')
        parser.add_argument('--created-by', default='admin')

    def handle(self, *args, **options) -> None:
        call_command(
            'import_applicants',
            options['csv_path'],
            created_by=options['created_by'],
        )
