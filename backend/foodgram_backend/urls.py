from django.contrib import admin
from django.urls import path, include
from api.views import ShortLinkRedirectView, RecipesViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'recipes', RecipesViewSet, basename='recipes')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include(router.urls)),
    path(
        's/<str:short_link>/',
        ShortLinkRedirectView.as_view(),
        name='short-redirect'
    )
]
