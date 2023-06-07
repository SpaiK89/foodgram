from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from recipes.models import (Ingredient, QuantityIngredient, Recipe, Tag,
                            Favorite, Cart)
from users.models import User, Follow


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""
    password = serializers.CharField(
        style={
            'input_type': 'password'
        },
        write_only=True,
    )

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password'
        )

    def validate(self, data):
        """Проверяет введенные данные."""
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        if username == 'me':
            raise serializers.ValidationError(
                {'username': 'Нельзя создать пользователя с никнеймом - "me"'}
            )
        if not first_name:
            raise serializers.ValidationError(
                {'first_name': 'Имя - обязательное поле'}
            )
        if not last_name:
            raise serializers.ValidationError(
                {'last_name': 'Фамилия - обязательное поле'}
            )
        return data


class CustomUserSerializer(UserSerializer):
    """Сериализатор пользователя."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, author):
        """Проверяет, подписан ли текущий пользователь на автора."""
        user = self.context.get('request').user
        return not user.is_anonymous and Follow.objects.filter(
            user=user, author=author).exists()


class SetPasswordSerializer(serializers.Serializer):
    """Устанавливает/меняет пароль пользователя."""
    current_password = serializers.CharField(
        error_messages={'required': 'Обязательное поле.'}
    )
    new_password = serializers.CharField(
        error_messages={'required': 'Обязательное поле.'}
    )

    def validate(self, data):
        new_password = data.get('new_password')
        try:
            validate_password(new_password)
        except exceptions.ValidationError as err:
            raise serializers.ValidationError(
                {'new_password': err.messages}
            )
        return super().validate(data)

    def update(self, instance, validated_data):
        current_password = validated_data.get('current_password')
        new_password = validated_data.get('new_password')
        if not instance.check_password(current_password):
            raise serializers.ValidationError(
                {
                    'current_password': 'Неверный пароль'
                }
            )
        if current_password == new_password:
            raise serializers.ValidationError(
                {
                    'new_password': 'Новый пароль должен отличаться от '
                                    'текущего пароля'
                }
            )
        instance.set_password(new_password)
        instance.save()
        return validated_data


class FollowRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода авторов, на которых подписан пользователь."""
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ('id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, author):
        """Проверяет подписан ли текущий пользователь на автора."""
        user = self.context.get('request').user
        return not user.is_anonymous and Follow.objects.filter(
            user=user, author=author.author).exists()

    def get_recipes(self, author):
        """Отображает рецепты в "Мои подписки"."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        limit = request.query_params.get('recipes_limit')
        recipes = Recipe.objects.filter(author=author.author)
        if limit:
            recipes = recipes.all()[:int(limit)]
        return FollowRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, author):
        """Показывает количество рецептов у автора."""
        return Recipe.objects.filter(author=author.author).count()

    def validate(self, data):
        user = data.get('user')
        author = data.get('author')
        if user == author:
            raise serializers.ValidationError(
                {
                    'error': 'Нельзя подписаться на себя'
                }
            )
        return data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class QuantityIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор количества ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = QuantityIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = QuantityIngredientSerializer(
        many=True,
        read_only=True,
        source='quantity_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def check_recipe(self, recipe, model):
        """Проверяет налчие рецепта."""
        user = self.context.get('request').user
        return not user.is_anonymous and model.objects.filter(
            user=user, recipe=recipe).exists()

    def get_is_favorited(self, recipe):
        """Проверяет, добавлен ли пользователем рецепт в избранное."""
        return self.check_recipe(recipe, Favorite)

    def get_is_in_shopping_cart(self, recipe):
        """Проверяет добавлен ли пользователем рецепт в корзину."""
        return self.check_recipe(recipe, Cart)

    def validate(self, data):
        """Проверяет входные данные при создании/редактировании рецепта."""
        if data['cooking_time'] < 1:
            raise ValidationError('Минимальное время приготовления - 1 минута')

        name = self.initial_data.get('name')
        if not name:
            raise ValidationError('Нет названия рецепта.')
        if self.context.get('request').method == 'POST':
            user = self.context.get('request').user
            if Recipe.objects.filter(author=user, name=name).exists():
                raise ValidationError(f'Рецепт "{name}" уже существует.')

        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise ValidationError('В рецепте нет ингредиентов.')
        ingredients_set = set()
        for ingredient in ingredients:
            ingredient = get_object_or_404(Ingredient, id=ingredient['id'])
            if ingredient in ingredients_set:
                raise ValidationError('Ингридиенты повторяются')
            ingredients_set.add(ingredient)
        data['ingredients'] = ingredients
        return data

    def create_ingredients(self, ingredients, recipe):
        """Записывает количество ингредиентов в рецепте."""
        for ingredient in ingredients:
            QuantityIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount')
            )

    def create(self, validated_data):
        """Создаёт рецепт."""
        image = validated_data.pop('image')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(image=image, **validated_data)
        recipe.tags.set(self.initial_data.get('tags'))
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Редактирует рецепт."""
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        ingredients = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.ingredients.clear()
        instance.tags.set(self.initial_data.get('tags'))
        self.create_ingredients(ingredients, instance)
        instance.save()
        return instance


class FavoritesSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта в подписках."""
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
