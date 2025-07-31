from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (ProductoRetrieveUpdateDestroyView,
                    ProductListView,
                    CategoryViewSet, 
                    TagViewSet, 
                    SizeViewSet)

router = DefaultRouter()
router.register('product', ProductoRetrieveUpdateDestroyView, basename='product')
router.register('categories', CategoryViewSet, basename='categories')
router.register('tags', TagViewSet, basename='tags')
router.register('sizes', SizeViewSet, basename='sizes')

urlpatterns = [
    path('product-list/', ProductListView.as_view(), name='product-list'),
    path('', include(router.urls)),
]
