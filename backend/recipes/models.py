from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from .constant import (
    EMAIL_MAX_LENGTH, FIRST_NAME_MAX_LENGTH,
    INGREDIENTS_NAME_MAX_LENGTH, LAST_NAME_MAX_LENGTH,
    MEASUREMENT_UNIT_MAX_LENGTH, RECIPES_MAX_LENGTH,
    SLUG_MAX_LENGTH, TAG_MAX_LENGTH, USERNAME_MAX_LENGTH,
    USERNAME_PATTERN
)


def user_avatar_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'users/avatars/user_{instance.id}/avatar.{ext}'


class FoodUser(AbstractUser):
    username = models.CharField(
        unique=True,
        max_length=USERNAME_MAX_LENGTH,
        verbose_name='Никнейм',
        validators=[
            RegexValidator(regex=USERNAME_PATTERN),
        ],
    )
    email = models.EmailField(
        unique=True,
        max_length=EMAIL_MAX_LENGTH,
        verbose_name='Адрес электронной почты',
    )
    first_name = models.CharField('Имя', max_length=FIRST_NAME_MAX_LENGTH)
    last_name = models.CharField('Фамилия', max_length=LAST_NAME_MAX_LENGTH)
    avatar = models.ImageField(upload_to=user_avatar_path)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name'
    ]

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('-username',)

    def __str__(self):
        return self.username


class Tags(models.Model):
    name = models.CharField(
        unique=True, max_length=TAG_MAX_LENGTH, verbose_name='Название'
    )
    slug = models.SlugField(
        unique=True,
        max_length=SLUG_MAX_LENGTH,
        verbose_name='Слаг',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Ingredients(models.Model):
    name = models.CharField(
        max_length=INGREDIENTS_NAME_MAX_LENGTH, verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ('-name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipes(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    name = models.CharField(
        verbose_name='Название', max_length=RECIPES_MAX_LENGTH
    )
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredients,
        through='IngredientsInRecipes',
        verbose_name='Продукты',
    )
    tags = models.ManyToManyField(Tags, verbose_name='Теги')
    image = models.ImageField(
        upload_to='recipes/images/', verbose_name='Картинка'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (мин)',
        validators=[MinValueValidator(1)]
    )
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации рецепта'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class IngredientsInRecipes(models.Model):
    recipe = models.ForeignKey(
        Recipes, on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredients, on_delete=models.CASCADE,
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'Продукт в рецепте'
        verbose_name_plural = 'Продукты в рецептах'
        default_related_name = 'recipe_ingredients'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (
            f'{self.ingredient.name} — '
            f'{self.amount} {self.ingredient.measurement_unit}'
        )


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Подписчики',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Авторы',
    )

    class Meta:
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_follow',
            ),
        ]

    def __str__(self):
        return f'{self.user.username} follows {self.author.username}'


class UserRecipeBaseModel(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(app_label)s_%(class)s'
            ),
        ]

    def __str__(self):
        return f'{self.user} -> {self.recipe}'


class Favorites(UserRecipeBaseModel):
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorites'


class ShoppingCart(UserRecipeBaseModel):
    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_carts'
