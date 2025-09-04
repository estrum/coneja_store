from .models import Order
from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .serializers import (
    OrderSerializer, 
    StoreOrderSerializer,
    UpdateOrderSerializer,
    CancelOrderSerializer
)
#from conf.permissions import IsOwnerOrStaff


# 1. Get All Orders ny store_name__slug
class StoreOrdersListView(generics.ListAPIView):
    serializer_class = StoreOrderSerializer

    def get_queryset(self):
        store_slug = self.kwargs["store"]
        qs = Order.objects.filter(store_name__slug=store_slug).order_by("-issued_at")

        # Filtros opcionales
        payment_status = self.request.query_params.get("payment_status")
        shipping_status = self.request.query_params.get("shipping_status")
        buyer_email = self.request.query_params.get("buyer_email")

        if payment_status:
            qs = qs.filter(payment_status=payment_status)
        if shipping_status:
            qs = qs.filter(shipping_status=shipping_status)
        if buyer_email:
            qs = qs.filter(buyer_email__iexact=buyer_email)

        return qs


# 2. Get Order by Formatted id
class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def get_object(self):
        formatted_id = self.kwargs["id"]
        try:
            real_id = int(formatted_id)
        except ValueError:
            # devolvemos un json custom
            raise ValueError("invalid_id")
        return get_object_or_404(Order, id=real_id)

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except ValueError as e:
            return Response(
                {"detail": "El ID de la orden debe ser numérico", "code": "invalid_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {"detail": "Order not found", "code": "order_not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )


#3. update order
class UpdateOrderView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = UpdateOrderSerializer
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(
            {
                "detail": "Order updated successfully",
                "code": "order_updated",
                "order": OrderSerializer(self.get_object()).data,
            },
            status=status.HTTP_200_OK,
        )


#4 delete order
class CancelOrderView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = CancelOrderSerializer
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(
            {
                "detail": "Order canceled successfully",
                "code": "order_canceled",
                "order": OrderSerializer(self.get_object()).data,
            },
            status=status.HTTP_200_OK,
        )
