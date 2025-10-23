from datetime import datetime
from io import BytesIO

from django.http import FileResponse
from django.template.loader import render_to_string


def generate_shopping_list(ingredients, user, recipes):
    context = {
        'user': user,
        'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'ingredients': ingredients,
        'recipes': recipes
    }
    return FileResponse(
        BytesIO(
            render_to_string('shopping_list.txt', context).encode('utf-8')
        ),
        as_attachment=True,
        filename='shopping_list.txt',
        content_type='text/plain'
    )
