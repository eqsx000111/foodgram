from djoser.views import UserViewSet as DjoserUserViewSet

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import RedirectView
from django.views.generic.detail import SingleObjectMixin
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from recipes.models import (
    Favorites,
    Ingredients,
    IngredientsInRecipes,
    Recipes,
    ShoppingCart,
    Tags,
    Subscription
)

from .permissions import IsAuthorOrAdminOrReadOnly, IsAdminOrReadOnly, IsAdminOrOwner
from .filters import IngredientsFilter, RecipesFilter
from .serializers import (
    FoodUserSerializer,
    CustomUserCreateSerializer,
    AvatarSerializer,
    SubscriptionSerializer,
    IngredientsSerializer,
    RecipeSimpleSerializer,
    RecipesReadSerializer,
    RecipesWriteSerializer,
    TagsSerializer,
    CustomSetPasswordSerializer
)
from .services import generate_shopping_list_pdf

User = get_user_model()


class FoodUserViewSet(DjoserUserViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly,]
    pagination_class = (LimitOffsetPagination)

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        elif self.action == 'avatar':
            return AvatarSerializer
        return FoodUserSerializer

    def get_permissions(self):
        if self.action in ['create', 'retrieve', 'list']:
            permission_classes = [AllowAny]
        elif self.action in [
            'avatar', 'subscriptions', 'subscribe', 'set_password'
        ]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return User.objects.all()

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAdminOrOwner]
    )
    def set_password(self, request):
        serializer = CustomSetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                'detail': 'Пароль успешно изменен !'
            }, status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['get'], url_path='me', permission_classes=[IsAdminOrOwner])
    def me(self, request):
        serializer = FoodUserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAdminOrOwner]
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user.avatar = serializer.validated_data['avatar']
            user.save()
            return Response(
                {'avatar': request.build_absolute_uri(user.avatar.url)}
            )
        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription, _ = Subscription.objects.get_or_create(
                user=user,
                author=author
            )
            if not _:
                return Response(
                    {
                        'errors': 'Вы уже подписаны на этого автора!'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SubscriptionSerializer(
                subscription, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Subscription.objects.filter(
            user=user,
            author=author
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Подписка не найдена'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAdminOrOwner]
    )
    def subscriptions(self, request):
        queryset = Subscription.objects.filter(user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipes.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def list(self, request, *args, **kwargs):
        user = request.user
        recipe = request.query_params.get('is_favorited')
        if recipe:
            try:
                recipe = int(recipe)
            except ValueError:
                return Response({'error': 'Некорректный id рецепта'}, status=status.HTTP_400_BAD_REQUEST)
            if not user.is_authenticated:
                return Response({'error': 'Авторизуйтесь для просмотра избранного!'}, status=status.HTTP_401_UNAUTHORIZED)
            return Response({'is_favorited': Favorites.objects.filter(user=user, recipe=recipe).exists()})
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save(author=request.user)
        write_serializer = RecipesWriteSerializer(recipe, context={'request': request})
        return Response(write_serializer.data, status=status.HTTP_201_CREATED)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipesReadSerializer
        return RecipesWriteSerializer

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        if not recipe.short_link:
            recipe.short_link = recipe.generate_short_link()
            recipe.save()
        short_url = request.build_absolute_uri(f'/s/{recipe.short_link}/')
        return Response({'short_url': short_url})

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=[IsAdminOrOwner],
        pagination_class=None
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipes, pk=pk)
        user = self.request.user
        if request.method == 'GET':
            if not user.is_authenticated:
                return Response({'is_favorited': False})
            is_favorited = Favorites.objects.filter(user=user, recipe=recipe).exists()
            return Response({'is_favorited': is_favorited})
        if request.method == 'POST':
            favorite, _ = Favorites.objects.get_or_create(
                user=user, recipe=recipe
            )
            if not _:
                return Response(
                    {'errors': 'Уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = RecipeSimpleSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        delete, _ = Favorites.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if not delete:
            return Response(
                {'errors': 'Не было в избранном'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[IsAdminOrOwner]
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipes, pk=pk)
        if request.method == 'POST':
            is_in_shopping_cart, _ = ShoppingCart.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if not _:
                return Response(
                    {'errors': 'Уже добавленно в список покупок'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = RecipeSimpleSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        delete, _ = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if not delete:
            return Response(
                {'errors': 'Не было в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAdminOrOwner]
    )
    def download_shopping_cart(self, request, pk=None):
        user = request.user
        ingredients = (
            IngredientsInRecipes.objects.filter(
                recipe__shopping_cart__user=user
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        if not ingredients.exists():
            return Response({'errors': 'Список покупок пуст'}, status=400)
        return generate_shopping_list_pdf(ingredients)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientsFilter
    search_fields = ('^name')


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    pagination_class = None


class ShortLinkRedirectView(SingleObjectMixin, RedirectView):
    model = Recipes
    slug_field = 'short_link'
    slug_url_kwarg = 'short_link'

    def get_redirect_url(self, *args, **kwargs):
        recipe = get_object_or_404(
            Recipes, short_link=self.kwargs['short_link']
        )
        redirect_url = reverse('recipes-detail', kwargs={'pk': recipe.pk})
        return redirect_url

    def get_queryset(self):
        return self.model.objects.filter(short_link=self.kwargs['short_link'])
