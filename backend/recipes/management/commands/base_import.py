import json

from django.core.management.base import BaseCommand


class BaseImportCommand(BaseCommand):
    """Базовый класс для импорта данных из JSON."""
    help = 'Импорт данных из JSON в указанную модель'
    model = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Путь к JSON-файлу'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
            items_list = self.model.objects.bulk_create(
                [self.model(**item) for item in data], ignore_conflicts=True,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Загружено {len(items_list)} '
                    f'записей из {file_path}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при загрузке файла {file_path}: {e}')
            )
