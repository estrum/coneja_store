from rest_framework import serializers
from django.db import transaction
from .models import Product, Category, Tag, Size, ProductInventory

#TODO: añadir logs a los serializer tags y productserializer
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
    """
    CRUD para inventario de productos
    no referenciampos product para poder hacer la referencia inversa
    """

    # Campo de solo lectura para mostrar nombre de la talla en GET
    size_name = serializers.CharField(
        source='size.size_name', read_only=True)

    # Campo de escritura para recibir el ID de talla en POST/PUT
    size = serializers.PrimaryKeyRelatedField(
        queryset=Size.objects.all(), write_only=True
    )

    class Meta:
        model = ProductInventory
        fields = ['id', 'size', 'size_name', 'stock']


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
    store_name = serializers.CharField(
        source='store_name.slug', read_only=True)
    product_inventory = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'image_urls',
            'price', 'store_name', 'category',
            'tags', 'product_inventory'
        ]

    def get_product_inventory(self, obj):
        inventory = ProductInventory.objects.filter(product=obj)
        return ProductInventorySerializer(inventory, many=True).data


#TODO: añadir logica de cloudinary para manejar las imangenes.
#La idea es que podamos añadir hasta 5 imagenes, elminar las 
# de una posicion recibiendo un texto delete-product.png que borre
#la imagen de esa misma posicion de cloudinary y lo mismo al editarla.
#las imagenes se guardaran en la carpeta del usuario dentro de la
#carpeta products y los nombres sera tipo product-1 hasta product-5
#asi poder sobreescribir la imagen.
#si no se recibe una imagen, se omite y no se cambia/actualiza
class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer para crear/editar producto junto con su inventario.
    """
    inventory = ProductInventorySerializer(many=True)
    store_name = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'image_urls',
            'price', 'category', 'store_name', 'tags',
            'inventory'
        ]

    @transaction.atomic
    def create(self, validated_data):
        inventory_data = validated_data.pop('inventory', [])
        user = self.context['request'].user
        tags = validated_data.pop('tags', [])

        # Crear producto
        product = Product.objects.create(**validated_data, store_name=user)
        product.tags.set(tags)

        # Crear inventario
        for inv in inventory_data:
            ProductInventory.objects.create(product=product, **inv)

        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        inventory_data = validated_data.pop('inventory', [])
        tags = validated_data.pop('tags', None)

        # Actualizar campos del producto
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if tags is not None:
            instance.tags.set(tags)
        instance.save()

        # Actualizar inventario (borramos y volvemos a crear)
        ProductInventory.objects.filter(product=instance).delete()
        for inv in inventory_data:
            ProductInventory.objects.create(product=instance, **inv)

        return instance
