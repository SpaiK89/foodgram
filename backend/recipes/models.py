from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models.functions import Length
from users.models import User

models.CharField.register_lookup(Length)


class Ingredient(models.Model):
    """Модель игредиентов."""
    name = models.CharField(
        blank=False,
        max_length=150,
        db_index=True,
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=150,
        verbose_name='Единицы измерения',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient'
            ),
            models.CheckConstraint(
                check=models.Q(name__length__gt=0),
                name='\n%(app_label)s_%(class)s_name - пустое значение\n',
            ),
            models.CheckConstraint(
                check=models.Q(measurement_unit__length__gt=0),
                name='\n%(app_label)s_%(class)s_measurement_unit - пустое'
                     'значение\n',
            ),
        )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    """Модель тэгов."""
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text='Введите название тэга',
    )
    color = models.CharField(
        max_length=7,
        unique=True,
        verbose_name='Цвет в HEX-формате',
        help_text='Цветовой HEX-код например, #49B64E',
        validators=[
            RegexValidator(
                '^#([a-fA-F0-9]{6})',
                message='Поле должно содержать цвет в HEX-формате.'
            )
        ]

    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        db_index=True,
        help_text='Уникальный слаг тэга'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class QuerySet(models.QuerySet):
    """
    Добполнительная модель для работы со списком рецептов с
    добавлением избранного и списка покупок.
    """

    def add_annotations(self, user_id):
        return self.annotate(
            is_favorited=models.Exists(
                Favorite.objects.filter(
                    recipe__pk=models.OuterRef('pk'),
                    user_id=user_id,
                )
            ),
            is_in_shopping_cart=models.Exists(
                ShoppingCart.objects.filter(
                    recipe__pk=models.OuterRef('pk'),
                    user_id=user_id,
                )
            ),
        )


class Recipe(models.Model):
    """Модель рецептов."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=200,
        db_index=True,
        verbose_name='Название рецепта',
        help_text='Название рецепта'
    )
    image = models.ImageField(
        blank=True,
        upload_to='recipes/images/',
        help_text='Фото блюда',
        verbose_name='Фото'
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientAmount',
        related_name='recipes',
        verbose_name='Список ингредиентов',
        help_text='Выберите ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тег',
        help_text='Выберите тэг'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        help_text='Время приготовления в минутах',
        validators=[MinValueValidator(
            1, 'Минимальное время приготовления - 1 минута')],
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    objects = QuerySet.as_manager()

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'author'),
                name='unique_for_author',
            ),
            models.CheckConstraint(
                check=models.Q(name__length__gt=0),
                name='\n%(app_label)s_%(class)s_name - пустое значение\n',
            ),
        )

    def __str__(self):
        return f'{self.name} от {self.author.username}'


class IngredientAmount(models.Model):
    """Модель, определяющая количество ингредиентов в рецепте."""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients_amount',
        verbose_name='Ингридиент',
        help_text='Выберите ингредиенты'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients_amount',
        verbose_name='Рецепт'
    )
    amount = models.IntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(
            1, 'Минимальное количество ингредиентов - 1 ед.')],
        default=1,
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты рецепта'
        constraints = (
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique_ingredients_recipe'
            ),
        )

    def __str__(self):
        return f'{self.ingredient}: {self.amount}'


class Favorite(models.Model):
    """Модель для хранения избранных рецептов."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Рецепт',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Пользователь',
    )

    date_added = models.DateTimeField(
        verbose_name='Дата добавления в избранное',
        auto_now_add=True,
        editable=False
    )

    class Meta:
        ordering = ('user',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_for_favorite'
            ),
        )


class ShoppingCart(models.Model):
    """Модель хранения списка покупок (Продуктовая корзина)."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )

    date_added = models.DateTimeField(
        verbose_name='Дата добавления в список покупок',
        auto_now_add=True,
        editable=False
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Корзина'
        verbose_name_plural = 'В корзине'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart'
            ),
        )
