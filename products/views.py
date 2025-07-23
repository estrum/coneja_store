from rest_framework import viewsets, status
from rest_framework.permissions import (IsAuthenticated, 
                                        IsAuthenticatedOrReadOnly,
                                        AllowAny)
from rest_framework.views import APIView
from rest_framework.response import Response

from django.db.models import Q

from .models import Product, Category, Tag, Size
from .serializers import ProductSerializer, CategorySerializer, TagSerializer, SizeSerializer
from users.permissions import IsAdminOrSuperUser 

class PublicReadOnly(viewsets.ModelViewSet):
    """
    Base ViewSet con lectura pública.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in ['destroy']:
            return [IsAdminOrSuperUser()]
        elif self.action in ['create', 'update', 'partial_update']:
            return [IsAuthenticated()]
        return [AllowAny()]


#product list view
class ProductListView(APIView):
    def get(self, request):
        queryset = Product.objects.filter(is_active=True)

        # Filtros
        search = request.query_params.get('search')
        category = request.query_params.get('category')
        tags = request.query_params.getlist('tags')  # ?tags=1&tags=2
        sizes = request.query_params.getlist('sizes')

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        if category:
            queryset = queryset.filter(category_id=category)
        if tags:
            queryset = queryset.filter(tags__id__in=tags).distinct()
        if sizes:
            queryset = queryset.filter(sizes__id__in=sizes).distinct()

        # Paginación
        is_admin = request.query_params.get('admin') == 'true'
        page_size = 50 if is_admin else 15
        total = queryset.count()
        max_page = max(1, (total + page_size - 1) // page_size)

        try:
            page = int(request.query_params.get('page', 1))
        except (TypeError, ValueError):
            page = 1

        page = max(1, min(page, max_page))

        if page < 1:
            page = 1
        elif page > max_page:
            page = max_page

        start = (page - 1) * page_size
        end = start + page_size
        
        # Ordenamiento
        order_by = request.query_params.get('order_by')
        allowed_order_fields = ['price', '-price', 'name', '-name', 'updated_at', '-updated_at']
        
        if order_by in allowed_order_fields:
            queryset = queryset.order_by(order_by)

        serializer = ProductSerializer(queryset[start:end], many=True)

        return Response({
            'page': page,
            'maxPage': max_page,
            'totalItems': total,
            'productList': serializer.data
        }, status=status.HTTP_200_OK)


# Product ViewSet - Metodos GetById, Create, Update y Delete
class ProductViewSet(PublicReadOnly):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    serializer_class = ProductSerializer

    def retrieve(self, request, pk=None):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({'detail': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def update(self, request, pk=None, partial=False):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({'detail': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProductSerializer(product, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Producto actualizado'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({'detail': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        product.delete()
        return Response({'detail': 'Producto eliminado'}, status=status.HTTP_204_NO_CONTENT)


# Category ViewSet
class CategoryViewSet(PublicReadOnly):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# Tag ViewSet
class TagViewSet(PublicReadOnly):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


# Size ViewSet
class SizeViewSet(PublicReadOnly):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer
