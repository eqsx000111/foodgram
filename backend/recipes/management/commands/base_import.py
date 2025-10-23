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

            objs = []
            for item in data:
                obj_data = {**item}
                objs.append(self.model(**obj_data))

            self.model.objects.bulk_create(objs, ignore_conflicts=True)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Загружено {len(objs)} записей из {file_path}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при загрузке файла {file_path}: {e}')
            )
