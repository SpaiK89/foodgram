from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator
from recipes.models import (Ingredient, IngredientAmount, Recipe, Tag,
                            Favorite, ShoppingCart)
from users.models import User, Follow


class UserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания нового пользователя."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password'
        )

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, data):
        """Проверяет введенные данные."""
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        forbidden_usernames = ['me', 'Me', 'ME', 'set_password',
                             'subscriptions', 'subscribe']
        if self.initial_data.get('username') in forbidden_usernames:
            raise serializers.ValidationError(
                {'username': f'Вы не можете использовать {username}'
                 'в качестве "username".'}
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


class UserReadSerializer(UserSerializer):
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
        return user.is_authenticated and Follow.objects.filter(
            user=user, author=author).exists()


class SetPasswordSerializer(serializers.Serializer):
    """Меняет пароль пользователя."""
    current_password = serializers.CharField(
        error_messages={'required': 'Обязательное поле.'}
    )
    new_password = serializers.CharField(
        error_messages={'required': 'Обязательное поле.'}
    )

    def validate_password(self, value):
        validate_password(value)
        return value

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


class FollowUserSerializer(UserReadSerializer):
    """
    Сериализатор для работы с подписками текущего пользователя
    (подписка/отписка).
    """
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeShortSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(source='recipes.count',
                                             read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count')

    def validate(self, obj):
        if (self.context.get('request') == obj):
            raise serializers.ValidationError({'errors': 'Ошибка подписки.'})
        return obj

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated
                and Follow.objects.filter(user=user, author=obj).exists())


class FollowSerializer(serializers.ModelSerializer):
    """
    Сериализатор для вывода списка авторов, на которых подписан пользователь.
    """
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count',
                                             read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated
                and Follow.objects.filter(user=user, author=obj).exists())


    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = '__all__',


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тэгов."""

    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = '__all__',


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор количества ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')

class RecipeShortSerializer(RecipeSerializer):
    """Сериализатор для рецептов с укороченным набором полей."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""
    tags = TagSerializer(read_only=True, many=True)
    author = UserReadSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(
        many=True,
        source='ingredients_amount'
    )
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )


class RecipeCreateSerializer(RecipeSerializer):
    """Сериализатор для создания/обновления/удаления рецептов."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    @staticmethod
    def save_ingredients(recipe, ingredients):
        ingredients_list = []
        for ingredient in ingredients:
            current_ingredient = ingredient['ingredient']['id']
            current_amount = ingredient.get('amount')
            ingredients_list.append(
                IngredientAmount(
                    recipe=recipe,
                    ingredient=current_ingredient,
                    amount=current_amount
                )
            )
        IngredientAmount.objects.bulk_create(ingredients_list)

    def validate(self, data):
        for field in ['name', 'text', 'cooking_time']:
            if not data.get(field):
                raise serializers.ValidationError(
                    f'{field} - Обязательное поле.'
                )
        if not data.get('tags'):
            raise serializers.ValidationError(
                'Нужно указать минимум 1 тэг.'
            )
        if not data.get('ingredients'):
            raise serializers.ValidationError(
                'Нужно указать минимум 1 ингредиент.'
            )
        inrgedient_id_list = [item['id'] for item in data.get('ingredients')]
        unique_ingredient_id_list = set(inrgedient_id_list)
        if len(inrgedient_id_list) != len(unique_ingredient_id_list):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        return data


    def create(self, validated_data):
        author = self.context.get('request').user
        ingredients = validated_data.pop('ingredients_amount')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data, author=author)
        recipe.tags.add(*tags)
        self.save_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        ingredients = validated_data.pop('ingredients_amount')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.ingredients.clear()
        instance.tags.add(*tags)
        self.save_ingredients(instance, ingredients)
        instance.save()
        return instance


class FavoriteSerializer(RecipeShortSerializer):
    """Сериализатор для работы со списком избранного."""
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже был добавлен в избранное'
            )
        ]


class ShoppingCartSerializer(RecipeShortSerializer):
    """Сериализатор для работы со списком покупок."""
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        write_only=True,
    )

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже был добавлен в список покупок'
            )
        ]

