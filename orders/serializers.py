from django.db import transaction
from rest_framework import serializers
from .models import Order, OrderDetail
from products.models import ProductInventory
from conf.manejo_imagenes import procesar_imagen
import cloudinary.uploader


class OrderDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderDetail
        fields = [
            "id",
            "product_name_snapshot",
            "quantity",
            "price_per_unit",
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderDetailSerializer(many=True)
    total_amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True)
    store_name = serializers.CharField(
        source='store_name.store_name', 
        read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "formatted_id",
            "store_name",
            "buyer_email",
            "buyer_phone",
            "shipping_address",
            "total_amount",
            "payment_status",
            "shipping_status",
            "tracking_number",
            "shipping_invoice_url",
            "issued_at",
            "items"
        ]
        read_only_fields = fields

    @transaction.atomic
    def create(self, validated_data):
        details_data = validated_data.pop("order_details", [])
        order = super().create(validated_data)

        total = 0
        for detail in details_data:
            product = detail["product"]
            qty = detail["quantity"]

            # actualizar stock
            inventory = ProductInventory.objects.get(product=product)
            inventory.stock -= qty
            inventory.save()

            # crear detalle
            value = product.price * qty
            OrderDetail.objects.create(
                order=order,
                product=product,
                quantity=qty,
                value=value
            )

            total += value

        order.total_amount = total
        order.save()
        return order


class StoreOrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetail
        fields = [
            "id",
            "order",
            "product_name_snapshot",
            "product_sku_snapshot",
            "quantity",
            "price_per_unit",
            "subtotal",
        ]
        read_only_fields = fields


class StoreOrderSerializer(serializers.ModelSerializer):
    items = StoreOrderDetailSerializer(many=True)
    store_name = serializers.CharField(
        source='store_name.store_name', read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "issued_at",
            "total_amount",
            "payment_status",
            "shipping_status",
            "shipping_address",
            "buyer_phone",
            "buyer_email",
            "notes",
            "tracking_number",
            "store_name",
            "items",
        ]
        read_only_fields = fields


class UpdateOrderSerializer(serializers.ModelSerializer):
    # Cambiamos a ImageField para recibir archivos
    shipping_invoice_url = serializers.ImageField(required=True)
    
    class Meta:
        model = Order
        fields = ["tracking_number", "shipping_invoice_url"]

    def update(self, instance, validated_data):
        # Procesar imagen tipo "boleta"
        if validated_data.get("shipping_invoice_url"):
            processed_img = procesar_imagen(
                validated_data.get("shipping_invoice_url"), 
                f"Order-{instance.id}", 
                "boleta")

            # Subir a Cloudinary
            result = cloudinary.uploader.upload(
                processed_img, 
                folder="order-invoices/",
                public_id=f"Order-{instance.id}",
                overwrite=True)
            
            instance.shipping_invoice_url = result["secure_url"]


        instance.tracking_number = validated_data.get(
            "tracking_number", 
            instance.tracking_number)
        instance.shipping_status = "processing"
        instance.save()
        return instance


class CancelOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = []  # no recibe datos del request

    def update(self, instance, validated_data):
        if instance.shipping_status == "canceled":
            raise serializers.ValidationError(
                {
                    "detail": "Order already canceled", 
                    "code": "already_canceled"
                }
            )

        # Revertir stock de los OrderDetail
        for item in instance.items.all():
            try:
                inventory = ProductInventory.objects.get(
                    id=item.product_sku_snapshot)
                inventory.stock += item.quantity
                inventory.save()
            except ProductInventory.DoesNotExist:
                pass

        # Cambiar estados
        instance.shipping_status = "canceled"
        instance.payment_status = "failed"
        instance.save()
        return instance
