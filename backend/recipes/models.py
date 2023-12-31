from colorfield.fields import ColorField
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Exists, OuterRef

from users.models import Follow, User  # noqa

MAX_NAME_LENGTH = 100
MAX_COLOR_LENGTH = 7
MAX_SLUG_LENGTH = 100


class Tag(models.Model):
    """Модель тегов для рецептов."""
    name = models.CharField(
        'Название',
        max_length=MAX_NAME_LENGTH,
        unique=True
    )
    color = ColorField(
        'Цвет',
        max_length=MAX_COLOR_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        'Слаг',
        max_length=MAX_SLUG_LENGTH,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингридиентов."""
    name = models.CharField('Название', max_length=MAX_NAME_LENGTH)
    measurement_unit = models.CharField('Еденица измерения', max_length=30)

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ('name',)

    def __str__(self):
        return self.name


class RecipeQuerySet(models.QuerySet):
    def with_user_annotations(self, user):
        return self.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(recipe=OuterRef('pk'), user=user)
            ),
            is_in_shopping_cart=Exists(
                ShopList.objects.filter(recipe=OuterRef('pk'), user=user)
            )
        )


class Recipe(models.Model):
    """Модель рецепта."""
    name = models.CharField('Название', max_length=MAX_NAME_LENGTH)
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[
            MinValueValidator(
                1, message='Минимальное время готовки не менее 1 минуты'
            )
        ]
    )
    image = models.ImageField('Изображение', upload_to='recipes/image/')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag, through='TagToRecipe',
        verbose_name='Теги',
    )

    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientToRecipe',
        verbose_name='Ингридиенты',
        related_name='recipes'
    )

    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    objects = RecipeQuerySet.as_manager()

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', 'name', )

    def __str__(self):
        return self.name


class TagToRecipe(models.Model):
    """Модель для связи тегов и рецептов."""
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, verbose_name='тег',
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='рецепт',
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'recipe'],
                name='unique_tag_recipe'
            )
        ]

    def __str__(self):
        return f'{self.tag} и {self.recipe}'


class FavoriteShoppingCart(models.Model):
    """Модель для связи списка покупок и избранного."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',

    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.user} и {self.recipe}'


class Favorite(FavoriteShoppingCart):
    """Модель добавления в избранное."""

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorites'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_favorite'
            )
        ]

    def __str__(self):
        return (f'Рецепт: {self.recipe} - теперь'
                f' в избранном пользователя: {self.user}')


class ShopList(FavoriteShoppingCart):
    """Модель списка покупок."""

    class Meta:
        default_related_name = 'shopping_list'
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_cart'
            )
        ]

    def __str__(self):
        return (f'Рецепт: {self.recipe} - теперь'
                f' в корзине пользователя: {self.user}')


class IngredientToRecipe(models.Model):
    """Модель связи ингридиентов и рецептов."""
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='Ингридиент',
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт',
        related_name='ingredient_recipe'
    )

    amount = models.PositiveIntegerField(
        validators=[
            MinValueValidator(
                1, message='Минимальное количество ингредиентов 1'
            )
        ],
        verbose_name='Количество продуктов',
        default=1
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredient_recipe'
            )
        ]

    def __str__(self):
        return f'{self.ingredient} и {self.recipe}'
