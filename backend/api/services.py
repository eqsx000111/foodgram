from datetime import datetime

from django.template.loader import render_to_string


def generate_shopping_list(ingredients, user, recipes):
    context = {
        'user': user,
        'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'ingredients': ingredients,
        'recipes': recipes
    }
    return render_to_string('shopping_list.txt', context)
