from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout
from .serializers import CartSerializer
from .models import Cart, Product, Vendor
from django.contrib.auth.decorators import login_required



def home(request):
    # Redirect users to their respective dashboards based on role
    if request.user.is_authenticated:
        role = None
        if request.user.is_staff or request.user.is_superuser:
            role = "admin"
        else:
            role = getattr(request.user.profile, "role", None)

        if role == "admin":
            return redirect("/superadmin/")
        elif role == "vendor":
            return redirect("/vendors/")
        elif role == "customer":
            return render(request, "index.html")
        else:
            # Unknown role, logout for safety
            logout(request)
            return redirect("/login/")

    return render(request, "index.html")

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
