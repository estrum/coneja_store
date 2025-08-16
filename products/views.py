from rest_framework import viewsets, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny

from django.db.models import Q

from .models import Product, Category, Tag, Size
from .serializers import (
    ProductSerializerGetAll, 
    ProductSerializerDetail,
    ProductSerializer,
    CategorySerializer, 
    TagSerializer, 
    SizeSerializer
)
from conf.permissions import IsOwnerByGUIDOrAdminForProductsApp

#TODO: usar throtling o cache para evitar la sobrecarga y ataques DDOS
class PublicReadOnly(viewsets.ModelViewSet):
    """
    exclusivo para los metodos crud relacionado a products
    y el inventory

    SIZE, TAGS y CATEGORIES : IsAdminUser
    
    PRODUCT y PRODUCTINVENTORY:
        ->(CREATE) PRODUCT - PRODUCTINVENTORY:
            SOLO EL DUEÑO O EL STAFF PUEDEN CREAR.
        ->(GETALL, GETBYID, GETBYSTORENAME) PRODUCT:
            CUALQUIERA PUEDE VER LA INFORMACIÓN.
        ->(GETBYID) PRODUCT CON ARTICLES:
            CUALQUIERA PUEDE VER LA INFORMACIÓN.
        ->(UPDATE, PATCH) PRODUCT Y ARTICLES:
            SOLO EL DUEÑO O EL STAFF PUEDEN MODIFICAR.
        ->(DELETE) PRODUCT:
            SOLO EL DUEÑO O EL STADD PUEDEN BORRAR.
            SI SE BORRA UN PRODUCTO TAMBIÉN SUS ARTICULOS
    """

    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action in [
            'create', 'update', 'partial_update','destroy']:
            return [IsOwnerByGUIDOrAdminForProductsApp()]
        return [permission() for permission in self.permission_classes]


class ProductSearchPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 50


class ProductSearchView(generics.ListAPIView):
    """
    Endpoint público para buscar productos por nombre, descripción o tags.
    Ejemplo de uso:
    GET /products/search/?q=camiseta&page=1
    """
    serializer_class = ProductSerializerGetAll
    pagination_class = ProductSearchPagination

    def get_queryset(self):
        queryset = Product.objects.filter(
            is_active=True).select_related(
                "category").prefetch_related("tags")
        
        q = self.request.query_params.get('q', None)

        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q) |
                Q(tags__name__icontains=q) |
                Q(category__name__icontains=q)
            ).distinct()

        return queryset.order_by('-updated_at')
    

class ProductByStoreView(generics.ListAPIView):
    """
    Endpoint público para buscar productos por el nombre de la tienda.
    ademas de filtrado por nombre, descripción o tags.
    Ejemplo de uso:
    GET /products/<coneja_store>/?q=camiseta&page=1
    """
    serializer_class = ProductSerializerGetAll
    pagination_class = ProductSearchPagination

    def get_queryset(self):
        store = self.kwargs.get('store')

        queryset = Product.objects.filter(
            is_active=True,
            posted_by__slug=store).select_related(
                "category").prefetch_related("tags")
        
        q = self.request.query_params.get('q', None)

        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q) |
                Q(tags__name__icontains=q) |
                Q(category__name__icontains=q)
            ).distinct()

        return queryset.order_by('-updated_at')


class ProductDetailView(generics.RetrieveAPIView):
    """
    Devuelve el detalle de un producto por su ID.
    Ejemplo: GET /product/15/
    """
    queryset = Product.objects.select_related(
        "category", "posted_by"
    ).prefetch_related("tags")
    serializer_class = ProductSerializerDetail
    lookup_field = "id"


class ProductViewSet(PublicReadOnly):
    """
    Para los metodos CREATE - PATCH Y DELETE de products
    """
    queryset = Product.objects.all().prefetch_related(
        'inventory', 'tags', 'category'
    )
    serializer_class = ProductSerializer


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
