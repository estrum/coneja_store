from django.urls import path
from .views import (StoreOrdersListView,
                    OrderDetailView,
                    UpdateOrderView,
                    CancelOrderView,
                    CheckoutView)

urlpatterns = [
    path("store/<str:store>/orders/", StoreOrdersListView.as_view(), name="store-orders"),
    path("order/<str:id>/", OrderDetailView.as_view(), name="order-detail"),
    path("order/<int:id>/update/", UpdateOrderView.as_view(), name="order-update"),
    path("order/<int:id>/cancel/", CancelOrderView.as_view(), name="order-cancel"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
]