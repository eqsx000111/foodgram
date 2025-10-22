from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (
    AllowAny, IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.validators import ValidationError

from .filters import IngredientsFilter, RecipesFilter
from recipes.models import (
    Favorites, Ingredients, IngredientsInRecipes,
    Recipes, ShoppingCart, Subscription, Tags
)
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer, FoodUserSerializer,
    IngredientsSerializer, RecipeSimpleSerializer,
    RecipesReadSerializer, RecipesWriteSerializer,
    SubscriptionSerializer, TagsSerializer
)
from .services import generate_shopping_list

User = get_user_model()


class FoodUserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        return self.queryset

    @action(
        detail=False,
        methods=['get'],
        url_path='me',
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        return Response(
            FoodUserSerializer(
                request.user,
                context={'request': request}
            ).data
        )

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.avatar = serializer.validated_data['avatar']
        user.save()
        return Response(
            {'avatar': request.build_absolute_uri(user.avatar.url)}
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        user = request.user
        if request.method == 'DELETE':
            get_object_or_404(Subscription, user=user, author_id=id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        author = get_object_or_404(User, id=id)
        if user == author:
            raise ValidationError(
                {'errors': 'Нельзя подписаться на самого себя!'}
            )
        subscription, _ = Subscription.objects.get_or_create(
            user=user, author=author
        )
        if not _:
            raise ValidationError({'errors': 'Уже подписаны!'})
        serializer = SubscriptionSerializer(
            subscription.author, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(authors__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipes.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipesReadSerializer
        return RecipesWriteSerializer

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        if not self.queryset.filter(pk=pk).exists():
            raise NotFound('Рецепт не найден!')
        short_url = request.build_absolute_uri(
            reverse('recipe-short-link', kwargs={'pk': pk})
        )
        return Response({'short-link': short_url})

    @staticmethod
    def favorite_shopping_cart_related(
        model, user, recipe_id, serializer_class, method_name
    ):
        recipe = get_object_or_404(Recipes, pk=recipe_id)
        if method_name == 'POST':
            _, created = model.objects.get_or_create(
                user=user, recipe=recipe
            )
            if not created:
                raise ValidationError(
                    {'errors': f'Рецепт {recipe.name} - уже добавлен!'}
                )
            serializer = serializer_class(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        delete, _ = model.objects.filter(
            user=user, recipe_id=recipe_id
        ).delete()
        if not delete:
            raise NotFound('Запись не найдена')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=[IsAuthenticated],
        pagination_class=None,
    )
    def favorite(self, request, pk=None):
        return self.favorite_shopping_cart_related(
            model=Favorites,
            user=request.user,
            recipe_id=pk,
            serializer_class=RecipeSimpleSerializer,
            method_name=request.method
        )

    @action(
        detail=True,
        methods=['get', 'post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk):
        return self.favorite_shopping_cart_related(
            model=ShoppingCart,
            user=request.user,
            recipe_id=pk,
            serializer_class=RecipeSimpleSerializer,
            method_name=request.method
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request, pk=None):
        user = request.user
        ingredients = (
            IngredientsInRecipes.objects.filter(
                recipe__shopping_carts__user=user
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        recipes = (
            Recipes.objects.filter(shopping_carts__user=user)
            .values('name', 'author__username')
            .distinct()
        )
        return generate_shopping_list(ingredients, user, recipes)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientsFilter
    search_fields = '^name'


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    pagination_class = None
