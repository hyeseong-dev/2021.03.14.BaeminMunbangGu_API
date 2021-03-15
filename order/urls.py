from django.urls import path

from order.views import OrderListView, CartView

urlpatterns = [
    path('', OrderListView.as_view()),
    path('/cart', CartView.as_view()),
]