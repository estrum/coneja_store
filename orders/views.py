from .models import Order
from rest_framework import generics
from products.models import ProductInventory
from .serializers import (
    OrderSerializer, StoreOrderSerializer
)
#from conf.permissions import IsOwnerOrStaff


# 1. GetOrdersByStore → Solo dueño de la tienda o staff
class StoreOrdersListView(generics.ListAPIView):
    serializer_class = StoreOrderSerializer

    def get_queryset(self):
        store_user_id = self.kwargs["user"]
        return Order.objects.filter(store_name=store_user_id).order_by("-issued_at")


# 2. GetOrderById → AllowAny (consulta pública con UUID o ID formateado)
class OrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    lookup_field = "id"   # o simplemente "pk"


# 3. UpdateOrder → Solo dueño o staff
class UpdateOrderView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    #permission_classes = [IsOwnerOrStaff]

    def perform_update(self, serializer):
        order = self.get_object()

        # ⚡ ejemplo: si cancela, se restaura stock
        if self.request.data.get("status") == "cancelled":
            details = order.details.all()
            for d in details:
                inv = ProductInventory.objects.get(product=d.product)
                inv.stock += d.quantity
                inv.save()

        serializer.save()
