from rest_framework import serializers
#from django.db import transaction
from .models import Product, Category, Tag, Size, ProductInventory


class CategorySerializer(serializers.ModelSerializer):
    """crud para categorías"""
    
    class Meta:
        model = Category
        fields = ['id', 'name']


class TagSerializer(serializers.ModelSerializer):
    """crud para tags"""

    class Meta:
        model = Tag
        fields = ['id', 'name']


class ProductInventorySerializer(serializers.ModelSerializer):
    """crud para el inventario de productos"""

    class Meta:
        model = ProductInventory
        fields = ['id', 'size', 'stock']


class SizeSerializer(serializers.ModelSerializer):
    """crud para los tamaños de los articulos de los productos"""

    class Meta:
        model = Size
        fields = ['id', 'size_name', 'description']


class ProductSerializerGetAll(serializers.ModelSerializer):
    """serializer para el endpoint getAll de los productos"""

    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, write_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 
            'image_urls', 'price', 'is_active',
            'category', 'tags', 'updated_at',
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['category'] = instance.category.name
        rep['tags'] = [tag.name for tag in instance.tags.all()]
        rep.pop('description')
        rep.pop('is_active')
        return rep


class ProductSerializerDetail(serializers.ModelSerializer):
    """
    para el endpoint getById del producto usado 
    en los detalles y formularios
    """

    category = serializers.CharField(
        source='category.name', read_only=True)
    tags = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='name')
    posted_by = serializers.CharField(
        source='posted_by.first_name', read_only=True)
    product_inventory = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'image_urls',
            'price', 'posted_by', 'category',
            'tags', 'product_inventory'
        ]

    def get_product_inventory(self, obj):
        inventory = ProductInventory.objects.filter(product=obj)
        return ProductInventorySerializer(inventory, many=True).data


class ProductSerializer(serializers.ModelSerializer):
    """para los endpoints create y patch de productInventory"""
    inventory = ProductInventorySerializer(many=True)

    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'posted_by',
                  'image_urls', 'image_public_ids', 'tags',
                  'price', 'updated_at', 'inventory']
    
    def create(self, validated_data):
        articles_data = validated_data.pop('inventory')
        product = Product.objects.create(**validated_data)
        for article in articles_data:
            ProductInventory.objects.create(producto=product, **article)
        return product
    
    def update(self, instance, validated_data):
        articles_data = validated_data.pop('inventory')

        # Actualizar el producto
        instance.name = validated_data.get('name', instance.name)
        instance.save()

        # Actualizar o crear artículos relacionados
        # Aquí puedes implementar una lógica más sofisticada para 
        # actualizar artículos existentes
        # o eliminar los que ya no están. 
        # Para simplificar, este ejemplo solo crea nuevos.
        instance.inventory.all().delete()
        for article_data in articles_data:
            ProductInventory.objects.create(
                producto=instance, **article_data)

        return instance
