from django.shortcuts import redirect
from django.http import Http404

from .models import Recipes


def short_link_redirect(request, pk):
    if not Recipes.objects.filter(pk=pk).exists():
        raise Http404(f'Рецепт с id={pk} не найден')
    return redirect(f'/recipes/{pk}')
