from rest_framework import serializers
from django.db import transaction
from .models import Product, Category, Tag, Size, ProductInventory

#category
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


#tags
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


#productInventory para los tamaños/tallas y el stock de los productos
class ProductInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInventory
        fields = ['id', 'size', 'stock']


#size
class SizeSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True)

    class Meta:
        model = Size
        fields = ['id', 'name', 'category']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Sobrescribir valores con los nombres legibles
        rep['category'] = instance.category.name
        return rep


#para el get all de los productos para la vitrina o el panel de usuario
class ProductSerializerGetAll(serializers.ModelSerializer):
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


#para el getById del producto usado en los detalles y formularios
class ProductSerializerDetail(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name', read_only=True)
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    posted_by = serializers.CharField(source='posted_by.first_name', read_only=True)
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


#para los endpoints create y patch
class ProductSerializer(serializers.ModelSerializer):
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
        # Aquí puedes implementar una lógica más sofisticada para actualizar artículos existentes
        # o eliminar los que ya no están. Para simplificar, este ejemplo solo crea nuevos.
        instance.inventory.all().delete() # Elimina los artículos existentes para recrearlos
        for article_data in articles_data:
            ProductInventory.objects.create(producto=instance, **article_data)

        return instance
