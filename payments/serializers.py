from rest_framework import serializers
from django.db import transaction
from orders.models import Order, OrderDetail
from products.models import ProductInventory

class CartItemSerializer(serializers.Serializer):
    article = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class CheckoutSerializer(serializers.Serializer):
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
                    payment_status="pending",
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
