from django.contrib import admin
from django.urls import include, path

from recipes.urls import short_link_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(short_link_patterns)),
    path('api/', include('api.urls')),
]
