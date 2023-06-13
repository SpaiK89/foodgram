from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F, Sum
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status, viewsets, mixins
from .filters import IngredientFilter, RecipeFilterSet
from .serializers import (
                        SetPasswordSerializer,
                        UserReadSerializer,
                        UserCreateSerializer,
                        FollowUserSerializer,
                        FollowSerializer,
                        IngredientSerializer,
                        TagSerializer,
                        RecipeSerializer,
                        RecipeShortSerializer,
                        RecipeCreateSerializer,
                        FavoriteSerializer,
                        ShoppingCartSerializer
)
from users.models import Follow, User
from .permissions import AuthorOrAdminOrReadOnly, AdminOrReadOnly
from recipes.models import (Tag, Ingredient, Recipe, IngredientAmount,
                            Favorite, ShoppingCart)


class UsersViewSet(mixins.CreateModelMixin,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   viewsets.GenericViewSet,):
    """
    Работает с пользователями.
    _____
    Для всех - вывод списка пользователей, создание нового пользователя,
    изменение текущего пароля.
    Для авторизованных пользователей - вывод конкретного пользователя по id,
    вывод информации о себе, подписка на автора рецепта.
    """

    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'me'):
            return UserReadSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return UserCreateSerializer

    def get_permissions(self):
        if self.action == 'retrieve':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

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

    @action(detail=False, methods=['GET'],
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Список подписок пользователя."""
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = FollowSerializer(page, many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, pk):
        """Подписка/отписка текущего пользователя на/от автора."""
        author = get_object_or_404(User, id=pk)

        if request.method == 'POST':
            serializer = FollowUserSerializer(
                author, data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=request.user, author=author)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(Follow, user=request.user,
                              author=author).delete()
            return Response({'detail': 'Успешная отписка'},
                            status=status.HTTP_204_NO_CONTENT)


class TagsViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    """Работает с тэгами. Теги может создавать только администратор"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminOrReadOnly,)
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Работает с ингредиентами. Ингредиенты может создавать только администратор
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    permission_classes = (AdminOrReadOnly,)
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Работает с рецептами."""
    queryset = Recipe.objects.all()
    permission_classes = (AuthorOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = RecipeFilterSet
    filterset_class = RecipeFilterSet
    serializer_class = RecipeSerializer

    def get_serializer_class(self):
        if self.action in ('favorite', 'shopping_cart'):
            return RecipeShortSerializer
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def get_queryset(self):
        user_id = self.request.user.pk
        return Recipe.objects.add_annotations(user_id).select_related(
            'author').prefetch_related('ingredients', 'tags')

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=(AuthorOrAdminOrReadOnly,)
    )
    def favorite(self, request, pk):
        """Добавляет рецепт в `избранное`."""
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {
            'user': request.user.pk,
            'recipe': recipe.pk
        }
        serializer = FavoriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = self.get_serializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        """Удаляет рецепт из `избранное`."""
        recipe = get_object_or_404(Recipe, pk=pk)
        Favorite.objects.filter(user=request.user, recipe=recipe).delete()
        message = {
            'detail': 'Вы успешно отписались от автора'
        }
        return Response(message, status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=(AuthorOrAdminOrReadOnly,)
    )
    def shopping_cart(self, request, pk):
        """Добавляет рецепт в `мои покупки`."""
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {
            'user': request.user.pk,
            'recipe': recipe.pk
        }
        serializer = ShoppingCartSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = self.get_serializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        """Удаляет рецепт из `мои покупки`."""
        recipe = get_object_or_404(Recipe, pk=pk)
        ShoppingCart.objects.filter(user=request.user, recipe=recipe).delete()
        message = {
            'detail':
                'You have successfully removed recipe from shopping cart'
        }
        return Response(message, status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Загружает файл *.txt со списком покупок. Считает сумму ингредиентов
         в рецептах выбранных для покупки. Возвращает текстовый файл со списком
         ингредиентов."""
        ingredients = IngredientAmount.objects.filter(
            recipe__shopping_cart__user=request.user).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')).annotate(
            amount=Sum('amount')
        )
        data = []
        for ingredient in ingredients:
            data.append(
                f'{ingredient["name"]} - '
                f'{ingredient["amount"]} '
                f'{ingredient["measurement_unit"]}'
            )
        content = 'Список покупок:\n\n' + '\n'.join(data)
        filename = 'shopping_cart.txt'
        request = HttpResponse(content, content_type='text/plain')
        request['Content-Disposition'] = f'attachment; filename={filename}'
        return request



