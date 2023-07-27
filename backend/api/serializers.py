import djoser.serializers
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from recipes.models import (Favorite, Ingredient, IngredientToRecipe,
                            Recipe, ShopList, Tag, Follow)
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'id',
                  'first_name', 'last_name', 'is_subscribed',)

    def get_is_subscribed(self, obj):
        """Проверка подписки."""
        request = self.context.get('request')
        return request.user.is_authenticated and obj.following.filter(
            user=request.user).exists()


class UserCreateSerializer(djoser.serializers.UserCreateSerializer):
    """Сериализатор создания пользователя."""

    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name',
            'last_name', 'password', 'id')


class SubscribeListSerializer(djoser.serializers.UserSerializer):
    """Сериализатор подписок."""
    recipe_count = SerializerMethodField()
    recipe = SerializerMethodField()
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = '__all__'
        read_only_fields = ('email', 'username',
                            'first_name', 'last_name')
        read_only_fields = ('email', 'username')

    def get_recipe_count(self, obj):
        """Возвращает количество рецептов автора"""
        return obj.recipe.count()

    def get_recipes(self, obj):
        """Возвращает список рецептов"""
        recipes = obj.recipe.all()
        request = self.context['request']
        limit = request.GET.get('recipes_limit')

        if limit:
            recipes = recipes[:int(limit)]

        return RecipeShortSerializer(recipes, many=True).data

    def get_is_subscribed(self, obj):
        """Проверка подписки пользователей"""
        request = self.context.get('request')
        return request.user.is_authenticated and obj.following.filter(
            username=request.user).exists()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор модели Тэг."""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор модели Ингредиент."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов и их количества"""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientToRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class IngredientRecipeForCreateSerializer(serializers.ModelSerializer):
    """Сериализатор связи ингридиентов и рецепта для создания."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientToRecipe
        fields = ('id', 'amount',)


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра рецепта."""
    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = IngredientRecipeSerializer(
        many=True,
        source='ingredient_recipe'
    )
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    image = Base64ImageField(max_length=None)

    class Meta:
        model = Recipe
        fields = '__all__'


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта. """
    ingredients = IngredientRecipeForCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField(max_length=None)
    author = UserSerializer(read_only=True)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def validate(self, data):
        if Recipe.objects.filter(text=data['text']).exists():
            raise serializers.ValidationError(
                'Рецепт уже существует')
        return data

    def validate_cooking_time(self, cooking_time):
        if not 1 <= cooking_time <= 2880:
            raise serializers.ValidationError(
                'Время готовки должно быть от 1 минуты до 2 суток'
            )
        return cooking_time

    def validate_recipe_tags(self, tags):
        if len(set(tags)) != len(tags):
            raise serializers.ValidationError('Теги не должны повторяться')
        if not tags:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один тег'
            )
        return tags

    def validate_ingredients(self, data):
        if not data:
            raise serializers.ValidationError(
                'Эй, друг, ингредиенты забыл добавить!'
            )
        ingredients = set()
        for ingredient in data:
            ingredient_id = ingredient['id']
            if ingredient_id in ingredients:
                raise (
                    serializers.ValidationError(
                        'Ингредиенты не могут повторяться'
                    )
                )
            ingredients.add(ingredient_id)

        amount = int(ingredient.get('amount'))
        if amount < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше 0, '
                f'получено: {amount}'
            )
        return data

    @staticmethod
    def create_ingredients(recipe, ingredients):
        ingredient_list = [
            IngredientToRecipe(
                ingredient=ingredient['id'],
                amount=ingredient['amount'],
                recipe=recipe
            )
            for ingredient in ingredients
        ]
        IngredientToRecipe.objects.bulk_create(ingredient_list)

    def create(self, validated_data):
        request = self.context.get('request')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)

        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        IngredientToRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients(instance, ingredients)
        instance.tags.set(tags)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        recipe = Recipe.objects.with_user_annotations(
            request.user
        ).get(id=instance.id)
        return RecipeReadSerializer(recipe, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для избранных рецептов и покупок."""

    class Meta:
        fields = (
            'name', 'text',
            'cooking_time', 'image',
        )
        model = Recipe


class ShopListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""
    recipe = RecipeShortSerializer(read_only=True, source='recipe')
    user = UserSerializer(read_only=True)

    class Meta:
        model = ShopList
        fields = ('recipe', 'user')

    def validate(self, data):
        recipe = data['recipe']
        user = data['user']

        if user.shopping_list.filter(recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже добавлен в корзину')

        return data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранных рецептов."""

    recipe = RecipeShortSerializer(read_only=True, source='recipe')
    user = UserSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ('recipe', 'user')

    def validate(self, data):
        recipe = data['recipe']
        user = data['user']

        if user.favorites.filter(recipe=recipe).exists():
            raise (
                serializers.ValidationError(
                    'Рецепт уже добавлен в избранное.'
                )
            )

        return data


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Follow (подписки)"""

    class Meta:
        model = Follow
        fields = '__all__'
        read_only_fields = ('user', 'author',)

    def validate(self, data):
        user = data['user']
        author = data['author']

        if user == author:
            raise serializers.ValidationError(
                'Ой, на себя подписываться нельзя!'
            )

        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого автора.'
            )

        return data
