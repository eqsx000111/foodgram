from recipes.models import Ingredients
from recipes.management.commands.base_import import BaseImportCommand


class Command(BaseImportCommand):
    help = 'Загружает продукты из JSON-файла'
    model = Ingredients
