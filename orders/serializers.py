from django.db import transaction
from rest_framework import serializers
from .models import Order, OrderDetail
from products.models import ProductInventory
from conf.manejo_imagenes import procesar_imagen
import cloudinary.uploader

#TODO: añadir logs en las orders
class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Despliega la información de los productos comprados
    Según la orden generada
    """

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
    """
    Despliega la oden del cliente con los productos que este
    compró
    """

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


class OrderSerializerList(serializers.ModelSerializer):
    """
    Despliega la oden del cliente en una lista corta
    """

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
            "buyer_email",
            "buyer_phone",
            "total_amount",
            "payment_status",
            "shipping_status",
            "store_name",
            "issued_at",
        ]
        read_only_fields = fields


class UpdateOrderSerializer(serializers.ModelSerializer):
    """
    Permite al dueño de la tienda subir una foto de voucher
    del envio del producto. cuando el producto esté en manos
    del cliente se dara como completado
    """
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
    """
    Permite al dueño de la tienda cancelar el pedido
    reestableciendo el stock de los articulos y
    reembolzar el dinero gastado en esa tienda.
    """
    class Meta:
        model = Order
        fields = []

    def update(self, instance, validated_data):
        if instance.shipping_status != "processing":
            raise serializers.ValidationError(
                {
                    "detail": "Order cannot be canceled", 
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


class CompleteOrRefoundOrderSerializer(serializers.Serializer):
    """
    Permite al administrador cambiar los estados de shipping
    y payment a completado o reembolsado.
    option = 1 => marca producto como entregado.
    option = 2 => marca producto como reembolsado.
    """
    option = serializers.IntegerField(write_only=True)

    def validate_option(self, value):
        if value not in [1, 2]:
            raise serializers.ValidationError(
                "Option must be 1 (delivered) or 2 (refounded).")
        return value

    def update(self, instance, validated_data):
        option = validated_data["option"]

        print(instance.shipping_status)
        print(instance.payment_status)
        # Validación de estados previos
        if instance.shipping_status == "processing" and \
            option == 1:
            instance.shipping_status = "delivered"

        elif instance.payment_status == "failed" and \
            option == 2:
            instance.payment_status = "refounded"

        else: 
            raise serializers.ValidationError(
                {
                    "detail": "Order status cannot be changed",
                    "code": "product already refounded or delivered",
                }
            )

        instance.save()
        return instance


class CartItemSerializer(serializers.Serializer):
    """
    Maneja los articulos del carro del cliente
    """
    
    article = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class CheckoutSerializer(serializers.Serializer):
    """
    Procesa la venta y genera una orden si todo va bien
    """
    email = serializers.EmailField()
    phone = serializers.CharField()
    address = serializers.CharField()
    notes = serializers.CharField(max_length=125)
    items = CartItemSerializer(many=True)

    def create(self, validated_data):
        cart_items = validated_data.pop("items")

        # agrupamos por tienda
        grouped_cart = {}

        with transaction.atomic():
            for item in cart_items:
                article = ProductInventory.objects.select_related(
                    "product").get(id=item["article"])
                store_user = article.product.posted_by

                # Validamos stock
                if article.stock < item["quantity"]:
                    raise serializers.ValidationError(
                        f"Artículo {article.id} con stock insuficiente"
                    )
                
                # Restamos stock
                article.stock -= item["quantity"]
                article.save()

                if store_user not in grouped_cart:
                    grouped_cart[store_user] = []
                grouped_cart[store_user].append(
                    {"article": article, "quantity": item["quantity"]})

            orders_created = []

            for store_user, items in grouped_cart.items():
                # calculamos el total de la orden
                total_amount = sum(
                    [i["article"].product.price * i["quantity"]
                      for i in items])

                # creamos la orden
                order = Order.objects.create(
                    store_name=store_user,
                    total_amount=total_amount,
                    payment_status="paid",
                    shipping_status="pending",
                    shipping_address=validated_data["address"],
                    buyer_phone=validated_data["phone"],
                    buyer_email=validated_data["email"],
                    notes=validated_data["notes"]
                )

                # creamos los detalles
                for i in items:
                    OrderDetail.objects.create(
                        order=order,
                        article=i["article"],
                        quantity=i["quantity"],
                        price_per_unit=i["article"].product.price,
                        subtotal=i[
                            "article"].product.price * i["quantity"],
                        product_name_snapshot=i["article"],
                        product_sku_snapshot=i["article"].id
                    )

                orders_created.append(order)

        return orders_created
