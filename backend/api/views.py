from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import (Ingredient, Recipe,
                            Tag, ShopList, Favorite)
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
                          TagSerializer, UserSerializer, FollowSerializer,
                          RecipeShortSerializer)
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
            data = {'user': user.id, 'author': author.id}
            serializer = FollowSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            subscribe_serializer = SubscribeListSerializer(
                author,
                context={'request': request}
            )
            return Response(
                subscribe_serializer.data,
                status=status.HTTP_201_CREATED
            )

        get_object_or_404(Follow, user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(following__user=user)
        subscriptions_page = self.paginate_queryset(queryset)
        serializer = SubscribeListSerializer(subscriptions_page,
                                             many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny, )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PageLimitPagination

#    def get_queryset(self):
#        queryset = Recipe.objects.with_user_annotations(
#            self.request.user
#        ).order_by('name')
#        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return CreateRecipeSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            queryset = Recipe.objects.with_user_annotations(
                self.request.user
            ).order_by('name')
        else:
            queryset = Recipe.objects.all().order_by('name')
        return queryset

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):
        ingredients = Ingredient.objects.filter(
            ingredienttorecipe__recipe__shopping_list__user=request.user
        ).values(
            'name', 'measurement_unit'
        ).annotate(
            total_amount=Sum(
                'ingredienttorecipe__amount'
            )).order_by('name')

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

    @action(detail=True, methods=['POST'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        recipe = self.get_object()
        self.handle_favorite_or_cart(request, recipe, ShopListSerializer)
        serializer = RecipeShortSerializer(
            recipe, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def destroy_shopping_cart(self, request, pk):
        get_object_or_404(
            ShopList,
            user=request.user.pk,
            recipe=get_object_or_404(Recipe, id=pk)
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        self.handle_favorite_or_cart(request, recipe, FavoriteSerializer)
        serializer = RecipeShortSerializer(
            recipe, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def handle_favorite_or_cart(self, request, recipe, serializer_class):
        data = {'user': request.user.id, 'recipe': recipe.id}
        serializer = serializer_class(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

    @favorite.mapping.delete
    def destroy_favorite(self, request, pk):
        get_object_or_404(
            Favorite,
            user=request.user,
            recipe=get_object_or_404(Recipe, id=pk)
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
