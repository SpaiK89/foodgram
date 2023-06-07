from django.contrib import admin

from foodgram.settings import VALUE_DISPLAY
from .models import Tag, QuantityIngredient, Ingredient, Recipe, Favorite


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Отображает теги в панели администратора."""
    list_display = ('name', 'slug', 'color')
    search_fields = ('name',)
    empty_value_display = VALUE_DISPLAY


class IngredientInline(admin.TabularInline):
    model = QuantityIngredient
    extra = 1


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Отображает ингредиенты в панели администратора."""
    list_display = ('name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('name',)
    empty_value_display = VALUE_DISPLAY


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Отображает рецепты в панели администратора."""
    list_display = ('author', 'name', 'cooking_time')
    search_fields = ('name', 'author', 'tags')
    list_filter = ('author', 'name', 'tags')
    inlines = (IngredientInline,)
    empty_value_display = VALUE_DISPLAY

    def count_favorites(self, obj):
        return obj.favorites.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Отображает подписки на авторов в панели администратора."""
    list_display = ('user', 'recipe')
    search_fields = ('user',)
    list_filter = ('user',)
    empty_value_display = VALUE_DISPLAY
