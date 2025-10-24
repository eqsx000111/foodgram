from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from .filters import IsInRecipesFilter
from .models import (
    Favorites, FoodUser, Ingredients, IngredientsInRecipes, Recipes,
    Subscription, Tags, ShoppingCart
)


admin.site.unregister(Group)


class RecipesCount:

    @admin.display(description='в рецептах')
    def get_recipes_count(self, obj):
        return obj.recipes.count()


class ShoppingCartInline(admin.TabularInline):
    model = ShoppingCart
    extra = 0
    can_delete = True
    fields = ('recipe', 'recipe_author')
    readonly_fields = ('recipe_author',)

    @admin.display(description='Автор рецепта')
    def recipe_author(self, obj):
        return obj.recipe.author.username


class FavoritesInline(admin.TabularInline):
    model = Favorites
    extra = 0
    can_delete = True
    verbose_name = 'Рецепт'
    verbose_name_plural = 'Избранное'


@admin.register(FoodUser)
class FoodUserAdmin(UserAdmin, RecipesCount):
    list_display = (
        'id',
        'username',
        'get_full_name',
        'email',
        'get_avatar',
        'get_recipes_count',
        'subscriptions_count',
        'subscribers_count',

    )
    readonly_fields = ('get_avatar',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('username', 'password')
        }),
        ('Персональная информация', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Настройка аватара', {
            'fields': ('avatar', 'get_avatar')
        }),
    )
    inlines = [ShoppingCartInline, FavoritesInline]
    search_fields = ('username', 'email', 'first_name', 'last_name')

    @admin.display(description='ФИО')
    def get_full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description='Аватар')
    @mark_safe
    def get_avatar(self, user):
        if user.avatar and hasattr(user.avatar, 'url'):
            return f'<img src="{user.avatar.url}" width="50" height="50"/>'
        return '—'

    @admin.display(description='подписок')
    def subscriptions_count(self, user):
        return user.followers.count()

    @admin.display(description='подписчиков')
    def subscribers_count(self, user):
        return user.authors.count()


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
class IngredientsAdmin(admin.ModelAdmin, RecipesCount):
    list_display = (
        'name',
        'measurement_unit',
        'get_recipes_count',
    )
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit', IsInRecipesFilter)
    ordering = ('name',)


@admin.register(Recipes)
class RecipesAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'cooking_time',
        'get_favorites_count',
        'get_ingredients_in_recipe',
        'get_tags',
        'get_image',
    )
    list_filter = ('tags', 'cooking_time', 'author')
    search_fields = ('name', 'author__username')
    ordering = ('-pub_date',)
    inlines = [IngredientsInRecipesInline]
    readonly_fields = ('get_image',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'author', 'text', 'cooking_time')
        }),
        ('Изображение', {
            'fields': ('image', 'get_image'),
        }),
        ('Теги', {
            'fields': ('tags',)
        }),
    )

    @admin.display(description=' продуктов')
    def get_ingredients_count(self, recipe):
        return recipe.recipe_ingredients.count()

    @admin.display(description='В избранном')
    def get_favorites_count(self, recipe):
        return recipe.favorites.count()

    @mark_safe
    @admin.display(description='Продукты')
    def get_ingredients_in_recipe(self, recipe):
        return '<br>'.join(
            f'{i.ingredient.name} {i.amount} ({i.ingredient.measurement_unit})'
            for i in recipe.recipe_ingredients.all()
        )

    @mark_safe
    @admin.display(description='Теги')
    def get_tags(self, recipe):
        return '<br>'.join(
            tag.name for tag in recipe.tags.all()
        )

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
class TagsAdmin(admin.ModelAdmin, RecipesCount):
    list_display = ('name', 'slug', 'get_recipes_count')
    readonly_fields = ('get_recipes_count',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'get_user_cart_count',
    )

    @admin.display(description='в корзине')
    def get_user_cart_count(self, obj):
        return obj.user.shopping_carts.count()


@admin.register(Favorites)
class FavoritesAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'get_favorites_count'
    )

    @admin.display(description='в избранном')
    def get_favorites_count(self, obj):
        return obj.user.favorites.count()
