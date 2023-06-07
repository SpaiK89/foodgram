from .views import UsersViewSet, TagsViewSet, RecipeViewSet, IngredientsViewSet
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router_v1 = DefaultRouter()

router_v1.register('users', UsersViewSet, basename='users')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('tags', TagsViewSet, basename='tags')
router_v1.register('ingredients', IngredientsViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]