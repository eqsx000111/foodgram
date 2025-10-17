import os

from django.conf import settings
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

FONT_PATH = os.path.join(settings.BASE_DIR, 'fonts', 'DejaVuSans.ttf')

if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont('DejaVuSans', FONT_PATH))
    DEFAULT_FONT = 'DejaVuSans'
else:
    DEFAULT_FONT = 'Helvetica'


def generate_shopping_list_pdf(ingredients):
    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'
    ] = 'attachment; filename="shopping_list.pdf"'

    p = canvas.Canvas(response, pagesize=A4)

    font_name = (
        'DejaVuSans'
        if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames()
        else 'Helvetica'
    )
    font_size = 12
    p.setFont(font_name, font_size)

    width, height = A4
    y = height - 50

    p.drawString(80, y, 'Список покупок')
    y -= 30

    for item in ingredients:
        line = f"{item['ingredient__name']} "
        f"({item['ingredient__measurement_unit']}) — {item['total_amount']}"
        p.drawString(60, y, line)
        y -= 18
        if y < 60:
            p.showPage()
            p.setFont(font_name, font_size)
            y = height - 50

    p.showPage()
    p.save()
    return response
