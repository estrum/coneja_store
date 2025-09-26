from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle

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

from conf.permissions import IsOwnerByGUIDOrAdminForRestApp
from logs.utils import create_log


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
            return [IsOwnerByGUIDOrAdminForRestApp()]
        return [permission() for permission in self.permission_classes]
    

class ProductThrottle(AnonRateThrottle):
    """limita las solicitudes a 200 por hora"""

    rate = '200/hour'


class ProductSearchPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 50

    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view=view)
        except Exception:
            
            request.query_params._mutable = True
            request.query_params['page'] = 1
            return super().paginate_queryset(queryset, request, view=view)

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "num_pages": self.page.paginator.num_pages,
            "current": self.page.number,
            "results": data
        })


@method_decorator(cache_page(60 * 5), name="dispatch")
class ProductSearchView(generics.ListAPIView):
    """
    Endpoint público para buscar productos por nombre, descripción o tags.
    Ejemplo de uso:
    GET /products/search/?q=camiseta&page=1
    """
    throttle_classes = [ProductThrottle]
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
    

@method_decorator(cache_page(60 * 5), name="dispatch")
class ProductByStoreView(generics.ListAPIView):
    """
    Endpoint público para buscar productos por el nombre de la tienda.
    ademas de filtrado por nombre, descripción o tags.
    Ejemplo de uso:
    GET /products/<coneja_store>/?q=camiseta&page=1
    """
    throttle_classes = [ProductThrottle]
    serializer_class = ProductSerializerGetAll
    pagination_class = ProductSearchPagination

    def get_queryset(self):
        store = self.kwargs.get('store')

        queryset = Product.objects.filter(
            is_active=True,
            store_name__slug=store).select_related(
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


@method_decorator(cache_page(60 * 5), name="dispatch")
class ProductDetailView(generics.RetrieveAPIView):
    """
    Devuelve el detalle de un producto por su ID.
    Ejemplo: GET /product/15/
    """
    throttle_classes = [ProductThrottle]
    queryset = Product.objects.select_related(
        "category", "store_name"
    ).prefetch_related("tags")
    serializer_class = ProductSerializerDetail
    lookup_field = "id"

    def retrieve(self, request, *args, **kwargs):
        try:
            pk = int(kwargs.get(self.lookup_field))
            
            instance = Product.objects.filter().get(pk=pk)
            print(instance)
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except (ValueError, Product.DoesNotExist):
            return Response(
                {"detail": "El ID del producto debe ser un número entero."},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProductViewSet(PublicReadOnly):
    """
    Para los metodos CREATE - PATCH Y DELETE de products
    """
    queryset = Product.objects.all().prefetch_related(
        'inventory', 'tags', 'category'
    )
    serializer_class = ProductSerializer

    def perform_log(self, action, message, instance=None):
        """Crea un log asociado al usuario y producto"""
        create_log(
            user=(self.request.user 
                  if self.request.user.is_authenticated else None),
            action=action,
            message=message,
            related_model="Product",
            related_id=str(instance.id) if instance else None,
        )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            instance = self.serializer_class.Meta.model.objects.get(pk=response.data["id"])
            self.perform_log("CREATE", "Producto creado", instance=instance)
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            self.perform_log("UPDATE", 
                             "Producto actualizado", 
                             instance=self.get_object())
            
        return response

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            self.perform_log("UPDATE", 
                             "Producto actualizado parcialmente", 
                             instance=self.get_object())
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_log("DELETE", 
                         "Producto eliminado", 
                         instance=instance)
        return super().destroy(request, *args, **kwargs)


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
