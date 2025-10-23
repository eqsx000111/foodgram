from django.contrib import admin


class IsInRecipesFilter(admin.SimpleListFilter):
    title = 'Есть в рецептах'
    parameter_name = 'is_in_recipes'
    LOOKUPS = (
        ('yes', 'Да'),
        ('no', 'Нет'),
    )

    def lookups(self, request, model_admin):
        return self.LOOKUPS

    def queryset(self, request, ingredients):
        if self.value() == 'yes':
            return ingredients.filter(
                recipe_ingredients__isnull=False
            ).distinct()
        if self.value() == 'no':
            return ingredients.filter(
                recipe_ingredients__isnull=True
            )
        return ingredients
