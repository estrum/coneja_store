from django.db import models
from django.conf import settings

from users.models import CustomUser

class Order(models.Model):
    """
    Orden para la factura del pedido
    La funcion formatted_id se usara para buscar la order
    """
    store_name = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
    )

    # datos básicos de la orden
    # fecha de emisión
    issued_at = models.DateTimeField(auto_now_add=True)
    # fecha última actualización
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS, default='pending'
    )

    SHIPPING_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
    ]
    shipping_status = models.CharField(
        max_length=20, choices=SHIPPING_STATUS, default='pending'
    )

    # TODO: añadír un campo de imagen para que el 
    # usuario suba la factura del envío 
    
    # dirección y contacto
    shipping_address = models.TextField()
    buyer_phone = models.CharField(max_length=20)
    buyer_email = models.EmailField()

    # comentarios del comprador
    notes = models.TextField(blank=True, null=True)
    # numero de trackeo del pedido
    tracking_number = models.CharField(
        max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} - from {self.store_name}"
    
    @property
    def formatted_id(self):
        return f"{self.id:05d}"


class OrderDetail(models.Model):
    """
    Detalle de los articulos que el cliente compró
    """
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name="items"
    )
    article = models.ForeignKey(
        "products.ProductInventory", 
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    # guardar nombre del producto al momento de la orden
    product_name_snapshot = models.CharField(max_length=255)
    product_sku_snapshot = models.CharField(
        max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        # calcular subtotal automáticamente
        self.subtotal = self.price_per_unit * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}-{self.article} (Order {self.order.id})"
