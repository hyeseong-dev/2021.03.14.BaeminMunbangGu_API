from django.urls import path
from .views      import (
ProductDetailView, 
ProductListView, 
ReviewView, 
ProductLikeView)

urlpatterns = [
    path('',                         ProductListView.as_view()),
    path('/<int:product_id>',        ProductDetailView.as_view()),
    path('/review',                  ReviewView.as_view()),
    path('/review/<int:product_id>', ReviewView.as_view()),
    path('/like',                    ProductLikeView.as_view()),
]