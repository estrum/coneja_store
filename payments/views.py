from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CheckoutSerializer
from orders.serializers import OrderSerializer

class CheckoutView(APIView):
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
