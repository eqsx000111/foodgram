from recipes.models import Tags
from recipes.management.commands.base_import import BaseImportCommand


class Command(BaseImportCommand):
    help = 'Загружает теги из JSON-файла'
    model = Tags
    fields = ['name', 'slug']
