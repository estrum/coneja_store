# orders/admin.py
from django.contrib import admin
from .models import Order, OrderDetail


class OrderDetailInline(admin.TabularInline):
    model = OrderDetail
    extra = 0
    readonly_fields = ["article", "quantity", "price_per_unit", "subtotal"]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "buyer_email",
        "buyer_phone",
        "shipping_address",
        "payment_status",
        "shipping_status",
        "issued_at",
        "store_name",   # la tienda
    )
    list_filter = ("payment_status", "shipping_status", "issued_at")
    search_fields = ("id", "buyer_email", "buyer_phone")
    inlines = [OrderDetailInline]


@admin.register(OrderDetail)
class OrderDetailAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "article",
        "quantity",
        "price_per_unit",
        "subtotal",
    )
    search_fields = ("order__id",)
