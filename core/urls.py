# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

from .api import ProductViewSet, CategoryViewSet, CartViewSet, CheckoutView, OrderViewSet, VendorViewSet, UserViewSet, AddressViewSet
from core.api import CreateRazorpayOrderView, VerifyRazorpayPaymentView


router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='order')   # singular basename
router.register(r'vendors', VendorViewSet, basename="vendor")
router.register(r'users', UserViewSet, basename="user")
router.register(r'addresses', AddressViewSet, basename='address')

urlpatterns = [
    # Django template views
    path("", views.home, name="home"),
    path("cart/", views.cart_view, name="cart"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    
    
    path("checkout/", views.checkout_page, name="checkout"),
    path("orders/", views.orders_page, name="orders"),
    

     

    # API endpoints
    path('api/', include(router.urls)),
    path('api/checkout/', CheckoutView.as_view(), name='api-checkout'),
    

    path('api/payments/create-razorpay-order/', CreateRazorpayOrderView.as_view(), name='create-razorpay-order'),
    path('api/payments/verify-razorpay-payment/', VerifyRazorpayPaymentView.as_view(), name='verify-razorpay-payment'),
    
    # path("api/payments/test-razorpay/", TestRazorpayOrderView.as_view(), name="test-razorpay")

]


