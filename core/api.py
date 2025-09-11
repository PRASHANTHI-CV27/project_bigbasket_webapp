from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from .models import Product,Category, Cart, CartItem, Product,CartOrder, CartOrderItems
from django.shortcuts import get_object_or_404
from .serializers import ProductSerializer, CategorySerializer,CartSerializer, CartItemSerializer, CartOrderSerializer
from rest_framework import serializers
from django.db import transaction
from decimal import Decimal

import uuid

from rest_framework.views import APIView





class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer

    def get_queryset(self):
        # start with all products, newest first
        qs = Product.objects.all().order_by('-date').prefetch_related('productimages_set')

        # filter by category (id or cid) if query param provided
        cat = self.request.query_params.get('category')
        if cat:
            if cat.isdigit():
                qs = qs.filter(category_id=int(cat))
            else:
                qs = qs.filter(category__cid=cat)

        # optional: filter by search term ?q=...
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(title__icontains=q)

        return qs




class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Provides:
      GET /api/categories/     -> list
      GET /api/categories/{pk}/ -> detail
    (Read only)
    """
    queryset = Category.objects.all().order_by('title')
    serializer_class = CategorySerializer
    
    
    # OPTIONAL helper action (uncomment if you want /api/categories/{pk}/products/)
    # from rest_framework.decorators import action
    # from rest_framework.response import Response
    #
    # @action(detail=True, methods=['get'])
    # def products(self, request, pk=None):
    #     cat = self.get_object()
    #     qs = Product.objects.filter(category=cat).prefetch_related('productimages_set')
    #     page = self.paginate_queryset(qs)
    #     if page is not None:
    #         serializer = ProductSerializer(page, many=True, context={'request': request})
    #         return self.get_paginated_response(serializer.data)
    #     serializer = ProductSerializer(qs, many=True, context={'request': request})
    #     return Response(serializer.data)
    
    
    
    
    
    
class CartViewSet(viewsets.ViewSet):
    """
    Cart API:
    - GET /api/cart/           → view cart
    - POST /api/cart/add/      → add item
    - PATCH /api/cart/<id>/    → update quantity
    - DELETE /api/cart/<id>/   → remove item
    """

    def _get_cart(self, request):
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
        else:
            sid = request.session.session_key or request.session.create() or request.session.session_key
            cart, _ = Cart.objects.get_or_create(session_id=sid)
        return cart

    def list(self, request):
        """Get current cart"""
        cart = self._get_cart(request)
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)

    
    def create(self, request):
        """Add product to cart"""
        cart = self._get_cart(request)
        product_id = request.data.get('product')
        qty = int(request.data.get('quantity', 1))

        product = get_object_or_404(Product, pk=product_id)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            item.quantity += qty
        else:
            item.price_snapshot = product.price
            item.quantity = qty
        item.save()

        return Response(CartSerializer(cart, context={'request': request}).data)

    def partial_update(self, request, pk=None):
        """Update quantity of a cart item"""
        item = get_object_or_404(CartItem, pk=pk)
        qty = int(request.data.get('quantity', item.quantity))
        item.quantity = qty
        item.save()
        return Response(CartItemSerializer(item).data)

    def destroy(self, request, pk=None):
        """Remove a cart item"""
        item = get_object_or_404(CartItem, pk=pk)
        item.delete()
        return Response({"detail": "Item removed"}, status=status.HTTP_204_NO_CONTENT)
    
    
    




def _get_cart_for_request(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        sid = request.session.session_key or request.session.create() or request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_id=sid)
    return cart

import traceback
class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            cart = _get_cart_for_request(request)
            items = list(cart.items.select_related('product').all())

            if not items:
                return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

            # compute totals and create order atomically
            with transaction.atomic():
                total_amount = Decimal("0.00")

                # validate items and sum price
                for ci in items:
                    # ensure product exists
                    if not getattr(ci, "product", None):
                        return Response({"detail": f"CartItem {ci.id} missing product"}, status=status.HTTP_400_BAD_REQUEST)

                    product_price = Decimal(ci.product.price or ci.price_snapshot or 0)
                    qty = Decimal(ci.quantity or 0)
                    total_amount += product_price * qty

                # create order
                invoice = uuid.uuid4().hex[:12].upper()
                order = CartOrder.objects.create(
                    user=request.user,
                    invoice_no=invoice,
                    price=total_amount,
                    paid_status=False,
                    order_status='processing'
                )

                # create order items (ensure model has 'product' field; if not, remove product=...)
                for ci in items:
                    product = ci.product
                    CartOrderItems.objects.create(
                        order=order,
                        product=product,              # <-- only if CartOrderItems has product FK
                        item_status='pending',        # use your choice/choices
                        item=product.title if product else (ci.product.title if hasattr(ci, 'product') else str(ci)),
                        image=(product.image if getattr(product, 'image', None) else None),
                        qty=ci.quantity,
                        price=product.price if product else (ci.price_snapshot or 0),
                        total=Decimal(ci.quantity) * Decimal(product.price if product else (ci.price_snapshot or 0))
                    )

                # clear cart
                cart.items.all().delete()

                serializer = CartOrderSerializer(order, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            # print full traceback to server console (very helpful)
            traceback.print_exc()
            # return a safe message to client and the error string
            return Response(
                {"detail": "Internal server error during checkout",
                 "error": str(e),
                 "traceback": traceback.format_exc()},
                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        
        
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/orders/        -> list orders (for authenticated user)
    /api/orders/{id}/   -> order detail (must belong to user, unless staff)
    """
    serializer_class = CartOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # staff/superuser can see all orders; normal users see only their own orders
        qs = CartOrder.objects.all().order_by('-order_date')
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return qs
        return qs.filter(user=user)
