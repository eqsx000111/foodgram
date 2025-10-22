from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (FoodUserViewSet, IngredientsViewSet, RecipesViewSet,
                    TagsViewSet)

router = DefaultRouter()
router.register(r'recipes', RecipesViewSet, basename='recipes')
router.register(r'users', FoodUserViewSet, basename='users')
router.register(r'ingredients', IngredientsViewSet, basename='ingredients')
router.register(r'tags', TagsViewSet, basename='tags')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
