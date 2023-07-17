from django.conf import settings
from django.contrib import admin

from .models import (Favorite, Ingredient, IngredientToRecipe, Recipe,
                     ShopList, Tag)


class IngredientInline(admin.TabularInline):
    model = IngredientToRecipe
    extra = 5
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time', 'favorites_amount',)
    search_fields = ('name', 'author')
    list_filter = ('name', 'author', 'tags')
    inlines = (IngredientInline,)
    empty_value_display = settings.EMPTY_VALUE

    def favorites_amount(self, obj):
        return obj.favorites.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user', 'recipe')
    empty_value_display = settings.EMPTY_VALUE


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = settings.EMPTY_VALUE


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name',)
    empty_value_display = settings.EMPTY_VALUE


@admin.register(ShopList)
class ShopListAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user')
    list_filter = ('recipe', 'user')
    search_fields = ('user',)
    empty_value_display = settings.EMPTY_VALUE
