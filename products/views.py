from rest_framework import viewsets, status
from rest_framework.permissions import (IsAuthenticatedOrReadOnly)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import serializers
from django.db.models import Q
from django.db import transaction

from .models import Product, Category, Tag, Size, ProductInventory
from .serializers import (
    ProductSerializerGetAll, 
    ProductSerializerDetail,
    ProductSerializer,
    ProductInventorySerializer,
    CategorySerializer, 
    TagSerializer, 
    SizeSerializer
)
from conf.permissions import (IsOwnerOrStaffOrSuperuser, 
                              IsOwnerOrSuperuser) 

class PublicReadOnly(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in ['destroy']:
            return [IsOwnerOrStaffOrSuperuser()]
        elif self.action in ['create', 'update', 'partial_update']:
            return [IsOwnerOrSuperuser()]
        return [permission() for permission in self.permission_classes]


# Product List View - GetAll con filtros y paginación
class ProductListView(APIView):
    def get(self, request):
        queryset = Product.objects.filter(is_active=True)

        # Filtros
        search = request.query_params.get('search')
        category = request.query_params.get('category')
        tags = request.query_params.getlist('tags')

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        if category:
            queryset = queryset.filter(category_id=category)
        if tags:
            queryset = queryset.filter(tags__id__in=tags).distinct()

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

        start = (page - 1) * page_size
        end = start + page_size

        # Ordenamiento
        order_by = request.query_params.get('order_by')
        allowed_order_fields = ['price', '-price', 'name', '-name', 'updated_at', '-updated_at']

        if order_by in allowed_order_fields:
            queryset = queryset.order_by(order_by)

        serializer = ProductSerializerGetAll(queryset[start:end], many=True)

        return Response({
            'page': page,
            'maxPage': max_page,
            'totalItems': total,
            'productList': serializer.data
        }, status=status.HTTP_200_OK)


# Product ViewSet - GetById, Create, Update, Delete
class ProductoRetrieveUpdateDestroyView(PublicReadOnly):
    queryset = Product.objects.all()
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
