from . import views
from django.urls import include, path


urlpatterns = [
    path("place_order/", views.place_order, name="place_order"),
    path("payments/", views.payments, name="payments"),
    path("order_complite/", views.order_complite, name="order_complite"),
]
