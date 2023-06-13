import os
from django.contrib import admin

from dotenv import load_dotenv
from .models import (Tag, IngredientAmount, Ingredient, Recipe, Favorite,
                     ShoppingCart)

load_dotenv()

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Отображает теги в панели администратора."""
    list_display = ('name', 'slug', 'color')
    search_fields = ('name',)
    empty_value_display = os.getenv('VALUE_DISPLAY', '---')


class IngredientInline(admin.TabularInline):
    model = IngredientAmount
    extra = 1


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Отображает ингредиенты в панели администратора."""
    list_display = ('name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('name',)
    save_on_top = True
    empty_value_display = os.getenv('VALUE_DISPLAY', '---')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Отображает рецепты в панели администратора."""
    list_display = ('author', 'name', 'cooking_time', 'count_favorites')
    search_fields = ('name', 'author', 'tags')
    list_filter = ('author', 'name', 'tags')
    inlines = (IngredientInline,)
    empty_value_display = os.getenv('VALUE_DISPLAY', '---')

    @staticmethod
    def count_favorites(obj):
        return obj.favorites.count()

    count_favorites.short_description = "Добавлено в избранное"


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Отображает подписки на авторов в панели администратора."""
    list_display = ('user', 'recipe')
    search_fields = ('user',)
    list_filter = ('user',)
    empty_value_display = os.getenv('VALUE_DISPLAY', '---')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Отображает список покупок в панели администратора."""
    list_display = ('id', 'recipe', 'user')
    search_fields = ('user',)
    list_filter = ('user',)
    empty_value_display = os.getenv('VALUE_DISPLAY', '---')

@admin.register(QuantityIngredient)
class IngredientAmountAdmin(admin.ModelAdmin):
    """Отображает количество игредиентов в рецептах в панели администратора."""
    list_display = ('id', 'ingredient', 'recipe', 'amount')
    search_fields = ('recipe',)
