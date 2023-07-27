from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import Ingredient, Recipe, Tag
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


from users.models import Follow, User
from .filter import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (CreateRecipeSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeReadSerializer,
                          ShopListSerializer, SubscribeListSerializer,
                          TagSerializer, UserSerializer, FollowSerializer)
from .pagination import PageLimitPagination


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageLimitPagination
    permission_classes = (AllowAny,)

    @action(detail=True, methods=['POST', 'DELETE'])
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, pk=id)

        if request.method == 'POST':
            serializer = FollowSerializer(author)
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=user, author=author)
            return Response(status=status.HTTP_201_CREATED)
        Follow.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        queryset = request.user.following.all()
        paginator = self.pagination_class()
        subscriptions_page = paginator.paginate_queryset(queryset, request)
        serializer = SubscribeListSerializer(subscriptions_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny, )
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PageLimitPagination

    def get_queryset(self):
        queryset = Recipe.objects.with_user_annotations(self.request.user)
        queryset = queryset.order_by('-created_at')
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return CreateRecipeSerializer

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):
        ingredients = Ingredient.objects.filter(
            ingredienttorecipe__recipe__shopping_list__user=request.user
        ).values(
            'name', 'measurement_unit'
        ).annotate(total_amount=Sum('ingredienttorecipe__amount'))

        return self.generate_shopping_cart_response(ingredients)

    def generate_shopping_cart_response(self, ingredients):
        shopping_list = ['Список покупок:\n']
        for ingredient in ingredients:
            name = ingredient['name']
            unit = ingredient['measurement_unit']
            amount = ingredient['total_amount']
            shopping_list.append(f'{name} - {amount}, {unit}')

        response = Response(
            '\n'.join(shopping_list),
            content_type='text/plain'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(detail=True, methods=['POST', 'DELETE'])
    def shopping_cart(self, request, pk):
        recipe = self.get_object()

        if request.method == 'POST':
            self.handle_favorite_or_cart(request, recipe, ShopListSerializer)
            return Response(status=status.HTTP_201_CREATED)
        self.handle_favorite_or_cart(
            request, recipe, ShopListSerializer, remove=True
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST', 'DELETE'])
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            self.handle_favorite_or_cart(request, recipe, FavoriteSerializer)
            return Response(status=status.HTTP_201_CREATED)
        favorite_recipe = self.get_object()
        favorite_recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def handle_favorite_or_cart(self, request, recipe, serializer_class):
        data = {'user': request.user.id, 'recipe': recipe.id}
        serializer = serializer_class(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
