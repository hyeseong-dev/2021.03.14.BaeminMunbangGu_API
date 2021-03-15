from django.urls import path, include

# from product.views import MainView

urlpatterns = [
        # path('main', MainView.as_view()),
        # path('product', include('product.urls')),
        # path('order', include('order.urls')),
        path('user', include('user.urls')),
]