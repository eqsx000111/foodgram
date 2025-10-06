import django_filters

from recipes.models import Ingredients, Recipes


class IngredientsFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Ingredients
        fields = ('name',)


class RecipesFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    author = django_filters.CharFilter(
        field_name='author', lookup_expr='icontains'
    )

    class Meta:
        models = Recipes
        fields = ('name', 'author')
