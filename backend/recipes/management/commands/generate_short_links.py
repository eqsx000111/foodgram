from django.core.management.base import BaseCommand

from recipes.models import Recipes


class Command(BaseCommand):
    help = 'Генерирует короткие ссылки для рецептов, у которых их нет'

    def handle(self, *args, **options):
        recipes_without_links = Recipes.objects.filter(
            short_link__isnull=True
        )
        count = recipes_without_links.count()
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('Все рецепты уже имеют короткие ссылки!')
            )
            return
        self.stdout.write(f'Найдено {count} рецептов без коротких ссылок')
        generated_links = set()
        for recipe in recipes_without_links:
            while True:
                short_link = recipe.generate_short_link()
                if short_link not in generated_links:
                    if not Recipes.objects.filter(
                        short_link=short_link
                    ).exists():
                        generated_links.add(short_link)
                        break
            recipe.short_link = short_link
            recipe.save(update_fields=['short_link'])
            self.stdout.write(
                self.style.SUCCESS(f'Рецепт "{recipe.name}" -> {short_link}')
            )
        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно создано {len(generated_links)} коротких ссылок!'
            )
        )
