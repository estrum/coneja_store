from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (ProductViewSet,
                    ProductSearchView,
                    ProductByStoreView,
                    ProductDetailView,
                    CategoryViewSet, 
                    TagViewSet, 
                    SizeViewSet)

router = DefaultRouter()
router.register('product', ProductViewSet, basename='product'),
router.register('categories', 
                CategoryViewSet, 
                basename='categories')
router.register('tags', 
                TagViewSet, 
                basename='tags')
router.register('sizes', 
                SizeViewSet, 
                basename='sizes')

urlpatterns = [
    path('search/', 
         ProductSearchView.as_view(), name='product-search'),
    path('store/<str:store>/', 
         ProductByStoreView.as_view(), name='product-by-user'),
    path('product-detail/<str:id>/', 
         ProductDetailView.as_view(), name='product-detail'),
    path('', include(router.urls)),
]
