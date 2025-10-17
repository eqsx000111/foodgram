import base64
from collections import Counter

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from djoser.serializers import (
    SetPasswordSerializer as DjoserSetPasswordSerializer,
    UserCreateSerializer,
)
from rest_framework import serializers

from recipes.constant import USERNAME_MAX_LENGTH
from recipes.models import (
    Ingredients,
    IngredientsInRecipes,
    Recipes,
    Subscription,
    Tags,
)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if data == '' or data is None:
            raise serializers.ValidationError(
                'Поле image не может быть пустым'
            )
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
            return super().to_internal_value(data)


class CustomSetPasswordSerializer(DjoserSetPasswordSerializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Текущий пароль неверный !')
        return value

    def validate_new_password(self, value):
        validate_password(value, self.context['request'].user)
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        fields = (
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
        )


class FoodUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=USERNAME_MAX_LENGTH)
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )
        read_only_fields = fields

    def get_is_subscribed(self, author):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=author).exists()


class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True, allow_null=True)

    class Meta:
        fields = ('avatar',)


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ('id', 'name', 'slug')
        read_only_fields = fields


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
        cooking_time = data.get('cooking_time')
        errors = {}
        if not ingredients:
            errors['ingredients'] = (
                'Как мы будем готовить блюдо без ингредиентов?!'
            )
        if not tags:
            errors['tags'] = 'Нужно добавить минимум один тег!'
        if cooking_time < 1:
            errors['cooking_time'] = (
                'Время приготовления должно быть больше нуля!'
            )
        for item in ingredients:
            amount = item.get('amount')
            if amount < 1:
                errors['ingredients'] = (
                    'Количество ингредиента должно быть больше нуля!'
                )
        tag_ids = [tag.id for tag in tags]
        duplicates_tags = [
            tag for tag, count in Counter(tag_ids).items() if count > 1
        ]
        if duplicates_tags:
            errors['tags'] = 'Теги не должны повторяться.'

        ingredient_ids = [item['ingredient'].id for item in ingredients]
        duplicates_ingredients = [
            i for i, count in Counter(ingredient_ids).items() if count > 1
        ]
        if duplicates_ingredients:
            errors['ingredients'] = 'Ингредиенты не должны повторяться!'
        if errors:
            raise serializers.ValidationError(errors)
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipes.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        for item in ingredients_data:
            IngredientsInRecipes.objects.create(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount'],
            )
        return recipe

    def update(self, instance, validated_data):
        if 'recipe_ingredients' in validated_data:
            ingredients_data = validated_data.pop('recipe_ingredients')
            instance.recipe_ingredients.all().delete()
            for item in ingredients_data:
                IngredientsInRecipes.objects.create(
                    recipe=instance,
                    ingredient=item['ingredient'],
                    amount=item['amount'],
                )
        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
            instance.tags.set(tags_data)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagsSerializer(instance.tags, many=True).data
        representation['ingredients'] = IngredientsInRecipeSerializer(
            instance.recipe_ingredients.all(), many=True
        ).data
        return representation


class RecipesReadSerializer(serializers.ModelSerializer):
    author = FoodUserSerializer(read_only=True)
    ingredients = IngredientsInRecipeSerializer(
        many=True, source='recipe_ingredients', read_only=True
    )
    tags = TagsSerializer(read_only=True, many=True)
    image = Base64ImageField(read_only=True)
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

    def get_is_favorited(self, recipe):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return recipe.favorites.filter(user=user).exists()

    def get_is_in_shopping_cart(self, recipe):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return recipe.shopping_cart.filter(user=user).exists()


class SubscriptionSerializer(serializers.ModelSerializer):
    author = FoodUserSerializer(read_only=True)
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Subscription
        fields = ('author',)

    def get_recipes(self, subscription):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipe_limit')
        queryset = subscription.author.recipes.all()
        if recipes_limit:
            queryset = queryset[: int(recipes_limit)]
        return RecipeSimpleSerializer(
            queryset, many=True, context={'request': request}
        ).data

    def get_recipes_count(self, subscription):
        return subscription.author.recipes.count()

    def to_representation(self, instance):
        data = FoodUserSerializer(instance.author, context=self.context).data
        data['recipes'] = self.get_recipes(instance)
        data['recipes_count'] = self.get_recipes_count(instance)
        return data


class RecipeSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipes
        fields = ('id', 'name', 'image', 'cooking_time')
