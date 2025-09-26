from conf.permissions import IsOwnerByGUIDOrAdminForRestApp

from .models import Order

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.throttling import AnonRateThrottle

from django.shortcuts import get_object_or_404

from .serializers import (
    OrderSerializer,
    UpdateOrderSerializer,
    CancelOrderSerializer,
    CheckoutSerializer,
    OrderSerializerList,
    CompleteOrRefoundOrderSerializer
)


class OrderThrottle(AnonRateThrottle):
    """limita las solicitudes a 20 por hora"""

    rate = '100/hour'


# 1. Get All Orders ny store_name__slug
class StoreOrdersListView(generics.ListAPIView):
    """
    permite al dueño de la tienda ver todas sus ordenes.
    El puede filtrar para ver cuales están listas y cuales
    faltan por actualizar.
    """

    permission_classes = [IsOwnerByGUIDOrAdminForRestApp]
    serializer_class = OrderSerializerList

    def get_queryset(self):
        store_slug = self.kwargs["store"]
        qs = Order.objects.filter(
            store_name__slug=store_slug).order_by("-issued_at")

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
    """
    permite revisar los detalles de la compra con
    el id
    """

    throttle_classes = [OrderThrottle]
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
                {
                    "detail": "El ID de la orden debe ser numérico", 
                    "code": "invalid_id"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {"detail": "Order not found", "code": "order_not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )


#3. update order
class UpdateOrderView(generics.UpdateAPIView):
    """
    permite al dueño de la tienda subir la factura del envío
    y cambiar el estado a processing.
    al hacer esto el dueño de la tienda no puede cancelar el pedido
    """

    permission_classes = [IsOwnerByGUIDOrAdminForRestApp]
    queryset = Order.objects.all()
    serializer_class = UpdateOrderSerializer
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(
            {
                "detail": "Order updated successfully",
                "code": "order updated",
                "order": OrderSerializer(self.get_object()).data,
            },
            status=status.HTTP_200_OK,
        )


#4 delete order
class CancelOrderView(generics.UpdateAPIView):
    """
    permite al dueño de la tienda cancelar el pedido
    mientras no se haya actualizado el estado del envío
    de processing.
    reestablece el stock que el cliente compró
    """

    permission_classes = [IsOwnerByGUIDOrAdminForRestApp]
    queryset = Order.objects.all()
    serializer_class = CancelOrderSerializer
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(
            {
                "detail": "Order canceled successfully",
                "code": "order canceled",
                "order": OrderSerializerList(self.get_object()).data,
            },
            status=status.HTTP_200_OK,
        )


#5 complete or refound order
class CompleteOrRefoundOrderView(generics.UpdateAPIView):
    """
    cambia estado de pedido a delivered si el pedido se completa
    o el pago a refounded si ocurre algo durante el traslado del pedido.
    Si se completa el delivery y el estado cambia a delivered,
    se crea una boleta para pagarle a la tienda que hizo las ventas
    """

    permission_classes = [IsAdminUser]
    serializer_class = CompleteOrRefoundOrderSerializer
    queryset = Order.objects.all()
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        option = self.request.data.get('option')

        response = super().update(request, *args, **kwargs)
        return Response(
            {
                "detail": "Order updated successfully",
                "code": "task completed",
                "order": OrderSerializerList(self.get_object()).data,
            },
            status=status.HTTP_200_OK,
        )


#6 generate payment
class CheckoutView(APIView):
    """
    genera el pago con la pasarela de pagos
    """

    throttle_classes = [OrderThrottle]

    def post(self, request, *args, **kwargs):
        serializer = CheckoutSerializer(data=request.data)
        if serializer.is_valid():
            orders = serializer.save()  # lista de órdenes creadas
            return Response(
                OrderSerializer(
                    orders, many=True).data, 
                    status=status.HTTP_201_CREATED)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST)
