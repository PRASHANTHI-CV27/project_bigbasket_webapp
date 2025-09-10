from django.shortcuts import render
from .serializers import CartSerializer
from .models import Cart, Product
from django.shortcuts import render, get_object_or_404



def home(request):
    return render(request, "index.html")

def cart_view(request):
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

