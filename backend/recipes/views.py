from django.shortcuts import redirect
from rest_framework.exceptions import NotFound

from .models import Recipes


def short_link_redirect(request, pk):
    if not Recipes.objects.filter(pk=pk).exists():
        raise NotFound('Страница не найдена')
    return redirect(request.build_absolute_uri(f'/recipes/{pk}'))
