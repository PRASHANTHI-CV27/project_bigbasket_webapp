# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

from .api import ProductViewSet, CategoryViewSet, CartViewSet, CheckoutView, OrderViewSet, VendorViewSet, UserViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='order')   # singular basename
router.register(r'vendors', VendorViewSet, basename="vendor")
router.register(r'users', UserViewSet, basename="user")

urlpatterns = [
    # Django template views
    path("", views.home, name="home"),
    path("cart/", views.cart_view, name="cart"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),

    # API endpoints
    path('api/', include(router.urls)),
    path('api/checkout/', CheckoutView.as_view(), name='api-checkout'),
]
