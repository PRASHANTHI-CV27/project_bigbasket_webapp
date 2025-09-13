from .models import Cart
from .serializers import CartSerializer

def cart_context(request):
    """
    Add cart count and totals to all templates
    """
    cart_count = 0
    cart_total = 0
    cart_savings = 0

    if request.user.is_authenticated or request.session.session_key:
        if not request.session.session_key:
            request.session.create()

        try:
            if request.user.is_authenticated:
                cart, _ = Cart.objects.get_or_create(user=request.user)
            else:
                cart, _ = Cart.objects.get_or_create(session_id=request.session.session_key)

            # If user is authenticated and cart is session-based, merge to user cart
            if request.user.is_authenticated and cart.session_id and not cart.user:
                user_cart, _ = Cart.objects.get_or_create(user=request.user)
                for item in cart.items.all():
                    existing = user_cart.items.filter(product=item.product).first()
                    if existing:
                        existing.quantity += item.quantity
                        existing.save()
                    else:
                        item.cart = user_cart
                        item.save()
                cart.delete()
                cart = user_cart

            cart_data = CartSerializer(cart).data
            cart_count = len(cart_data["items"])
            cart_total = cart_data["total"]
            cart_savings = cart_data["savings"]

        except Exception:
            pass

    return {
        "cart_count": cart_count,
        "cart_total": cart_total,
        "cart_savings": cart_savings,
    }
