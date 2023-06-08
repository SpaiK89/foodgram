from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
from .filters import IngredientSearchFilter, RecipeFilterSet
from .serializers import (
                        SetPasswordSerializer,
                        CustomUserSerializer,
                        CustomUserCreateSerializer,
                        FollowSerializer,
                        IngredientSerializer,
                        TagSerializer,
                        RecipeSerializer,
                        FavoritesSerializer)
from users.models import Follow, User
from .permissions import IsAuthorOrAdminOrReadOnly, IsAdminOrReadOnly
from recipes.models import (Tag, Ingredient, Recipe, QuantityIngredient,
                            Favorite, Cart)


class UsersViewSet(UserViewSet):
    """Работает с пользователями."""

    def get_serializer_class(self):
        if self.action == 'set_password':
            return SetPasswordSerializer
        if self.action in (
                'list', 'retrieve', 'me', 'subscribe', 'subscriptions'
        ):
            return CustomUserSerializer
        return CustomUserCreateSerializer

    def __get_add_delete_follow(self, request, id):
        """Создаёт/удаляет связь между пользователями."""
        user = get_object_or_404(User, username=request.user)
        author = get_object_or_404(User, id=id)
        if user == author:
            return Response(
                {'errors': 'Нельзя отписываться или подписываться на себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            if Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow = Follow.objects.create(user=user, author=author)
            serializer = FollowSerializer(
                follow, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        get_object_or_404(Follow, user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('POST',), detail=True,
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id=None):
        """Создаёт связь между пользователями."""
        return self.__get_add_delete_follow(request, id)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        """Удаляет связь между пользователями."""
        return self.__get_add_delete_follow(request, id)

    @action(methods=('GET',), detail=False,
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Список подписок пользователя."""
        user = request.user
        if user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['POST'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        user = request.user
        data = request.data
        serializer = self.get_serializer(user, data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(
            {
                'detail': 'Пароль успешно изменен'
            },
            status=status.HTTP_204_NO_CONTENT
        )


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    """Работает с тегами. Теги может создавать только администратор"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """Работает с ингредиентами. Ингредиенты может создавать только админ"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientSearchFilter
    permission_classes = (IsAdminOrReadOnly,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Работает с рецептами."""
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filter_class = RecipeFilterSet
    filterset_class = RecipeFilterSet
    serializer_class = RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def __get_add_delete_recipe(self, model, request, pk):
        """
        Проверяет наличие рецепта в избранных или корзине,
        после - добавляет/удаляет рецепт.
        """
        user = get_object_or_404(User, username=request.user)
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            model.objects.get_or_create(user=user, recipe=recipe)
            serializer = FavoritesSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        get_object_or_404(model, user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('POST', 'DELETE'),
            permission_classes=[IsAuthorOrAdminOrReadOnly])
    def favorite(self, request, pk=None):
        """Добавляет/удаляет рецепт из избранного."""
        return self.__get_add_delete_recipe(Favorite, request, pk)

    @action(detail=True, methods=('POST', 'DELETE'),
            permission_classes=[IsAuthorOrAdminOrReadOnly])
    def shopping_cart(self, request, pk=None):
        """Добавляет/удаляет рецепт из корзины."""
        return self.__get_add_delete_recipe(Cart, request, pk)

    @action(detail=False, methods=('GET',),
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """
        Список покупок скачивается в формате .txt.
        Пользователь получает файл с суммированным перечнем
        и количеством необходимых ингредиентов для всех рецептов.
        """
        carts = get_object_or_404(User, username=request.user).cart.all()
        ingredients_set = {}

        for item in carts:
            ingredients = QuantityIngredient.objects.filter(recipe=item.recipe)

            for ingredient in ingredients:
                amount = ingredient.amount
                name = ingredient.ingredient.name
                measurement_unit = ingredient.ingredient.measurement_unit
                if name not in ingredients_set:
                    ingredients_set[name] = {
                        'amount': amount,
                        'measurement_unit': measurement_unit,
                    }
                else:
                    ingredients_set[name]['amount'] += amount

        cart_list = [' {} - {} {}.\n '.format(
            name, ingredients_set[name]['amount'],
            ingredients_set[name]['measurement_unit'],
        ) for name in ingredients_set]
        cart_list = 'Список покупок:\n\n ' + '\n'.join(cart_list)
        filename = 'shopping_cart.txt'
        request = HttpResponse(cart_list, content_type='text/plain')
        request['Content-Disposition'] = f'attachment; filename={filename}'
        return request
