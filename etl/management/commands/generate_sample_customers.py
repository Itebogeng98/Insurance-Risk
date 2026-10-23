from django.core.management.base import BaseCommand, CommandParser

from etl.synthetic import generate_synthetic_applicants


class Command(BaseCommand):
    help = 'Generate a local development applicant CSV shaped for the import_applicants command.'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('output_path')
        parser.add_argument('--rows', type=int, default=50)
        parser.add_argument('--seed', type=int, default=None)

    def handle(self, *args, **options) -> None:
        df = generate_synthetic_applicants(options['rows'], seed=options['seed'])
        df.to_csv(options['output_path'], index=False)
        self.stdout.write(self.style.SUCCESS(
            f'Wrote {len(df)} local development applicant rows to {options["output_path"]}'
        ))
