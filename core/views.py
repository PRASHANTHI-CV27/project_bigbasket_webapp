from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout
from .serializers import CartSerializer
from .models import Cart, Product, Vendor
from django.contrib.auth.decorators import login_required
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
import razorpay
from django.conf import settings
from .models import CartOrder, Payment


razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))




def home(request):
    return render(request,"index.html")
   
def cart_view(request):
    # Allow all users (authenticated or anonymous) to view cart

    cart = None
    savings = 0
    total = 0

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        sid = request.session.session_key or request.session.create() or request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_id=sid)

    if cart:
        for item in cart.items.all():
            total += item.line_total
            if item.product.old_price:
                savings += (float(item.product.old_price) - float(item.product.price)) * item.quantity

    return render(request, "cart.html", {
        "cart": cart,
        "cart_total": round(total, 2),
        "cart_savings": round(savings, 2),
    })


    
    
    


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    discount = None
    if product.old_price and float(product.old_price) > float(product.price):
        discount = round(((float(product.old_price) - float(product.price)) / float(product.old_price)) * 100)

    return render(request, "product_detail.html", {
        "product": product,
        "discount": discount,
    })







@login_required
def checkout_page(request):
    return render(request, "checkout.html")




def orders_page(request):
    return render(request, "orders.html")





