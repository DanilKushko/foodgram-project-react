from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import (Favorite, Ingredient, Recipe,
                            ShopList, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import Follow, User

from .filter import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (CreateRecipeSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeReadSerializer,
                          ShopListSerializer, SubscribeListSerializer,
                          TagSerializer, UserSerializer)


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    permission_classes = (IsAuthenticated,)

    @action(detail=True, methods=['POST', 'DELETE'])
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, pk=id)

        if request.method == 'POST':
            serializer = SubscribeListSerializer(author, data=request.data)
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=user, following=author)
            return Response(status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(Follow, user=user, following=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'])
    def get_self_page(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False)
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        serializer = SubscribeListSerializer(queryset, many=True)
        return Response(serializer.data)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        else:
            return CreateRecipeSerializer

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):
        ingredients = Ingredient.objects.filter(
            ingredienttorecipe__recipe__shopping_list__user=request.user
        ).values(
            'name', 'measurement_unit'
        ).annotate(total_amount=Sum('ingredienttorecipe__amount'))

        shopping_list = ['Список покупок:\n']
        for ingredient in ingredients:
            # The field names in the annotation are incorrect
            name = ingredient['name']
            unit = ingredient['measurement_unit']
            amount = ingredient['total_amount']
            shopping_list.append(f'{name} - {amount}, {unit}')

        response = Response(
            '\n'.join(shopping_list),
            content_type='text/plain'
        )
        response[
            'Content-Disposition'
            ] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(detail=True, methods=['POST', 'DELETE'])
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            data = {'user': request.user.id, 'recipe': recipe.id}
            serializer = ShopListSerializer(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(
                ShopList, user=request.user, recipe=recipe
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST', 'DELETE'])
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            data = {'user': request.user.id, 'recipe': recipe.id}
            serializer = FavoriteSerializer(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            favorite = get_object_or_404(
                Favorite, user=request.user, recipe=recipe
            )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
