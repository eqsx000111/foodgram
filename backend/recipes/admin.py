from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from .filters import IsInRecipesFilter
from .models import (
    FoodUser, Ingredients, IngredientsInRecipes, Recipes,
    Subscription, Tags
)


class RelatedCountMixin:

    @staticmethod
    def get_related_count(obj, related_name):
        return getattr(obj, related_name).count()


@admin.register(FoodUser)
class FoodUserAdmin(UserAdmin, RelatedCountMixin):
    list_display = (
        'id',
        'username',
        'get_full_name',
        'email',
        'get_avatar',
        'recipes_count',
        'subscriptions_count',
        'subscribers_count',

    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('get_avatar',)

    @admin.display(description='ФИО')
    def get_full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description='Аватар')
    @mark_safe
    def get_avatar(self, user):
        return f'<img src="{user.avatar.url}" width="50" height="50"/>'

    @admin.display(description='рецептов')
    def recipes_count(self, user):
        return self.get_related_count(user, 'recipes')

    @admin.display(description='подписок')
    def subscriptions_count(self, user):
        return self.get_related_count(user, 'followers')

    @admin.display(description='подписчиков')
    def subscribers_count(self, user):
        return self.get_related_count(user, 'authors')


@admin.register(Subscription)
class SubscribtionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'author',
    )
    search_fields = (
        'user__username',
        'author__username',
    )


class IngredientsInRecipesInline(admin.TabularInline):
    model = IngredientsInRecipes
    extra = 1
    min_num = 1
    fields = ('ingredient', 'amount')
    autocomplete_fields = ['ingredient']


@admin.register(Ingredients)
class IngredientsAdmin(admin.ModelAdmin, RelatedCountMixin):
    list_display = (
        'name',
        'measurement_unit',
        'get_recipes_count',
    )
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit', IsInRecipesFilter)
    ordering = ('name',)

    def get_recipes_count(self, ingredients):
        return self.get_related_count(ingredients, 'recipes')


@admin.register(Recipes)
class RecipesAdmin(admin.ModelAdmin, RelatedCountMixin):
    list_display = (
        'id',
        'name',
        'cooking_time',
        'author',
        'get_favorites_count',
        'get_ingredients_in_recipe',
        'get_tags',
        'get_image',
        'get_ingredients_count',
    )
    list_filter = ('tags', 'cooking_time', 'author')
    search_fields = ('name', 'author__username')
    filter_horizontal = ('tags',)
    ordering = ('-pub_date',)
    inlines = [IngredientsInRecipesInline]
    fields = (
        'name',
        'author',
        'text',
        'image',
        'cooking_time',
        'tags',
    )

    @admin.display(description='Кол-во продуктов')
    def get_ingredients_count(self, recipe):
        return self.get_related_count(recipe, 'recipe_ingredients')

    @admin.display(description='В избранном')
    def get_favorites_count(self, recipe):
        return self.get_related_count(recipe, 'favorites')

    @mark_safe
    @admin.display(description='Продукты')
    def get_ingredients_in_recipe(self, recipe):
        return '<br>'.join(
            f'{i.name} {i.amount} ({i.measurement_unit})'
            for i in recipe.ingredients.all()
        )

    @admin.display(description='Теги')
    def get_tags(self, recipe):
        return recipe.tags.all()

    @mark_safe
    @admin.display(description='Картинка')
    def get_image(self, recipe):
        if recipe.image:
            return f'<img src="{recipe.image.url}" width="80" />'
        return '-'


@admin.register(IngredientsInRecipes)
class IngredientsInRecipesAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    list_filter = ('recipe', 'ingredient')
    search_fields = ('recipe__name', 'ingredient__name')
    autocomplete_fields = ['recipe', 'ingredient']


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin, RelatedCountMixin):
    list_display = ('name', 'slug', 'get_tags_in_recipes_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description='в рецептах')
    def get_tags_in_recipes_count(self, tags):
        return self.get_related_count(tags, 'recipes')
