from django.contrib import admin

from .models import (
    Recipes,
    Subscription,
    Ingredients,
    FoodUser,
    Tags,
    IngredientsInRecipes
)


@admin.register(FoodUser)
class FoodUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email')


@admin.register(Subscription)
class SubscribtionAdmin(admin.ModelAdmin):

    list_display = ('user', 'author',)
    search_fields = ('user__username', 'author__username',)
    list_filter = ('user', 'author',)


class IngredientsInRecipesInline(admin.TabularInline):
    model = IngredientsInRecipes
    extra = 1
    min_num = 1
    fields = ('ingredient', 'amount')
    autocomplete_fields = ['ingredient']


@admin.register(Ingredients)
class IngredientsAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    ordering = ('name',)


@admin.register(Recipes)
class RecipesAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time', 'get_ingredients_count')
    list_filter = ('tags', 'cooking_time', 'author')
    search_fields = ('name', 'description', 'author__username')
    filter_horizontal = ('tags',)
    inlines = [IngredientsInRecipesInline]
    fields = (
        'name',
        'author',
        'description',
        'image',
        'cooking_time',
        'tags',
    )

    def get_ingredients_count(self, obj):
        return obj.recipe_ingredients.count()
    get_ingredients_count.short_description = 'Кол-во ингредиентов'


@admin.register(IngredientsInRecipes)
class IngredientsInRecipesAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    list_filter = ('recipe', 'ingredient')
    search_fields = ('recipe__name', 'ingredient__name')
    autocomplete_fields = ['recipe', 'ingredient']


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

