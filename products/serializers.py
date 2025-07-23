from rest_framework import serializers
from .models import Product, Category, Tag, Size

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class SizeSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True)

    class Meta:
        model = Size
        fields = ['id', 'name', 'category']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Sobrescribir valores con los nombres legibles
        rep['category'] = instance.category.name
        return rep


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, write_only=True)
    sizes = serializers.PrimaryKeyRelatedField(queryset=Size.objects.all(), many=True, write_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'image_url',
            'price', 'stock', 'is_active',
            'category', 'tags', 'sizes',   # sólo escritura
            'updated_at'
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Sobrescribir valores con los nombres legibles
        rep['category'] = instance.category.name
        rep['tags'] = [tag.name for tag in instance.tags.all()]
        rep['sizes'] = [size.name for size in instance.sizes.all()]
        return rep

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        sizes = validated_data.pop('sizes', [])
        request = self.context.get('request')

        if request and hasattr(request, 'user'):
            validated_data['posted_by'] = request.user

        product = Product.objects.create(**validated_data)
        product.tags.set(tags)
        product.sizes.set(sizes)
        return product

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        sizes = validated_data.pop('sizes', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if tags is not None:
            instance.tags.set(tags)
        if sizes is not None:
            instance.sizes.set(sizes)

        instance.save()
        return instance
