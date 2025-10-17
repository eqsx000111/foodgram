import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredients, Tags


class Command(BaseCommand):
    help = 'Загружает ингредиенты или теги из CSV файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', type=str, required=True, help='Путь к CSV-файлу'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['ingredients', 'tags'],
            required=True,
            help='Тип данных для загрузки: ingredients или tags',
        )

    def handle(self, *args, **options):
        file_path = options['file']
        data_type = options['type']

        try:
            with open(file_path, encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                count = 0

                if data_type == 'ingredients':
                    for row in reader:
                        if not row or len(row) < 2:
                            continue
                        name, measurement_unit = row[0].strip(), row[1].strip()
                        Ingredients.objects.get_or_create(
                            name=name, measurement_unit=measurement_unit
                        )
                        count += 1

                elif data_type == 'tags':
                    for row in reader:
                        if not row or len(row) < 3:
                            continue
                        name, slug = row[0].strip(), row[1].strip()
                        Tags.objects.get_or_create(name=name, slug=slug)
                        count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Загружено {count} записей {data_type} из {file_path}'
                    )
                )

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Файл не найден: {file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при загрузке: {e}'))
