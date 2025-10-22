from collections import Counter

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Ingredients, IngredientsInRecipes, Recipes,
    Subscription, Tags
)

User = get_user_model()


class FoodUserSerializer(UserSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + ('avatar', 'is_subscribed')
        read_only_fields = fields

    def get_is_subscribed(self, author):
        user = self.context['request'].user
        return user.is_authenticated and Subscription.objects.filter(
            user=user, author=author
        ).exists()


class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True, allow_null=True)

    class Meta:
        fields = ('avatar',)


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ('id', 'name', 'slug')


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = ('id', 'name', 'measurement_unit')


class IngredientsInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all(), source='ingredient'
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )
    amount = serializers.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        model = IngredientsInRecipes
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipesWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientsInRecipeSerializer(
        many=True, source='recipe_ingredients', required=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(), many=True, required=True
    )
    image = Base64ImageField(required=True, allow_null=False)
    cooking_time = serializers.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        model = Recipes
        fields = (
            'name',
            'ingredients',
            'image',
            'tags',
            'cooking_time',
            'text',
        )

    def validate(self, data):
        ingredients = data.get('recipe_ingredients')
        tags = data.get('tags')
        errors = {}
        if not ingredients:
            errors['ingredients'] = (
                'Необходимо добавить минимум один ингредиент'
            )
        if not tags:
            errors['tags'] = 'Необходимо добавить минимум один тег!'
        tag_ids = [tag.id for tag in tags]
        duplicates_tags = [
            tag for tag, count in Counter(tag_ids).items() if count > 1
        ]
        if duplicates_tags:
            duplicates_tag_names = [
                tag.name for tag in tags if tag.id in duplicates_tags
            ]
            errors['tags'] = (
                f'Следующие теги повторяются: '
                f'{", ".join(set(duplicates_tag_names))}.'
            )

        ingredient_ids = [item['ingredient'].id for item in ingredients]
        duplicates_ingredients = [
            i for i, count in Counter(ingredient_ids).items() if count > 1
        ]
        if duplicates_ingredients:
            duplicates_ingredients_names = [
                item['ingredient'].name for item in ingredients
                if item['ingredient'].id in duplicates_ingredients
            ]
            errors['ingredients'] = (
                f'Следующие ингредиенты повторяются: '
                f'{", ".join(set(duplicates_ingredients_names))}.'
            )
        if errors:
            raise serializers.ValidationError(errors)
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('tags')
        recipe = super().create(validated_data)
        recipe.tags.set(tags_data)
        ingredients_to_create = [
            IngredientsInRecipes(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount'],
            )
            for item in ingredients_data
        ]
        IngredientsInRecipes.objects.bulk_create(ingredients_to_create)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        if tags_data is not None:
            instance.tags.set(tags_data)
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
        ingredients_to_create = [
            IngredientsInRecipes(
                recipe=instance,
                ingredient=item['ingredient'],
                amount=item['amount'],
            )
            for item in ingredients_data
        ]
        IngredientsInRecipes.objects.bulk_create(ingredients_to_create)
        return instance

    def to_representation(self, instance):
        return RecipesReadSerializer(
            instance,
            context=self.context
        ).data

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError(
                'Поле image не может быть пустым!'
            )
        return image


class RecipesReadSerializer(serializers.ModelSerializer):
    author = FoodUserSerializer(read_only=True)
    ingredients = IngredientsInRecipeSerializer(
        many=True, source='recipe_ingredients', read_only=True
    )
    tags = TagsSerializer(read_only=True, many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = (
            'id',
            'author',
            'name',
            'ingredients',
            'image',
            'tags',
            'cooking_time',
            'text',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def check_existence(self, recipe, related_name):
        user = self.context['request'].user
        related_manager = getattr(recipe, related_name)
        return user.is_authenticated and related_manager.filter(
            user=user
        ).exists()

    def get_is_favorited(self, recipe):
        return self.check_existence(recipe, 'favorites')

    def get_is_in_shopping_cart(self, recipe):
        return self.check_existence(recipe, 'shopping_carts')


class SubscriptionSerializer(FoodUserSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.IntegerField(
        read_only=True,
        source='recipes.count'
    )

    class Meta:
        model = User
        fields = FoodUserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, author):
        request = self.context.get('request')
        limit = int(request.GET.get('recipes_limit', 10**10))
        return RecipeSimpleSerializer(
            author.recipes.all()[:limit],
            many=True,
            context={'request': request}
        ).data


class RecipeSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipes
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields
