from django.urls import path
from .views import StoreOrdersListView,OrderDetailView

urlpatterns = [
    path("store/<int:user>/orders/", StoreOrdersListView.as_view(), name="store-orders"),
    path("orders/<int:id>/", OrderDetailView.as_view(), name="order-detail"),
]