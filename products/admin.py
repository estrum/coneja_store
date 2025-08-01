# products/admin.py
from django.contrib import admin
from .models import Category, Tag, Product, Size, ProductInventory

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('id', 'size_name', 'description')
    search_fields = ('size_name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'category', 'posted_by', 'price', 'is_active')
    list_filter = ('category', 'is_active', 'tags')
    search_fields = ('name', 'description')
    filter_horizontal = ('tags',)


@admin.register(ProductInventory)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'product')
    search_fields = ('product',)
