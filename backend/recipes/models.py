import string
import random
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.conf import settings


from .constant import (
    USERNAME_MAX_LENGTH,
    USERNAME_PATTERN,
    EMAIL_MAX_LENGTH,
    FIRST_NAME_MAX_LENGTH,
    LAST_NAME_MAX_LENGTH,
    TAG_MAX_LENGTH,
    SLUG_MAX_LENGTH,
    SLUG_PATTERN,
    INGREDIENTS_NAME_MAX_LENGTH,
    MEASUREMENT_UNIT_MAX_LENGTH,
    RECIPES_MAX_LENGTH,
    SHORT_LINK_MAX_LENGTH,
)


def user_avatar_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'users/avatars/user_{instance.id}/avatar.{ext}'


class FoodUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)


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

    objects = FoodUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
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
        validators=[
            RegexValidator(regex=SLUG_PATTERN),
        ],
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
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('-name',)

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
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(Tags, verbose_name='Теги')
    image = models.ImageField(
        upload_to='recipes/images/', verbose_name='Картинка'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (мин)'
    )
    short_link = models.CharField(
        max_length=SHORT_LINK_MAX_LENGTH,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Короткая ссылка',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации рецепта'
    )

    def save(self, *args, **kwargs):
        if not self.pk and not self.short_link:
            self.short_link = self.generate_short_link()
        super().save(*args, **kwargs)

    def generate_short_link(self):
        length = 6
        characters = string.ascii_letters + string.digits
        while True:
            short_link = ''.join(
                random.choice(characters) for _ in range(length)
            )
            if not Recipes.objects.filter(short_link=short_link).exists():
                return short_link

    def get_short_link(self):
        if self.short_link:
            return f'{self.short_link}'
        return None

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class IngredientsInRecipes(models.Model):
    recipe = models.ForeignKey(
        Recipes, on_delete=models.CASCADE, related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes'
    )
    amount = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'recipe',
                    'ingredient'
                ], name='unique_recipe_ingredient'
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
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
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


class Favorites(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipes, on_delete=models.CASCADE, verbose_name='Рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite'
            ),
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorites'

    def __str__(self):
        return f'{self.user} -> {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='shopping_cart',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_cart'
            ),
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'{self.user} -> {self.recipe}'
