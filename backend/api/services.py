from datetime import datetime
from django.http import HttpResponse
from django.template.loader import render_to_string


def generate_shopping_list(ingredients, user, recipes):
    context = {
        'user': user,
        'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'recipes': recipes,
        'ingredients': ingredients
    }
    content = render_to_string('shopping_list.txt', context)
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=shopping_list.txt'
    return response
    
