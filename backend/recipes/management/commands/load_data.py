import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredients, Tags


class BaseImportCommand(BaseCommand):
    """Базовый класс для импорта данных из JSON."""
    model = None
    fields = []

    def load_data(self, file_path):
        """Считывает JSON и возвращает список объектов модели."""
        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        return [
            self.model(**{field: item[field] for field in self.fields})
            for item in data
        ]

    def import_data(self, file_path):
        """Основная логика импорта с bulk_create."""
        objs = self.load_data(file_path)
        self.model.objects.bulk_create(objs, ignore_conflicts=True)
        return len(objs)


class Command(BaseImportCommand):
    help = 'Импортирует ингредиенты или теги из JSON-файла.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Путь к JSON-файлу'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['ingredients', 'tags'],
            required=True,
            help='Тип данных: ingredients или tags'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        data_type = options['type']

        try:
            if data_type == 'ingredients':
                self.model = Ingredients
                self.fields = ['name', 'measurement_unit']
            elif data_type == 'tags':
                self.model = Tags
                self.fields = ['name', 'slug']

            count = self.import_data(file_path)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Загружено {count} записей {data_type} из {file_path}'
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при загрузке: {e}'))
