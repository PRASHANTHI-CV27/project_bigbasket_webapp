# urls.py (app or project)
from django.urls import path,include
from rest_framework.routers import DefaultRouter
from . import views

from . api import ProductViewSet, CategoryViewSet, CartViewSet, CheckoutView, OrderViewSet


router = DefaultRouter()
router.register(r'products', ProductViewSet, basename= 'product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    path("", views.home, name="home"),
    path("cart/", views.cart_view, name="cart"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    
    
    path('api/', include(router.urls)), 
    path('api/orders/checkout/', CheckoutView.as_view(), name='api-checkout'),

    
]
